FROM ubuntu:focal

RUN apt update

RUN apt install -y ffmpeg

CMD ffmpeg -i https://unfixed.art/live.m3u8 -c copy output1.mkv
