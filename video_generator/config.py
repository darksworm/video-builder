from typing import List, Dict, final

from option_templates import replace_template_option_names_with_template_options


class Config:
    def __init__(self, config: dict, export_path):
        self._contents = config
        self._export_dir = export_path + "/"

    def get_variables(self) -> Dict[str, str]:
        return self._contents.get('shared_variables', {})

    def get_options(self) -> List[str]:
        return self._contents.get('shared_options', [])

    def get_videos(self) -> Dict[str, dict]:
        return self._contents.get('videos', {})

    def get_option_templates(self) -> dict:
        return self._contents.get('option_templates', {})

    def get_export_path(self) -> str:
        return self._export_dir


class VideoConfig:
    def __init__(self, config_dict):
        self._contents = config_dict

    def get_variables(self) -> Dict[str, str]:
        return self._contents.get('variables', {})

    def get_options(self) -> List[str]:
        return self._contents.get('options', [])

    def get_combine(self) -> List[str]:
        return self._contents.get('combine', [])

    def is_combination(self) -> bool:
        return len(self.get_combine()) > 0

    def get_title(self) -> str:
        return self._contents.get('title')

    def get_script_name(self) -> str:
        return f'export_{self.get_title()}.bash'

    def __eq__(self, other):
        return other._contents == self._contents


class VideoVariableListProvider:
    def get(self, video_config: VideoConfig) -> Dict[str, str]:
        raise NotImplementedError()


@final
class StaticVariableListProvider(VideoVariableListProvider):
    def __init__(self, variable_map: Dict[str, str]):
        self.variable_map = variable_map

    def get(self, video_config: VideoConfig):
        replaced_map = {}
        title = video_config.get_title()
        for variable_name, variable_contents in self.variable_map.items():
            replaced_map[variable_name] = variable_contents.replace('{video_title}', title)

        return replaced_map


class VideoConfigBuilder:
    def __init__(self, raw_video_config: dict, config: Config, variable_provider: VideoVariableListProvider):
        self.config = config
        self.raw_config = raw_video_config
        self.video_config = VideoConfig(self.raw_config)
        self.variable_provider = variable_provider

    def build(self) -> VideoConfig:
        self.raw_config['variables'] = self._build_variables()
        self.raw_config['options'] = self._build_options()

        return VideoConfig(self.raw_config)

    def _build_options(self) -> List[str]:
        config_dict = [
            *self.config.get_options(),
            *self.video_config.get_options()
        ]
        templates = self.config.get_option_templates()

        return replace_template_option_names_with_template_options(config_dict, templates)

    def _build_variables(self) -> Dict[str, str]:
        return {
            **self.config.get_variables(),
            **self.video_config.get_variables(),
            **self.variable_provider.get(self.video_config)
        }


def build_video_configs(config: Config, variable_provider: VideoVariableListProvider) -> List[VideoConfig]:
    video_configs = []
    for title, video_config in config.get_videos().items():
        video_config['title'] = title
        builder = VideoConfigBuilder(video_config, config, variable_provider)
        video_configs.append(builder.build())

    return video_configs
