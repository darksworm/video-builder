#!/bin/bash

fps=24
seconds=10
fontsize=372
fontcolor=#b50411

font=assets/font.ttf
background=assets/blackness.png
thanks=assets/thanks.png
remember=assets/remember.png
movie=assets/movie.mp4
bgmusic=assets/backgroundmusic.mp3

uplink=rtmp:127.0.0.1/show/live

ffmpeg \
    -loop 1 \
    -i $background \
    -i $bgmusic \
    -c:v libx264 \
    -c:a aac \
    -filter "volume=0.07" \
    -r $fps \
    -t $seconds \
    -pix_fmt yuv420p \
    -vf \
    "\
        fps=$fps, \
        drawtext=fontfile='$font' \
        :fontcolor=$fontcolor \
        :fontsize=$fontsize \
        :x=(w-text_w)/2 \
        :y=(h-text_h)/2 \
        :text='%{eif\:(($seconds-t)/60)\:d\:2}\:%{eif\:mod(($seconds-t),60)\:d\:2}' \
    " \
    -loop -1 \
    -ar 44100 \
    -strict -2 \
    -f flv \
    $uplink \
&& \
ffmpeg \
    -loop 1 \
    -i $background \
    -c:v libx264 \
    -t 5 \
    -pix_fmt yuv420p \
    -vf scale=1920:1080 \
    -f flv $uplink \
&& \
ffmpeg \
    -loop 1 \
    -i $remember \
    -c:v libx264 \
    -t 8 \
    -pix_fmt yuv420p \
    -vf scale=1920:1080 \
    -f flv $uplink \
&& \
ffmpeg \
    -loop 1 \
    -i $thanks \
    -c:v libx264 \
    -t 8 \
    -pix_fmt yuv420p \
    -vf scale=1920:1080 \
    -f flv $uplink \
&& \
ffmpeg \
    -loop 1 \
    -i $background \
    -c:v libx264 \
    -t 5 \
    -pix_fmt yuv420p \
    -vf scale=1920:1080 \
    -f flv $uplink \
&& \
ffmpeg \
    -re \
    -i $movie \
    -c:v libx264 \
    -c:a aac \
    -loop -1 \
    -ar 44100 \
    -strict -2 \
    -f flv $uplink;
