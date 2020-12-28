def get_static_video_variables(video_title):
    return {
        'output_file': video_title + '.mp4',
        'script_path': '$(readlink --canonicalize-existing "$0")',
        'script_md5': '$(md5sum $script_path | cut -d" " -f1)',
        'video_md5': '$(exiftool $output_file | grep Artist | cut -d":" -f2 | xargs)'
    }


def write_video_variables(file_to, video):
    write_bash_variables(file_to, video.config.get_variables())
    write_video_list_variable(file_to, video)


def write_bash_variables(file_to, var_dict):
    for var, val in var_dict.items():
        file_to.write(f'{var}={val}\n')
    file_to.write('\n')


def write_video_list_variable(file_to, video):
    if video.config.is_combination():
        video_list = video.config.get_combine()
    else:
        video_list = [video.config.get_title()]

    video_list_string = ' '.join([video_name + '.mp4' for video_name in video_list])
    file_to.write(f'videos=( {video_list_string} )\n\n')
