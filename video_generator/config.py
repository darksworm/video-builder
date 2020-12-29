from typing import List, Dict


class Config:
    def __init__(self, config: dict, export_path):
        self._contents = config
        self._export_dir = self._add_trailing_slash(export_path)

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


class VideoConfigListBuilder:
    def __init__(self, configs: Dict[str, dict]):
        self._configs = configs

    def add_title_and_script_dir(self, script_dir: str) -> 'VideoConfigListBuilder':
        for title, video_config in self._configs.items():
            video_config['title'] = title
            video_config['script_dir'] = script_dir
        return self

    def prepend_variables(self, variables: Dict[str, str]) -> 'VideoConfigListBuilder':
        for _, config in self._configs.items():
            config['variables'] = {**variables, **config.get('variables', {})}
        return self

    def append_variables(self, variables: Dict[str, str]) -> 'VideoConfigListBuilder':
        for _, config in self._configs.items():
            config['variables'] = {**config.get('variables', {}), **variables}
        return self

    def prepend_options(self, options: List[str]) -> 'VideoConfigListBuilder':
        for _, config in self._configs.items():
            config['options'] = [*options, *config.get('options', [])]
        return self

    def replace_variable_references(self) -> 'VideoConfigListBuilder':
        for title, config in self._configs.items():
            for variable_name, variable_contents in config['variables'].items():
                config['variables'][variable_name] = str(variable_contents).replace('{video_title}', title)
        return self

    def build(self) -> List[VideoConfig]:
        return [VideoConfig(config) for _, config in self._configs.items()]

    class _TemplateReplacer:
        @classmethod
        def replace_template_names_with_options(cls, option_list: List[str], templates: Dict[str, str]) -> List[str]:
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

    def replace_template_option_names(self, option_templates: Dict[str, str]) -> 'VideoConfigListBuilder':
        replacer = VideoConfigListBuilder._TemplateReplacer
        for _, config in self._configs.items():
            options = config.get('options', [])
            config['options'] = replacer.replace_template_names_with_options(options, option_templates)
        return self


def create_video_configs_from_global_config(config: Config, append_variables: Dict[str, str]) -> List[VideoConfig]:
    return VideoConfigListBuilder(config.get_videos()) \
        .add_title_and_script_dir(config.get_export_path()) \
        .prepend_variables(config.get_variables()) \
        .append_variables(append_variables) \
        .prepend_options(config.get_options()) \
        .replace_template_option_names(config.get_option_templates()) \
        .replace_variable_references() \
        .build()
