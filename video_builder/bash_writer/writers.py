from typing import TextIO, List, final

from bash_writer import bash_code
from bash_writer.builders import BashCodeBuilder
from bash_writer.builders import StaticBashCodeBuilder, VideoScriptCallBuilder, BashVariableBuilder, \
    FFmpegGenerateBuilder, FFmpegConcatBuilder, VideoListVariableBuilder
from config.config import VideoConfig, Config


@final
class BashScriptWriter:
    def __init__(self, file: TextIO, builders: List[BashCodeBuilder]):
        self._file = file
        self._builders = builders

    def __del__(self):
        self.close_file()

    def _generate_bash(self):
        fragments = [builder.build() for builder in self._builders]
        return '\n'.join(fragments)

    def write(self):
        bash = self._generate_bash()
        self._file.write(bash)

    def close_file(self):
        self._file.close()


def create_file(path: str, name: str = "") -> TextIO:
    return open(f'{path}{name}', 'w')


def write_main_script(config: Config, videos: List[VideoConfig]) -> None:
    with create_file(config.get_script_path()) as file:
        code_builders = [
            StaticBashCodeBuilder(bash_code.script_beginning),
            BashVariableBuilder(config.get_variables()),
            VideoScriptCallBuilder(videos)
        ]

        script = BashScriptWriter(file, code_builders)
        script.write()


def write_video_script(video: VideoConfig) -> None:
    command_builder = FFmpegGenerateBuilder
    skip_regenerate = bash_code.skip_regenerate_existing_video

    if video.is_combination():
        skip_regenerate = bash_code.concat_video_md5 + skip_regenerate
        command_builder = FFmpegConcatBuilder

    with create_file(video.get_script_path()) as file:
        code_builders = [
            StaticBashCodeBuilder(bash_code.script_beginning),

            BashVariableBuilder(video.get_variables()),
            VideoListVariableBuilder(video),

            StaticBashCodeBuilder(skip_regenerate),

            command_builder(video.get_options()),

            StaticBashCodeBuilder(bash_code.metadata_writer),
            StaticBashCodeBuilder(bash_code.video_script_output)
        ]

        script = BashScriptWriter(file, code_builders)
        script.write()


def write_video_scripts(videos: List[VideoConfig]) -> None:
    for video in videos:
        write_video_script(video)
