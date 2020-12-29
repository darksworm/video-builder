from typing import TextIO, List, Dict, final

import bash_code
from config import VideoConfig


class BashCodeBuilder:
    def build(self) -> str:
        raise NotImplementedError()


@final
class StaticBashCodeBuilder(BashCodeBuilder):
    def __init__(self, code):
        self._code = code

    def build(self):
        return self._code + "\n"


@final
class BashScript:
    def __init__(self, file: TextIO, builders: List[BashCodeBuilder]):
        self._file = file
        self._code_builders = builders

    def __del__(self):
        self.close_file()

    def _generate_bash(self):
        fragments = [builder.build() for builder in self._code_builders]
        return '\n'.join(fragments)

    def write(self):
        bash = self._generate_bash()
        self._file.write(bash)

    def close_file(self):
        self._file.close()


@final
class BashVariableBuilder(BashCodeBuilder):
    def __init__(self, variables: Dict[str, str]):
        self._variables = variables

    def build(self) -> str:
        fragments = [f'{name}={value}\n' for name, value in self._variables.items()]
        return '\n'.join(fragments)


@final
class BashVideoScriptCallBuilder(BashCodeBuilder):
    def __init__(self, videos: List[VideoConfig]):
        self._videos = videos

    @staticmethod
    def _get_video_script_call_code(video: VideoConfig) -> str:
        return f'export {video.get_title()}_length=$(bash {video.get_script_name()})'

    def build(self) -> str:
        videos_code = map(self._get_video_script_call_code, self._videos)
        joined_code = ' && \\\n'.join(videos_code)
        return joined_code


def write_main_script(file: TextIO, videos: List[VideoConfig], variables: Dict[str, str]) -> None:
    code_builders = [
        StaticBashCodeBuilder('#!/bin/bash'),
        StaticBashCodeBuilder('set -e -u'),
        BashVariableBuilder(variables),
        BashVideoScriptCallBuilder(videos)
    ]

    script = BashScript(file, code_builders)
    script.write()


def create_file(path: str, name: str = "") -> TextIO:
    return open(f'{path}{name}', 'w')


def write_video_scripts(videos: List[VideoConfig]) -> None:
    for video in videos:
        write_video_script(video)


def write_video_script(video: VideoConfig) -> None:
    with create_file(video.get_script_path()) as video_file:
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
