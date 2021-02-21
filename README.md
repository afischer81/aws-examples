# aws-examples

Amazon Web Services (AWS) examples for cloud computing

## Setup

* install [AWS commandline interface](https://aws.amazon.com/cli/)
* create/retrieve credentials in [IAM console](https://console.aws.amazon.com/iam/home)
* adjust paths to AWS and python executable in install.bat
* configure AWS client with the credentials obtained in the IAM console
```
install.bat configure
```
* create bucket(s) in [S3 management console ](https://s3.console.aws.amazon.com/)
* create and start instance in [EC2 console](https://console.aws.amazon.com/ec2/v2/home?region=eu-central-1)
* SSH connection to EC2 instance
** create keypair for instance and download it
** install the key in ssh client (e.g. MobaXTerm)
** copy public key to .ssh/authorized_keys in EC2 instance (make sure the rights are 400)

## Tests

* adjust test instance id and bucket name ``install.bat`` or ``install.sh``
* execute
```
install.bat tests
```
on a Windows system or
```
install.sh tests
```
on a Linux system.

## Create a movie from a set of time stamped images

* Create input (image upload) and output bucket (movie download) in S3 console
* Connect to EC2 instance
** copy content of create-movie directory to instance (via ssh client)
** build ffmpeg video encoder in instance
```
./movie-install.sh
```
* adjust create-movie.py call in ``install.bat``
* run
```
install.bat create-movie
```
on a Windows system or
```
install.sh create-movie
```
on a Linux system.
