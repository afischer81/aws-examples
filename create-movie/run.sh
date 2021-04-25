#!/bin/bash

function create_movie {
    mkdir -p images
    aws s3 cp s3://af-imageproc-in/images.tar images.tar
    tar -C images -x -f images.tar
    rm -f images.tar
    movie_file=$(ls images | head -1 | cut -d_ -f1).mp4
    ./images-to-movie.py images ${movie_file}
    rm -f /tmp/img_*.jpg
    aws s3 cp ${movie_file} s3://af-imageproc-out
    rm -f ${movie_file}
}

log=run.log
create_movie > ${log} 2>&1
aws s3 cp ${log} s3://af-imageproc-out
#rm -f ${log}
