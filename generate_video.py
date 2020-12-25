# Multipart video ffmpeg script generation script.
# Uses yaml file (from first arg) to generate multi-section videos.
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
#    prestream:
#      combine:
#        - darkness_5_sec
#        - countdown_initial
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
#
#
# Example usage - generate video from config "prestream.yaml" and overwrite
# already existing files
# python generate_video.py prestream.yaml -y

import yaml
import os
import sys

# creates a bash script with name {name}.bash
def start_script(name):
    f = open(f'export/{name}', 'w')
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
def conf(filename=""):
    if conf.config:
        return conf.config
    else:
        with open(filename, 'r') as file:
            return yaml.load(file, Loader=yaml.FullLoader)
conf.config = 0

def confirm():
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("OK to continue [Y/N]? ").lower()
    return answer == "y"

# the magic starts here

if len(sys.argv) < 2:
    print('Please pass the config yaml as the first parameter!')
    sys.exit(1)

config_file = sys.argv[1]

if not os.path.exists(config_file):
    print(f'Passed file "{config_file}" does not exist!')
    sys.exit(2)

overwrite_all = "-y" in sys.argv

if overwrite_all:
    print("Going to overwrite all existing files.")
    if not confirm():
        sys.exit(3)

conf.config = conf(config_file)

scripts_to_execute = []
main_script_name = 'generate_video.bash'
videos = conf()['videos'].keys()

# this bash function generates and runs the ffmpeg command to combine all of
# the videos passed in as the second parameter to filename in the first
bash_concat_function_1 = """\
function concat_videos() {
  videos=("$@")

  lim=`expr ${#videos[@]} - 1`
  fc=""

  for i in `seq 0 $lim`; do
      fc="$fc[$i:v][$i:a]"
  done

  # put all the videos together
  ffmpeg \\
    -y \\
    ${videos[@]/#/-i } \\
    -filter_complex "${fc}concat=n=${#videos[@]}:v=1:a=1[a][v]" \\
    -map "[v]" \\
    -map "[a]" \\
"""
bash_concat_function_2 = """\
    $output_file
}
"""

bash_script_return_command = """\
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $output_file | cut -d. -f1\
"""

bash_confirm_video_overwrite = f"""\
if [ -f "$output_file" ]; then
    read -p "$output_file already exists, overwrite? (y|n) " -n 1 -r
    >&2 echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        {bash_script_return_command}
        exit 1
    fi
fi
"""

for title, video_config in conf()['videos'].items():
    script_name = f'export_{title}.bash'
    video_script = start_script(script_name)
    write_globals(video_script)

    if 'vars' in video_config.keys():
        # any global vars with same name will be overwritten by video vars
        write_vars(video_script, video_config['vars'])

    video_script.write(f'output_file={title}.mp4\n\n')

    if not overwrite_all:
        video_script.write(bash_confirm_video_overwrite)

    if 'combine' in video_config.keys():
        video_script.write("\n" + bash_concat_function_1)
        write_options(video_script, video_config['options'])
        video_script.write(bash_concat_function_2 + "\n")

        parts = [name + '.mp4' for name in video_config['combine']]
        parts = ' '.join([p for p in parts])
        video_script.write('concat_videos ' + parts  + '\n')

        video_script.write('\n')
    else:
        video_script.write('\nffmpeg \\\n')
        write_global_options(video_script)
        write_options(video_script, video_config['options'])
        video_script.write(f'\t$output_file 1>/dev/null\n\n')

    # output the resulting video lenght
    video_script.write(bash_script_return_command)

    video_script.close()

    scripts_to_execute.append(f'export {title}_length=$(bash {script_name})')

with start_script(main_script_name) as main_script:
    write_globals(main_script)

    main_script.write("\n")

    # run all the video generation scripts
    main_script.write(' && \\\n'.join([s for s in scripts_to_execute]))

# run the generated script
os.chdir('export')
os.system('chmod +x *.bash')
os.system(f'bash {main_script_name}')
