import logging
import os
import subprocess
import time

# AWS interface
import boto3
from botocore.exceptions import ClientError

class AWS(object):
    """
    Facilitator class to Amazon web services (AWS)

    reference: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/examples.html
    """

    def __init__(self, region="eu-central-1", logger=None):
        if logger == None:
            self.log = logging.getLogger(__file__)
        else:
            self.log = logger
        self.s3 = boto3.resource('s3', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)

    def create_address(self, instance_id):
        try:
            allocation = self.ec2.allocate_address(Domain='vpc')
            response = self.ec2.associate_address(
                allocation['AllocationId'],
                InstanceId=instance_id
            )
        except ClientError as e:
            self.log.error(e)
        return response

    def create_key_pair(self, name):
        response = self.ec2.create_key_pair(KeyName=name)
        return response

    def create_security_group(self, group_name, desc, ingress=None):
        response = self.ec2.describe_vpcs()
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
        try:
            response = self.ec2.create_security_group(GroupName=group_name, Description=desc, VpcId=vpc_id)
            security_group_id = response['GroupId']
            self.log.info('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
            if not ingress is None:
                ip_perms = []
                for x in ingress:
                    ing = {
                        'IpProtocol': 'tcp',
                        'FromPort': x['from'],
                        'ToPort': x['to'],
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                    if 'protocol' in x.keys():
                        ing['IpProtocol'] = x['protocol']
                    ip_perms.append(ing)
                data = self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=ip_perms
                )
                self.log.info('Ingress Successfully Set %s' % data)
        except ClientError as e:
            self.log.error(e)
        return response

    def delete_address(self, allocation_id):
        try:
            response = self.ec2.release_address(AllocationId=allocation_id)
        except ClientError as e:
            self.log.error(e)
        return response

    def delete_key_pair(self, name):
        response = self.ec2.delete_key_pair(KeyName=name)
        return response

    def delete_security_group(self, id):
        try:
            response = self.ec2.delete_security_group(GroupId=id)
            self.log.info('Security Group {} Deleted'.format(id))
        except ClientError as e:
            self.log.error(e)
        return response

    def delete(self, bucket, files):
        s3 = boto3.client('s3')
        objects = []
        for fname in files:
            objects.append({ 'Key': os.path.basename(fname) })
        self.log.debug('deleting {} objects in {}'.format(len(objects), bucket))
        response = s3.delete_objects(Bucket=bucket, Delete={ 'Objects': objects })
        return response

    def download(self, bucket, files):
        result = []
        s3 = boto3.client('s3')
        for fname in files:
            name = os.path.basename(fname)
            self.log.debug('downloading {} from {}'.format(name, bucket))
            s3.download_file(bucket, name, fname)
            if not os.path.exists(fname):
                fname = None
            result.append(fname)
        return result

    def get_addresses(self):
        filters = [
            {'Name': 'domain', 'Values': ['vpc']}
        ]
        return self.ec2.describe_addresses(Filters=filters)

    def get_buckets(self):
        return list(self.s3.buckets.all())

    def get_command_output(self, instance_id, command_id):
        response = self.ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        return response

    def get_instances(self):
        return self.ec2.describe_instances()

    def get_instance(self, instance_id):
        result = None
        response = self.ec2.describe_instances()
        for instance in response['Reservations'][0]['Instances']:
            if instance['InstanceId'] == instance_id:
                result = instance
                break
        return result

    def get_key_pairs(self):
        return self.ec2.describe_key_pairs()

    def send_command(self, instance_id, command, comment='', wait=False):
        for i in range(3):
            try:
                response = self.ssm.send_command(
                    InstanceIds=[instance_id],
                    DocumentName="AWS-RunShellScript",
                    Comment=comment,
                    Parameters={ 'command': [ command ] }
                )
            except:
                self.log.error('instance {} may not be fully up, waiting ...'.format(instance_id))
                time.sleep(15)
                response = None
                pass
        if wait and not response is None:
            response = self.wait_for_ssm_command(response)
        return response

    def send_commands(self, instance_id, commands=[], comment='', wait=False):
        for i in range(3):
            try:
                response = self.ssm.send_command(
                    InstanceIds=[instance_id],
                    DocumentName="AWS-RunShellScript",
                    Comment=comment,
                    Parameters={ 'commands': commands }
                )
            except:
                self.log.error('instance {} may not be fully up, waiting ...'.format(instance_id))
                time.sleep(15)
                response = None
                pass
        if wait and not response is None:
            self.log.info('waiting for {}'.format(commands))
            response = self.wait_for_ssm_command(response)
            # get commmand output
            if not response is None and 'Commands' in response.keys() and len(response['Commands']) > 0:
                command_id = response['Commands'][0]['CommandId']
                response = self.get_command_output(instance_id, command_id)
        return response

    def reboot_instance(self, id, wait=False):
        try:
            self.ec2.reboot_instances(InstanceIds=[id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                self.log.error("You don't have permission to reboot instances.")
                raise

        try:
            response = self.ec2.reboot_instances(InstanceIds=[id], DryRun=False)
            self.log.info('Success {}'.format(response))
        except ClientError as e:
            self.log.error(e)
        return response

    def start_instance(self, id, wait=False, sleep_interval=10):
        # Do a dryrun first to verify permissions
        try:
            self.ec2.start_instances(InstanceIds=[id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        response = None
        try:
            response = self.ec2.start_instances(InstanceIds=[id], DryRun=False)
            self.log.debug(response)
        except ClientError as e:
            self.log.error(e)

        if wait:
            response = self._instance_wait_for_state(id, 'running', interval=sleep_interval)
            time.sleep(sleep_interval)
        return response

    def stop_instance(self, id, wait=False, sleep_interval=10):
        # Do a dryrun first to verify permissions
        try:
            self.ec2.stop_instances(InstanceIds=[id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[id], DryRun=False)
            self.log.debug(response)
        except ClientError as e:
            self.log.error(e)

        if wait:
            time.sleep(sleep_interval)
            response = self._instance_wait_for_state(id, 'stopped', interval=sleep_interval)
        return response

    def upload(self, bucket, files):
        result = []
        s3 = boto3.client('s3')
        for fname in files:
            name = os.path.basename(fname)
            self.log.debug('uploading {} to {}'.format(name, bucket))
            s3.upload_file(fname, bucket, name)
            result.append(name)
        return result

    def wait_for_ssm_command(self, command, timeout=300, interval=10):
        response = None
        for repeat in range(timeout // interval):
            time.sleep(interval)
            response = self.ssm.list_commands(
                CommandId=command['Command']['CommandId'])
            if not response.get('Commands', False):
                return response
            self.log.info('command {} {} {}'.format(
                command['Command']['CommandId'],
                command['Command']['Parameters']['commands'],
                response['Commands'][0]['Status']))
            if response['Commands'][0]['Status'] in \
                    ('Success', 'Cancelled', 'Failed', 'TimedOut'):
                return response
        raise Exception(
            'Timed out after {} waiting for an SSM command to finish.'.format(timeout))
        return response

    def _instance_wait_for_state(self, id, state, timeout=300, interval=5):
        info = {}
        t = 0
        while t < timeout:
            info = self.get_instance(id)
            self.log.debug('instance {} state {}'.format(id, info['State']['Name']))
            if info['State']['Name'] == state:
                break
            time.sleep(interval)
            t += interval
        self.log.debug('instance {} state {}'.format(id, info['State']['Name']))
        return info
