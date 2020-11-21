#!/bin/bash
fps=24
cd_dur=20
audio_fade_dur=15
fontsize=372
fontcolor=#b50411
audio_rate=44100

font=assets/font.ttf
background=assets/blackness.png
thanks=assets/thanks.png
remember=assets/remember.png
movie=assets/movie.mp4
bgmusic=assets/backgroundmusic.mp3

export_target=export/prestream.mp4

# remove all the temporary assets and previously generated prestream
rm -rf tmp > /dev/null 2>&1
mkdir tmp > /dev/null 2>&1
rm $export_target > /dev/null 2>&1

# exit on errors
set -e

# introduce keyframe/intraframe every 2 seconds
# this ensures that the video can be nicely split into ts chunks
# https://superuser.com/questions/908280/what-is-the-correct-way-to-fix-keyframes-in-ffmpeg-for-dash
keyframe_framenr=`expr $fps \* 2`

shared_opts="\
    -g $keyframe_framenr\
    -keyint_min $keyframe_framenr \
    -sc_threshold 0 \
    -c:v h264 \
    -c:a aac \
    -ac 2 \
    -ar $audio_rate \
    -r $fps"

blank_audio_opts="\
    -f lavfi \
    -i anullsrc=channel_layout=stereo:sample_rate=$audio_rate"

# set cd_dur + 1 otherwise it skips the first second
cd_dur=`expr $cd_dur + 1`
fade_start=`expr $cd_dur - $audio_fade_dur`

# generate countdown
ffmpeg \
    -loop 1 \
    -i $background \
    -i $bgmusic \
    -t $cd_dur \
    -af "volume=0.07,afade=t=out:st=$fade_start:d=$audio_fade_dur" \
    $shared_opts \
    -vf \
    "\
        fps=$fps, \
        drawtext=fontfile='$font' \
        :fontcolor=$fontcolor \
        :fontsize=$fontsize \
        :x=(w-text_w)/2 \
        :y=(h-text_h)/2 \
        :text='%{eif\:(($cd_dur-t)/60)\:d\:2}\:%{eif\:mod(($cd_dur-t),60)\:d\:2}' \
    " \
    -strict -2 \
    tmp/countdown.mp4

# generate darkness
ffmpeg \
    -loop 1 \
    -i $background \
    $blank_audio_opts \
    -t 5 \
    $shared_opts \
    tmp/spacer.mp4

# generate reminder video
ffmpeg \
    -loop 1 \
    -i $remember \
    $blank_audio_opts \
    -t 8 \
    $shared_opts \
    tmp/remember.mp4

# generate "thanks, enjoy" video
ffmpeg \
    -loop 1 \
    -i $thanks \
    $blank_audio_opts \
    -t 8 \
    $shared_opts \
    tmp/enjoy.mp4

prestream_chunks=(\
    tmp/spacer.mp4 \
    tmp/countdown.mp4 \
    tmp/spacer.mp4 \
    tmp/remember.mp4 \
    tmp/enjoy.mp4 \
    tmp/spacer.mp4
)

lim=`expr ${#prestream_chunks[@]} - 1`

for i in `seq 0 $lim`; do
    filter_complex="$filter_complex[$i:v][$i:a]"
done

# put all the videos together
ffmpeg \
    ${prestream_chunks[@]/#/-i } \
    -filter_complex "${filter_complex}concat=n=${#prestream_chunks[@]}:v=1:a=1[a][v]" \
    -map "[v]" \
    -map "[a]"  \
    -bsf:a aac_adtstoasc \
    -b:a 256k \
    $shared_opts \
    $export_target

rm -rf tmp > /dev/null 2>&1
