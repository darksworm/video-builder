Example config - generates video with name "prestream.mp4" which consists of
two parts - "darkness_5_sec" and "countdown_initial"

```yaml
 videos:
   darkness_5_sec:
     # these variables override globals for the specific video
     variables:
       duration: 5
     options:
       # you can either add custom string options
       - "-i $darkness_img"
       - "-t $duration"

       # or use "preset_options"
       - shared_options

   countdown_initial:
     variables:
       duration: 1200
     options:
       - "-i $darkness_img"
       - "-t $duration"
       - shared_options
       - countdown
       - "-strict 2"

   prestream:
     combine:
       - darkness_5_sec
       - countdown_initial

 # refering to these template names in video options will replace the names
 # with values declared here
 option_templates:
   shared_options: "\
     -g $keyframe_framenr \
     -keyint_min $keyframe_framenr \
     -r $fps"

   countdown: -vf "fps=$fps,drawtext=x=(w-text_w)/2:y=(h-text_h)/2:text='%{eif\:(($duration-t)/60)\:d\:2}\:%{eif\:mod(($duration-t),60)\:d\:2}'"

 # shared options are always applied first for every video
 shared_options:
   - "-y"
   - "-loop 1"

 # shared variables are applied for all videos
 shared_variables:
   assets: /home/ilmars/dev/devops/nginx-streamer/assets
   fps: 24
   keyframe_framenr: 48
   darkness_img: $assets/blackness.png
```

Example usage - generate video from config "prestream.yaml" to directory "export"
```bash
python generate_video.py prestream.yaml export
```
