#!/bin/bash
set -e

uplink=rtmp:127.0.0.1/show/live
videos=(countdown.mp4 2nd.mp4 1st.mp4 3rd.mp4 1st.mp4 movie.mp4)

for item in ${videos[*]}
do
    ffmpeg \
        -re \
        -i assets/$item \
        -c:v copy \
        -c:a copy \
        -f flv \
        $uplink;
done
