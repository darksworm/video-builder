from typing import List, Dict, final

from bash_writer import bash_code
from config.config import VideoConfig


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
class BashVariableBuilder(BashCodeBuilder):
    def __init__(self, variables: Dict[str, str]):
        self._variables = variables

    def build(self) -> str:
        return ''.join([f'{name}={value}\n' for name, value in self._variables.items()])


@final
class VideoScriptCallBuilder(BashCodeBuilder):
    def __init__(self, videos: List[VideoConfig]):
        self._videos = videos

    @staticmethod
    def _get_video_script_call_code(video: VideoConfig) -> str:
        return f'export {video.get_title()}_length=$(bash {video.get_script_name()})'

    def build(self) -> str:
        videos_code = map(self._get_video_script_call_code, self._videos)
        joined_code = ' && \\\n'.join(videos_code)
        return joined_code


@final
class FFmpegOptionBuilder(BashCodeBuilder):
    def __init__(self, options: List[str]):
        self._options = options

    def _format_option(self, option):
        if type(option) is dict:
            first_key = list(option.keys())[0]
            first_elem = option[first_key]
            return self._format_option(first_elem)
        else:
            return f'\t{option}'

    def build(self):
        return ' \\\n'.join([
            self._format_option(option) for option in self._options
        ])


@final
class FFmpegGenerateBuilder(BashCodeBuilder):
    def __init__(self, options: List[str]):
        self._option_builder = FFmpegOptionBuilder(options)

    def build(self):
        return '\t'.join([
            '\nffmpeg \\\n',
            f'{self._option_builder.build()} \\\n',
            '$output_file 1>/dev/null\n\n'
        ])


@final
class FFmpegConcatBuilder(BashCodeBuilder):
    def __init__(self, options: List[str]):
        self._option_builder = FFmpegOptionBuilder(options)

    def build(self):
        return '\n'.join([
            bash_code.concat_function_1,
            f'{self._option_builder.build()} \\',
            bash_code.concat_function_2,
            '\nconcat_videos ${videos[@]}\n\n'
        ])


@final
class VideoListVariableBuilder(BashCodeBuilder):
    def __init__(self, config: VideoConfig):
        self._config = config

    def _get_video_parts(self):
        if self._config.is_combination():
            return self._config.get_combine()
        return [self._config.get_title()]

    def _get_variable_contents(self):
        titles = [title + '.mp4' for title in self._get_video_parts()]
        return ' '.join(titles)

    def build(self):
        return BashVariableBuilder({
            'videos': f'( {self._get_variable_contents()} )'
        }).build()
