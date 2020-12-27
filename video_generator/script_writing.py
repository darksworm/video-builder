import bash_code
from variables import write_video_variables, write_bash_variables

def create_script(path, name):
    f = open(f'{path}/{name}', 'w')
    f.write('#!/bin/bash\nset -e -u\n\n')
    return f

def write_main_script(videos, config):
    variables = config.get_variables()
    with create_script(config.get_export_path() ,'generate.bash') as script:
        write_bash_variables(script, variables)
        write_video_script_calls(script, videos)
        script.close()

def write_video_script_calls(file_to, videos):
    calls = map(get_video_call_bash_code, videos)
    file_to.write(' && \\\n'.join([c for c in calls]))

def write_video_scripts(videos, global_config):
    for video in videos:
        write_video_script(video, global_config)

def write_video_script(video, global_config):
    file_path = global_config.get_export_path() + video.script_name
    with open(file_path, 'w') as video_file:
        write_video_variables(video_file, video)
        write_video_skip_logic(video_file, video)
        write_ffmpeg_command(video_file, video)
        write_video_metadata_code(video_file, video)
        write_video_exit_statement(video_file, video)

def write_video_exit_statement(file_to, video):
    file_to.write(bash_code.script_return_command)

def write_video_skip_logic(file_to, video):
    if video.config.is_combination():
        file_to.write(bash_code.concat_video_md5)
    file_to.write(bash_code.skip_regenerate_existing_video)

def get_video_call_bash_code(video):
    title = video.config.get_title()
    return f'export {title}_length=$(bash {video.script_name})'

def write_video_metadata_code(file_to, video):
    # save generation script md5 in generated videos "artist" metadata field
    file_to.write(f'exiftool $output_file -artist="$script_md5" 1>/dev/null\n')
    # remove the backup file created by exiftool
    file_to.write('rm ${output_file}_original\n\n')

def write_ffmpeg_command(file_to, video):
    if video.config.is_combination():
        write_ffmpeg_concat_command(file_to, video)
    else:
        write_ffmpeg_generate_command(file_to, video)

def write_ffmpeg_concat_command(file_to, video):
    file_to.write(bash_code.concat_function_1)
    write_ffmpeg_options(file_to, video.config.get_options())
    file_to.write(bash_code.concat_function_2 + "\n")
    file_to.write('\nconcat_videos ${videos[@]}\n\n')

def write_ffmpeg_generate_command(file_to, video):
    file_to.write('\nffmpeg \\\n')
    write_ffmpeg_options(file_to, video.config.get_options())
    file_to.write(f'\t$output_file 1>/dev/null\n\n')

def write_ffmpeg_options(file_to, option_list):
    for option in option_list:
        if type(option) is dict:
            first_key = list(option.keys())[0]
            first_elem = option[first_key]
            write_ffmpeg_options(file_to, first_elem)
        else:
            file_to.write(f'\t{option} \\\n')
