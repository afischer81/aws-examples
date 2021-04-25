#!/bin/bash

EC2_INSTANCE=i-00d4bb1c2ee88275c

function do_install {
    sudo apt-get install -y awscli jq python3-pip
    sudo pip3 install boto3
}

function do_movie {
    python3 create-movie.py /data/raspi6/images/wetter/2021/03/29 ${EC2_INSTANCE} af-imageproc-in af-imageproc-out
}

function do_start {
    aws ec2 start-instances --instance-ids ${EC2_INSTANCE}
}

function do_status {
    aws ec2 describe-instances --instance-ids ${EC2_INSTANCE} | jq ".Reservations[0].Instances[0].State.Name" | sed -e 's/"//g'
}

task=$1
shift
do_$task $*
