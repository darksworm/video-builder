from typing import List, Dict


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
