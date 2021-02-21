#!/bin/bash

mkdir images
aws s3 cp s3://af-imageproc-in images --recursive --include "*.jpg"
movie_file=$(ls images | head -1 | cut -d_ -f1).mp4
./images-to-movie.py images ${movie_file}
rm -f /tmp/img_*.jpg
aws s3 cp ${movie_file} s3://af-imageproc-out
rm -f ${movie_file}
