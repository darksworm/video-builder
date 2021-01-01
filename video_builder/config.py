from abc import ABC
from typing import List, Dict, final


class Config:
    def __init__(self, config: dict, export_path: str, script_name: str):
        self._contents = config
        self._export_dir = self._add_trailing_slash(export_path)
        self._script_name = script_name

    @staticmethod
    def _add_trailing_slash(directory: str):
        if '/' != directory[-1:]:
            return directory + '/'
        return directory

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

    def get_script_name(self) -> str:
        return f'export_{self._script_name}.bash'

    def get_script_path(self) -> str:
        return self._export_dir + self.get_script_name()


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

    def get_script_path(self) -> str:
        return self._contents.get('script_dir') + self.get_script_name()


class VideoConfigListPreprocessor:
    def process_one(self, title: str, config: dict) -> dict:
        raise NotImplementedError()

    def process(self, config: Dict[str, dict], video_title: str) -> Dict[str, dict]:
        return self.process_one(video_title, config)


@final
class VideoConfigTitleAdder(VideoConfigListPreprocessor):
    def process_one(self, title: str, config: dict) -> dict:
        return {**config, **{'title': title}}


@final
class VideoConfigScriptDirAdder(VideoConfigListPreprocessor):
    def __init__(self, script_dir: str):
        self._script_dir = script_dir

    def process_one(self, title: str, config: dict) -> dict:
        return {**config, **{'script_dir': self._script_dir}}


class VideoConfigVariablePreprocessor(VideoConfigListPreprocessor, ABC):
    def __init__(self, variables: Dict[str, str]):
        self._variables = variables


@final
class VideoConfigVariableAppender(VideoConfigVariablePreprocessor):
    def process_one(self, title: str, config: dict) -> dict:
        config['variables'] = {**config.get('variables', {}), **self._variables}
        return config


@final
class VideoConfigVariablePrepender(VideoConfigVariablePreprocessor):
    def process_one(self, title: str, config: dict) -> dict:
        config['variables'] = {**self._variables, **config.get('variables', {})}
        return config


@final
class VideoConfigOptionPrepender(VideoConfigListPreprocessor):
    def __init__(self, options: List[str]):
        self._options = options

    def process_one(self, title: str, config: dict) -> dict:
        config['options'] = [*self._options, *config.get('options', [])]
        return config


class VideoConfigReferenceReplacer(VideoConfigListPreprocessor, ABC):
    def __init__(self, reference_map: Dict[str, str]):
        self._reference_map = reference_map


@final
class VideoConfigVariableReferenceReplacer(VideoConfigReferenceReplacer):
    @staticmethod
    def _replace_reference(reference_name: str, reference_value: str, items: dict) -> dict:
        for variable_name, variable_value in items.items():
            items[variable_name] = str(variable_value).replace(reference_name, reference_value)
        return items

    def process_one(self, title: str, config: dict) -> dict:
        for reference_name, reference_value in self._reference_map.items():
            config['variables'] = self._replace_reference(reference_name, reference_value, config['variables'])
        return config


@final
class VideoConfigOptionReferenceReplacer(VideoConfigReferenceReplacer):
    def process_one(self, title: str, config: dict) -> dict:
        config['options'] = self._replace_template_names_with_options(config['options'], self._reference_map)
        return config

    @classmethod
    def _replace_template_names_with_options(cls, option_list: List[str], templates: Dict[str, str]) -> List[str]:
        replaced = []
        for name in option_list:
            options = cls._get_option_or_template_options_list(name, templates)
            replaced = [*replaced, *options]
        return replaced

    @staticmethod
    def _get_template_options_for_template_name(template_name: str, templates: Dict[str, str]) -> List[str]:
        option_text = templates[template_name]
        split_options = option_text.splitlines(keepends=False)
        return split_options

    @classmethod
    def _get_option_or_template_options_list(cls, option: str, templates: Dict[str, str]) -> List[str]:
        if option in templates:
            preset_options = cls._get_template_options_for_template_name(option, templates)
            return preset_options
        else:
            return [option]


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


def get_static_video_config_preprocessors(config: Config) -> List[VideoConfigListPreprocessor]:
    return [
        VideoConfigTitleAdder(),
        VideoConfigScriptDirAdder(config.get_export_path()),
        VideoConfigVariablePrepender(config.get_variables()),
        VideoConfigOptionPrepender(config.get_options()),
        VideoConfigOptionReferenceReplacer(config.get_option_templates())
    ]


def build_video_config(title: str, config: dict, preprocessors: List[VideoConfigListPreprocessor]) -> VideoConfig:
    builder = VideoConfigBuilder(title, config)
    preprocessors = preprocessors + [VideoConfigVariableReferenceReplacer({'{video_title}': title})]
    builder.set_preprocessors(preprocessors)
    return builder.build()


def build_video_configs_from_global_config(config: Config, appendable_variables: Dict[str, str]) -> List[VideoConfig]:
    video_config_dicts = config.get_videos()
    static_preprocessors = get_static_video_config_preprocessors(config)
    static_preprocessors.append(VideoConfigVariableAppender(appendable_variables))

    return [
        build_video_config(video_title, video_config, static_preprocessors)
        for video_title, video_config in video_config_dicts.items()
    ]
