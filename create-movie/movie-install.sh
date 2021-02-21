sudo amazon-linux-extras install epel
sudo yum install gcc git nasm x264-devel python3 python3-pip dejavu-sans-fonts
sudo pip3 install numpy pillow requests
git clone https://git.ffmpeg.org/ffmpeg.git
cd ffmpeg
./configure --enable-libx264 --enable-gpl
make install
