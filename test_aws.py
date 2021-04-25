import json
import logging
import os
import shutil
import sys
import time
import unittest

# local modules
from aws import AWS

self = os.path.basename(sys.argv[0])
myName = os.path.splitext(self)[0]
log = logging.getLogger(myName)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log.setLevel(logging.DEBUG)

aws = AWS(logger=log)
test_bucket = 'af-example1'
test_instance_id = 'i-00d4bb1c2ee88275c'

@unittest.skip("Skipping Test01")
class Test01(unittest.TestCase):

    def test_get_buckets(self):
        buckets = aws.get_buckets()
        log.debug(buckets)
        self.assertGreater(len(buckets), 0)

    def test_get_instances(self):
        response = aws.get_instances()
        log.debug(response)

@unittest.skip("Skipping Test02")
class Test02(unittest.TestCase):

    def test_upload(self):
        files = []
        for f in os.listdir('tmp'):
            files.append(os.path.join('tmp', f))
        response = aws.upload(test_bucket, files)
        self.assertEqual(len(response), len(files))

@unittest.skip("Skipping Test03")
class Test03(unittest.TestCase):

    def test_download(self):
        if os.path.exists('download'):
            shutil.rmtree('download')
        os.makedirs('download')
        files = []
        for f in os.listdir('tmp'):
            files.append(os.path.join('download', f))
        response = aws.download(test_bucket, files)
        self.assertEqual(len(response), len(files))
        self.assertFalse(None in response)

@unittest.skip("Skipping Test03a")
class Test03a(unittest.TestCase):

    def test_delete(self):
        files = []
        for f in os.listdir('tmp'):
            files.append(os.path.join('tmp', f))
        test_bucket = 'af-imageproc-out'
        files = [ '2018-01-30.mp4' ]
        response = aws.delete(test_bucket, files)
        self.assertEqual(len(response['Deleted']), len(files))

@unittest.skip("Skipping Test04")
class Test04(unittest.TestCase):

    def test_get_instance(self):
        instance = aws.get_instance(test_instance_id)
        log.info(instance)
        self.assertEqual(instance['InstanceId'], test_instance_id)
        self.assertEqual(instance['InstanceType'], 't2.micro')
        self.assertEqual(instance['Placement']['AvailabilityZone'], 'eu-central-1b')

@unittest.skip("Skipping Test05")
class Test05(unittest.TestCase):

    def test_start_instance(self):
        instance = aws.get_instance(test_instance_id)
        if instance['State']['Name'] == "stopped":
            log.info('starting instance {}'.format(test_instance_id))
            response = aws.start_instance(test_instance_id, wait=True)
            log.debug(response)
            self.assertTrue(response['State']['Name'], "running")
        else:
            log.warn('instance {} not stopped'.format(test_instance_id))

@unittest.skip("Skipping Test06")
class Test06(unittest.TestCase):

    def test_stop_instance(self):
        instance = aws.get_instance(test_instance_id)
        if instance['State']['Name'] == "running":
            log.info('stopping instance {}'.format(test_instance_id))
            response = aws.stop_instance(test_instance_id, wait=True)
            log.debug(response)
            self.assertTrue(response['State']['Name'], "stopped")
        else:
            log.warn('instance {} not running'.format(test_instance_id))

@unittest.skip("Skipping Test07")
class Test07(unittest.TestCase):

    def test_send_commands(self):
        instance = aws.get_instance(test_instance_id)
        if not instance['State']['Name'] == "running":
            response = aws.start_instance(test_instance_id, True)
            log.debug(response)
            self.assertTrue(response['State']['Name'], "running")
        response = aws.send_commands(test_instance_id, [ 'ifconfig' ], wait=True)
        log.debug(response)

#@unittest.skip("Skipping Test08")
class Test08(unittest.TestCase):

    def test_send_commands(self):
        instance = aws.get_instance(test_instance_id)
        if not instance['State']['Name'] == "running":
            response = aws.start_instance(test_instance_id, True)
            log.debug(response)
            self.assertTrue(response['State']['Name'], "running")
        response = aws.send_commands(test_instance_id, [ '#!/bin/bash', 'cd /home/ec2-user', 'su -c "ls -al" ec2-user' ], wait=True)
        self.assertIsNotNone(response)
        self.assertTrue('StandardOutputContent' in response)
        print(response['StandardOutputContent'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
