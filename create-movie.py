import logging
import os
import sys

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
files = []
for f in os.listdir(image_dir):
    if not f.endswith('.jpg'):
        continue
    files.append(os.path.join(image_dir, f))
aws = AWS(region='eu-central-1', logger=log)
log.info('uploading image files from {} to AWS S3 bucket {}'.format(image_dir, bucket_in))
aws.upload(bucket_in, files)
log.info('starting EC2 instance {}'.format(instance_id))
aws.start_instance(instance_id, wait=True)
log.info('starting command {} in instance'.format(command))
aws.send_commands(instance_id, [ command ], wait=True)
log.info('stopping EC2 instance {}'.format(instance_id))
aws.stop_instance(instance_id)
log.info('cleanup {}'.format(bucket_in))
aws.delete(bucket_in, files)
movie_file_name = os.path.basename(files[1])[:10] + '.mp4'
log.info('downloading movie file from AWS S3 bucket {} to {}'.format(bucket_out, movie_file_name))
aws.download(bucket_out, [ movie_file_name ])
log.info('cleanup {}'.format(bucket_out))
aws.delete(bucket_out, [ movie_file_name ])
