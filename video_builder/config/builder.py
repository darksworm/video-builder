from typing import List, Dict

from config.config import Config, VideoConfig
from config.preprocessors import VideoConfigListPreprocessor, VideoConfigVariableReferenceReplacer


class VideoConfigBuilder:
    def __init__(self, video_title: str, config: Dict[str, dict]):
        self._preprocessors = []
        self._config = config
        self._video_title = video_title

    def set_preprocessors(self, preprocessors: List[VideoConfigListPreprocessor]) -> None:
        self._preprocessors = preprocessors

    def _execute_preprocessors(self):
        for preprocessor in self._preprocessors:
            self._config = preprocessor.process(self._config, self._video_title)

    def build(self) -> VideoConfig:
        self._execute_preprocessors()
        return VideoConfig(self._config)


def build_video_config(title: str, config: dict, preprocessors: List[VideoConfigListPreprocessor]) -> VideoConfig:
    builder = VideoConfigBuilder(title, config)
    preprocessors = [
        *preprocessors,
        VideoConfigVariableReferenceReplacer({'{video_title}': title})
    ]
    builder.set_preprocessors(preprocessors)
    return builder.build()


def build_video_configs_from_config(config: Config, preprocessors: List[VideoConfigListPreprocessor]) -> List[
    VideoConfig]:
    return [
        build_video_config(video_title, video_config, preprocessors)
        for video_title, video_config in config.get_videos().items()
    ]
