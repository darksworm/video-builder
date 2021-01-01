from typing import List, final

from bash_writer import bash_code
from bash_writer.builders import BashCodeBuilder
from bash_writer.builders import StaticBashCodeBuilder, VideoScriptCallBuilder, BashVariableBuilder, \
    FFmpegGenerateBuilder, FFmpegConcatBuilder, VideoListVariableBuilder
from config.config import VideoConfig, Config


@final
class BashScriptWriter:
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._file = None

    def __del__(self):
        self.close_file()

    def __enter__(self) -> 'BashScriptWriter':
        return self

    def __exit__(self, a, b, c):
        self.close_file()

    def _open_file(self) -> None:
        if self._file is None:
            self._file = open(self._file_path, 'w')

    @staticmethod
    def _generate_bash(builders: List[BashCodeBuilder]) -> str:
        fragments = [builder.build() for builder in builders]
        return '\n'.join(fragments)

    def write(self, builders: List[BashCodeBuilder]) -> None:
        bash = self._generate_bash(builders)
        self._open_file()
        self._file.write(bash)

    def close_file(self) -> None:
        if self._file is not None:
            self._file.close()


def write_main_script(config: Config, videos: List[VideoConfig]) -> None:
    code_builders = [
        StaticBashCodeBuilder(bash_code.script_beginning),
        BashVariableBuilder(config.get_variables()),
        VideoScriptCallBuilder(videos)
    ]

    with BashScriptWriter(config.get_script_path()) as writer:
        writer.write(code_builders)


def write_video_script(video: VideoConfig) -> None:
    command_builder = FFmpegGenerateBuilder
    skip_regenerate = bash_code.skip_regenerate_existing_video

    if video.is_combination():
        skip_regenerate = bash_code.concat_video_md5 + skip_regenerate
        command_builder = FFmpegConcatBuilder

    builders = [
        StaticBashCodeBuilder(bash_code.script_beginning),

        BashVariableBuilder(video.get_variables()),
        VideoListVariableBuilder(video),

        StaticBashCodeBuilder(skip_regenerate),

        command_builder(video.get_options()),

        StaticBashCodeBuilder(bash_code.metadata_writer),
        StaticBashCodeBuilder(bash_code.video_script_output)
    ]

    with BashScriptWriter(video.get_script_path()) as writer:
        writer.write(builders)


def write_video_scripts(videos: List[VideoConfig]) -> None:
    for video in videos:
        write_video_script(video)
