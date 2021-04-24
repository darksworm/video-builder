## Video generator
![tests](https://github.com/darksworm/video-builder/workflows/tests/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/darksworm/video-builder/badge.svg?branch=master)](https://coveralls.io/github/darksworm/video-builder?branch=master)

Works as a facade for FFmpeg.

Generates bash scripts to generate videos with ffmpeg.

Uses YAML to define video contents, options.

## Example

Task: Generate a video with 5 seconds of darkness, followed by a "thanks for watching" image for 8 seconds, followed by another 5 seconds of darkness.

1. Define videos in YAML

```yaml
shared_options:
  - "-y"
  - "-v warning"
  - "-hide_banner"
  - "-stats"

shared_variables:
  assets: /mnt/assets
  darkness_img: $assets/blackness.png
  thanks_img: $assets/thanks_img.png
  audio_rate: 44100

option_templates:
  blank_audio_options: "-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=$audio_rate"

videos:
  darkness_5_sec:
    variables:
      duration: 5
    options:
      - "-loop 1"
      - "-i $darkness_img"
      - "-t $duration"
      - blank_audio_options

  thanks:
    variables:
      duration: 8
    options:
      - "-loop 1"
      - "-i $thanks_img"
      - blank_audio_options
      - "-t $duration"
  
  prestream:
    options:
      - "-c:v h264"
      - "-c:a aac"
    combine:
      - darkness_5_sec
      - thanks
      - darkness_5_sec
```

2. Run `build_videos.py`

```bash
python build_videos.py prestream.yaml export
```

3. Enjoy
