# NGINX HLS VOD streamer

Streaming setup created for movie night. Includes a minutes, seconds countdown and capable of displaying images before VOD starts. Streams over HTTPS.

### Setup
1. place ssl cert and key (cert.pem, privkey.pem) in `docker/ssl/`
2. place prepared VOD in `export/keyframed_movie.mp4` (see [VOD preparation](#vod_prep))
3. change vars in `export_prestream.sh` to suit your needs
4. run `export_prestream.sh`

### Streaming
1. run `run_nginx.sh` to run nginx docker container (will kill all other containers)
2. run `run_stream.sh` to start the ffmpeg stream

### Viewing
1. open VLC media player
2. CTRL+N or Media -> Open network stream
3. enter `https://unfixed.art/live`
4. press play

[detailed instructions available here](https://imgur.com/a/jZoCTvb)

### Caveats
1. created specifically for one VOD (styling may not fit others)
2. stream runs only on https, http will be redirected
3. stream will only run on host `unfixed.art`

### <a name="vod_prep"></a>VOD preparation
```bash
ffmpeg \
    -y \
    -i /path/to/vod \
    -g 48 \
    -keyint_min 48 \
    -sc_threshold 0 \
    -c:v h264 \
    -c:a aac \
    -bsf:a aac_adtstoasc \
    -b:v 3M -maxrate 3M -bufsize 1M \
    -strict 2 \
    export/keyframed_movie.mp4
```
