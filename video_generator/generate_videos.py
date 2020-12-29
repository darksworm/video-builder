# Multipart video ffmpeg script generation script.
# Uses yaml file (from first arg) to generate multi-section videos in export
# directory (second arg)
#
# example usage
# python generate_video.py prestream.yaml ../export
#
# see usage.md for more info

import os
from sys import argv

import yaml

from bash_code import static_video_variables
from config import Config, create_video_configs_from_global_config
from script_writing import write_video_scripts, write_main_script


def generate_videos(yaml_file_path: str, export_path: str) -> int:
    config = create_config(yaml_file_path, export_path, main_script_name='generate.bash')
    generate_scripts(config)
    return run_script(config.get_export_path(), config.get_script_name())


def generate_scripts(config: Config) -> None:
    video_configs = create_video_configs_from_global_config(config, append_variables=static_video_variables)
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


def generate_videos_from_cli(arguments: list) -> int:
    [_, yaml_file_path, export_path] = arguments
    return generate_videos(yaml_file_path, export_path)


def are_cli_arguments_valid(arguments: list) -> bool:
    if len(arguments) < 3:
        print('Please pass the config yaml and export path.')
        return False

    if not os.path.exists(arguments[1]):
        print('Passed yaml file does not exist!')
        return False

    return True


def init():
    if __name__ == "__main__":
        exit(1 if not are_cli_arguments_valid(argv) else generate_videos_from_cli(argv))


init()
