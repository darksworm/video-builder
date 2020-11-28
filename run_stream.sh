#!/bin/bash
set -e

uplink=rtmp:127.0.0.1/show/live?pwd=change_this_password
videos=(prestream.mp4 keyframed_movie.mp4)

for item in ${videos[*]}
do
    ffmpeg \
        -re \
        -i export/$item \
        -c:v copy \
        -c:a copy \
        -f flv \
        $uplink;
done
