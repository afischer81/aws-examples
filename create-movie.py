import logging
import os
import sys
import time

from aws import AWS

self = os.path.basename(sys.argv[0])
myName = os.path.splitext(self)[0]
log = logging.getLogger(myName)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log.setLevel(logging.DEBUG)

image_dir = sys.argv[1]
instance_id = sys.argv[2]
bucket_in = sys.argv[3]
bucket_out = sys.argv[4]
command = './run.sh'

# get the date from one of the image files
name = ''
for f in os.listdir(image_dir):
    if not f.endswith('.jpg'):
        continue
    name = f[:10]
    break
# pack all images into one archive, so we have only one transfer
os.system('tar -C {} -c -f images.tar .'.format(image_dir))

aws = AWS(region='eu-central-1', logger=log)
log.info('uploading image files from {} to AWS S3 bucket {}'.format(image_dir, bucket_in))
aws.upload(bucket_in, [ 'images.tar' ])
os.remove('images.tar')

log.info('starting EC2 instance {}'.format(instance_id))
aws.start_instance(instance_id, wait=True)

log.info('starting command {} in instance'.format(command))
response = aws.send_commands(instance_id, [ '#!/bin/bash', 'cd /home/ec2-user', 'su -c "{}" ec2-user'.format(command) ])
response = aws.wait_for_ssm_command(response, timeout=1200, interval=60)

log.info('stopping EC2 instance {}'.format(instance_id))
aws.stop_instance(instance_id)

log.info('cleanup {}'.format(bucket_in))
aws.delete(bucket_in, [ 'images.tar' ])

movie_file_name = name + '.mp4'
log.info('downloading movie file from AWS S3 bucket {} to {}'.format(bucket_out, movie_file_name))
aws.download(bucket_out, [ movie_file_name, 'run.log' ])

log.info('cleanup {}'.format(bucket_out))
aws.delete(bucket_out, [ movie_file_name ])
