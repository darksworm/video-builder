docker build docker -t nginx-streamer && \
    docker kill $(docker ps -q) ; \
    docker run -d --rm -p 443:443 -p 80:80 -p 1935:1935 nginx-streamer:latest && \
    docker logs -tf $(docker ps -q)
