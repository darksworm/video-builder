# NGINX HLS streamer

Streaming setup created for movie night. Includes a minutes, seconds countdown and capable of displaying images before movie starts. Streams over HTTPS.

### Setup
1. place ssl cert and key (cert.pem, privkey.pem) in `docker/ssl/`
2. place movie in `assets/movie.mp4`
3. change vars in `stream.sh` to suit your needs

### Streaming
1. run `nginx.sh` to run nginx docker container (will kill all other containers)
2. run `stream.sh` to start the ffmpeg stream
3. run `renice.sh` as root to set ffmpeg + nginx process priorities

### Viewing
1. open VLC media player
2. CTRL+N or Media -> Open network stream
3. enter `https://stream.emojigun.com/live.m3u8`
4. press play

### Caveats
1. specifically made for one movie (styling may not fit others)
2. stream runs only on https, http should redirect
3. stream will only run on host `stream.emojigun.com`
