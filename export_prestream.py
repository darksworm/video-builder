# Multipart video ffmpeg script generation script.
# Uses `prestream.yaml` to generate multi-section videos.
#
# Example config - generates video with name "prestream.mp4" which consists of
# two parts - "darkness_5_sec" and "countdown_initial"
#
#  videos:
#    darkness_5_sec:
#      # these vars override globals for the specific video
#      vars:
#        duration: 5
#      options:
#        # you can either add custom string options
#        - "-i $darkness_img"
#        - "-t $duration"
#
#        # or use "preset_options"
#        - shared_options
#
#    countdown_initial:
#      vars:
#        duration: 1200
#      options:
#        - "-i $darkness_img"
#        - "-t $duration"
#        - shared_options
#        - countdown
#        - "-strict 2"
#
#  output:
#    name: prestream
#    parts:
#      - darkness_5_sec
#      - countdown_initial
#
#  preset_options:
#    shared_options: "\
#      -g $keyframe_framenr \
#      -keyint_min $keyframe_framenr \
#      -r $fps"
#
#    countdown: -vf "fps=$fps,drawtext=x=(w-text_w)/2:y=(h-text_h)/2:text='%{eif\:(($duration-t)/60)\:d\:2}\:%{eif\:mod(($duration-t),60)\:d\:2}'"
#
#  # global options are always applied first for every video
#  global_options:
#    - "-y"
#    - "-loop 1"
#
#  # global variables are applied for all videos
#  global_vars:
#    assets: /home/ilmars/dev/devops/nginx-streamer/assets
#    fps: 24
#    keyframe_framenr: 48
#    darkness_img: $assets/blackness.png

import yaml
import os

# creates a bash script with name {name}.bash
def start_script(name):
    f = open(f'export/{name}.bash', 'w')
    f.write('#!/bin/bash\nset -e -u\n\n')
    return f

# writes varibales from {var_dict} to {file_to}
def write_vars(file_to, var_dict):
    for var, val in var_dict.items():
        file_to.write(f'{var}={val}\n')

# alias for writing global variables
def write_globals(file_to):
    write_vars(file_to, conf()['global_vars'])

# writes all ffpmeg options/params from {opt_list} to {file_to}
# if an opt is a string, it will be interpreted as a preset option.
# if an opt is a dict, it will be interpreted as a custom option and the dicts
# first value will be written instead.
def write_options(file_to, opt_list):
    for option in opt_list:
        if type(option) is dict:
            option = option[list(option.keys())[0]]
            write_options(file_to, option)
        else:
            presets = conf()['preset_options']

            if option in presets.keys():
                formatted = '\t'.join(presets[option].splitlines(True))
                file_to.write(f'\t{formatted}\\\n')
            else:
                file_to.write(f'\t{option} \\\n')

def write_global_options(file_to):
    write_options(file_to, conf()['global_options'])

# gets config from prestream.yaml or cache
def conf():
    if conf.config:
        return conf.config
    else:
        with open('prestream.yaml', 'r') as file:
            conf.config = yaml.load(file, Loader=yaml.FullLoader)
        return conf()
conf.config = 0

# the magic starts here

scripts_to_execute = []
main_script_name = 'generate_prestream'
videos = conf()['videos'].keys()
output_parts = conf()['output']['parts']

# this bash function generates and runs the ffmpeg command to combine all of
# the videos passed in as the second parameter to filename in the first
bash_concat_function = """\
function concat_videos() {
  videos=("$@")

  lim=`expr ${#videos[@]} - 1`

  for i in `seq 0 $lim`; do
      fc="$fc[$i:v][$i:a]"
  done

  # put all the videos together
  ffmpeg \\
      -y \\
      ${videos[@]/#/-i } \\
      -filter_complex "${fc}concat=n=${#videos[@]}:v=1:a=1[a][v]" \\
      -map "[v]" \\
      -map "[a]"  \\
      -bsf:a aac_adtstoasc \\
      -b:a 256k \\
""" + conf()['preset_options']['shared_options'] + " \\" \
"""
      $output_file
}
"""

for op in output_parts:
    if op not in videos:
        print(f'"{op}", defined in output parts not found in video section!')
        exit(1)

for title, video_config in conf()['videos'].items():
    # don't generate videos which won't be used in the output
    if title not in output_parts:
        print(f'video {title} not found in output parts, skipping it.\n')
        continue

    video_script = start_script(title)
    write_globals(video_script)

    # any global vars with same name will be overwritten by video vars
    write_vars(video_script, video_config['vars'])

    video_script.write('\nffmpeg \\\n')
    write_global_options(video_script)
    write_options(video_script, video_config['options'])
    video_script.write(f'\t{title}.mp4 1>/dev/null\n\n')

    # output the resulting video lenght
    video_script.write(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {title}.mp4 | cut -d. -f1')

    video_script.close()

    scripts_to_execute.append(f'export {title}_length=$(bash {title}.bash)')

with start_script(main_script_name) as main_script:
    write_globals(main_script)

    output_fn = conf()['output']['name'] + '.mp4';
    main_script.write('output_file=' + output_fn + '\n')

    main_script.write("\n" + bash_concat_function + "\n")

    # set up list of videos that need to be concatenated
    parts = [name + '.mp4' for name in conf()['output']['parts']]

    # run all the video generation scripts
    main_script.write(' && \\\n'.join([s for s in scripts_to_execute]))

    # and then concat the videos
    main_script.write(' && \\\n')
    main_script.write('concat_videos ' + ' '.join([p for p in parts]) + '\n')

# run the generated script
os.chdir('export')
os.system('chmod +x *.bash')
os.system(f'bash {main_script_name}.bash')
