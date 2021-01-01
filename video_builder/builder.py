import os
from typing import List

import yaml

from bash_code import static_video_variables
from config.builder import build_video_configs_from_config
from config.config import Config
from config.preprocessors import VideoConfigListPreprocessor, VideoConfigOptionReferenceReplacer, \
    VideoConfigOptionPrepender, VideoConfigVariablePrepender, VideoConfigScriptDirAdder, VideoConfigTitleAdder, \
    VideoConfigVariableAppender
from script_writing import write_video_scripts, write_main_script


def build_videos(yaml_file_path: str, export_path: str) -> int:
    config = create_config(yaml_file_path, export_path, main_script_name='generate.bash')
    generate_scripts(config)
    return run_script(config.get_export_path(), config.get_script_name())


def get_static_video_config_preprocessors(config: Config) -> List[VideoConfigListPreprocessor]:
    return [
        VideoConfigTitleAdder(),
        VideoConfigScriptDirAdder(config.get_export_path()),
        VideoConfigVariablePrepender(config.get_variables()),
        VideoConfigVariableAppender(static_video_variables),
        VideoConfigOptionPrepender(config.get_options()),
        VideoConfigOptionReferenceReplacer(config.get_option_templates()),
    ]


def generate_scripts(config: Config) -> None:
    preprocessors = get_static_video_config_preprocessors(config)
    video_configs = build_video_configs_from_config(config, preprocessors)
    write_video_scripts(video_configs)
    write_main_script(config.get_script_path(), video_configs, config.get_variables())


def create_config(yaml_file_path: str, export_path: str, main_script_name: str) -> Config:
    raw_config = load_yaml_config_from_file(yaml_file_path)
    return Config(raw_config, export_path, main_script_name)


def load_yaml_config_from_file(filename: str) -> dict:
    with open(filename, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def run_script(path: str, name: str) -> int:
    os.chdir(path)
    os.system('chmod +x *.bash')
    return os.system(f'bash {name}')
