#!/bin/bash
set -e

uplink=rtmp:127.0.0.1/show/stream?pwd=change_this_password
videos=(prestream.mp4) #keyframed_movie.mp4)

for item in ${videos[*]}
do
    [ ! -f "export/$item" ] && echo "File export/$item does not exist!" && exit 1
done

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
