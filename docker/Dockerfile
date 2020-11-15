FROM ubuntu:focal

RUN apt update

RUN apt install -y nginx libnginx-mod-rtmp

RUN mkdir -p /mnt/hls/keys
RUN mkdir /mnt/not-exist
RUN mkdir /etc/nginx/ssl

COPY ssl /etc/nginx/ssl

COPY index.html /mnt/index.html
COPY nginx.conf /etc/nginx/nginx.conf

RUN nginx -t

CMD nginx
