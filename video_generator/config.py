import yaml


class Config:
    def __init__(self, yaml_path, export_path):
        self._contents = load_yaml_config(yaml_path)
        self._export_dir = export_path + "/"

    def get_variables(self) -> list:
        return self._contents.get('shared_variables', [])

    def get_options(self) -> list:
        return self._contents.get('shared_options', [])

    def get_videos(self) -> dict:
        return self._contents.get('videos', {})

    def get_option_templates(self) -> dict:
        return self._contents.get('option_templates', {})

    def get_export_path(self) -> str:
        return self._export_dir


class VideoConfig:
    def __init__(self, config_dict):
        self._contents = config_dict

    def get_variables(self) -> dict:
        return self._contents.get('variables', {})

    def get_options(self) -> list:
        return self._contents.get('options', [])

    def get_combine(self) -> list:
        return self._contents.get('combine', [])

    def is_combination(self) -> bool:
        return len(self.get_combine()) > 0

    def get_title(self) -> str:
        return self._contents.get('title')


def load_yaml_config(filename=""):
    with open(filename, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)
