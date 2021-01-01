from abc import ABC
from typing import List, Dict, final


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
        if config.get('variables', False):
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
