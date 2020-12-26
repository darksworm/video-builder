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

# write global and opt_list ffpmeg options/flags
def write_options(file_to, opt_list, config):
    if opt_list != config['global_options']:
        write_options(file_to, config['global_options'], config)

    for option in opt_list:
        if type(option) is dict:
            option = option[list(option.keys())[0]]
            write_options(file_to, option)
        else:
            presets = config['preset_options']

            if option in presets.keys():
                formatted = '\t'.join(presets[option].splitlines(True))
                file_to.write(f'\t{formatted}\\\n')
            else:
                file_to.write(f'\t{option} \\\n')

def load_yaml_config(filename=""):
    with open(filename, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)

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

config = load_yaml_config(config_file)

scripts_to_execute = []
main_script_name = 'generate_video.bash'
videos = config['videos'].keys()

bash_concat_function_1 = """\
# combine all files from arguments with ffmpeg using filter_complex and map
function concat_videos() {
  videos=("$@")

  lim=`expr ${#videos[@]} - 1`
  filter_compex=""

  for i in `seq 0 $lim`; do
      filter_complex="$filter_complex[$i:v][$i:a]"
  done

  ffmpeg \\
    -y \\
    ${videos[@]/#/-i } \\
    -filter_complex "${filter_complex}concat=n=${#videos[@]}:v=1:a=1[a][v]" \\
    -map "[v]" \\
    -map "[a]" \\
"""
bash_concat_function_2 = """\
    $output_file
}
"""

bash_script_return_command = """\
# output generated videos duration in seconds
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $output_file | cut -d. -f1\
"""

bash_skip_regenerate_existing_video = f"""\
# if the md5 stored in the video file matches this scripts md5, there is no
# need to regenerate the video as it is up to date.
if [ -f "$output_file" ] && [ "$script_md5" = "$video_md5" ]; then
    >&2 echo "$output_file already up to date, skipping it!"
    {bash_script_return_command}
    exit 1
fi
>&2 echo "Generating $output_file..."
"""

bash_concat_video_md5 = """\
# for concatenated videos, generate the script hash from the combination of all
# consumed video scripts
for video in "${videos[@]}"
do
    dir=$(dirname $script_path)
    name=export_$(echo $video | cut -d"." -f1 | xargs).bash
    script_md5=${script_md5}$(md5sum $dir/$name | cut -d" " -f1)
done
script_md5=$(echo $script_md5 | md5sum | cut -d" " -f1)
"""

for title, video_config in config['videos'].items():
    script_name = f'export_{title}.bash'
    video_script = start_script(script_name)

    video_script.write(f'output_file={title}.mp4\n\n')
    video_script.write('script_path=$(readlink --canonicalize-existing "$0")\n')
    video_script.write('script_md5=$(md5sum $script_path | cut -d" " -f1)\n')
    video_script.write('video_md5=$(exiftool $output_file | grep Artist | cut -d":" -f2 | xargs)\n')

    write_vars(video_script, config['global_vars'])

    if 'vars' in video_config.keys():
        # any global vars with same name will be overwritten by video vars
        write_vars(video_script, video_config['vars'])

    video_script.write('\n')

    if 'combine' in video_config.keys():
        video_script.write(bash_concat_function_1)
        write_options(video_script, video_config['options'], config)
        video_script.write(bash_concat_function_2 + "\n")

        parts = [name + '.mp4' for name in video_config['combine']]
        parts = ' '.join([p for p in parts])

        video_script.write('videos=( ' + parts + ' )\n\n')
        video_script.write(bash_concat_video_md5 + "\n")

        if not overwrite_all:
            video_script.write(bash_skip_regenerate_existing_video)

        video_script.write('\nconcat_videos ${videos[@]}\n')

        video_script.write('\n')
    else:
        if not overwrite_all:
            video_script.write(bash_skip_regenerate_existing_video)

        video_script.write('\nffmpeg \\\n')
        write_options(video_script, video_config['options'], config)
        video_script.write(f'\t$output_file 1>/dev/null\n\n')

    # save generation script md5 in generated videos "artist" metadata field
    video_script.write(f'exiftool $output_file -artist="$script_md5" 1>/dev/null\n')
    # remove the backup file created by exiftool
    video_script.write('rm ${output_file}_original\n\n')
    # output the resulting video length
    video_script.write(bash_script_return_command)

    video_script.close()

    scripts_to_execute.append(f'export {title}_length=$(bash {script_name})')

with start_script(main_script_name) as main_script:
    write_vars(main_script, config['global_vars'])

    main_script.write("\n")
    # run all the video generation scripts
    main_script.write(' && \\\n'.join([s for s in scripts_to_execute]))

# run the generated script
os.chdir('export')
os.system('chmod +x *.bash')
os.system(f'bash {main_script_name}')
