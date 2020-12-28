from typing import TextIO, List

import bash_code
from config import Config, VideoConfig


def create_script(path: str, name: str) -> TextIO:
    f = open(f'{path}/{name}', 'w')
    f.write('#!/bin/bash\nset -e -u\n\n')
    return f


def write_main_script(videos: List[VideoConfig], config: Config) -> None:
    variables = config.get_variables()
    with create_script(config.get_export_path(), 'generate.bash') as script:
        write_bash_variables(script, variables)
        write_video_script_calls(script, videos)
        script.close()


def write_video_script_calls(file_to: TextIO, videos: List[VideoConfig]) -> None:
    calls = map(get_video_call_bash_code, videos)
    file_to.write(' && \\\n'.join([c for c in calls]))


def write_video_scripts(videos: List[VideoConfig], config: Config) -> None:
    for video in videos:
        write_video_script(video, config)


def write_video_script(video: VideoConfig, config: Config) -> None:
    file_path = config.get_export_path() + video.get_script_name()
    with open(file_path, 'w') as video_file:
        write_video_variables(video_file, video)
        write_video_skip_logic(video_file, video)
        write_ffmpeg_command(video_file, video)
        write_video_metadata_code(video_file)
        write_video_exit_statement(video_file)


def write_video_exit_statement(file_to: TextIO) -> None:
    file_to.write(bash_code.script_return_command)


def write_video_skip_logic(file_to: TextIO, video: VideoConfig) -> None:
    if video.is_combination():
        file_to.write(bash_code.concat_video_md5)
    file_to.write(bash_code.skip_regenerate_existing_video)


def get_video_call_bash_code(video: VideoConfig) -> str:
    return f'export {video.get_title()}_length=$(bash {video.get_script_name()})'


def write_video_metadata_code(file_to: TextIO) -> None:
    # save generation script md5 in generated videos "artist" metadata field
    file_to.write(f'exiftool $output_file -artist="$script_md5" 1>/dev/null\n')
    # remove the backup file created by exiftool
    file_to.write('rm ${output_file}_original\n\n')


def write_ffmpeg_command(file_to: TextIO, video: VideoConfig) -> None:
    if video.is_combination():
        write_ffmpeg_concat_command(file_to, video)
    else:
        write_ffmpeg_generate_command(file_to, video)


def write_ffmpeg_concat_command(file_to: TextIO, video: VideoConfig) -> None:
    file_to.write(bash_code.concat_function_1)
    write_ffmpeg_options(file_to, video.get_options())
    file_to.write(bash_code.concat_function_2 + "\n")
    file_to.write('\nconcat_videos ${videos[@]}\n\n')


def write_ffmpeg_generate_command(file_to: TextIO, video: VideoConfig) -> None:
    file_to.write('\nffmpeg \\\n')
    write_ffmpeg_options(file_to, video.get_options())
    file_to.write(f'\t$output_file 1>/dev/null\n\n')


def write_ffmpeg_options(file_to: TextIO, options: list) -> None:
    for option in options:
        if type(option) is dict:
            first_key = list(option.keys())[0]
            first_elem = option[first_key]
            write_ffmpeg_options(file_to, first_elem)
        else:
            file_to.write(f'\t{option} \\\n')


def write_video_variables(file_to: TextIO, video: VideoConfig) -> None:
    write_bash_variables(file_to, video.get_variables())
    write_video_list_variable(file_to, video)


def write_bash_variables(file_to: TextIO, variables: dict) -> None:
    for var, val in variables.items():
        file_to.write(f'{var}={val}\n')
    file_to.write('\n')


def write_video_list_variable(file_to: TextIO, video: VideoConfig) -> None:
    if video.is_combination():
        video_list = video.get_combine()
    else:
        video_list = [video.get_title()]

    video_list_string = ' '.join([video_name + '.mp4' for video_name in video_list])
    file_to.write(f'videos=( {video_list_string} )\n\n')
