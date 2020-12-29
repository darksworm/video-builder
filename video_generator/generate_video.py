# Multipart video ffmpeg script generation script.
# Uses yaml file (from first arg) to generate multi-section videos in export
# directory (second arg)
#
# example usage
# python generate_video.py prestream.yaml ../export
#
# see usage.md for more info

import os
from sys import exit, argv

import yaml

from bash_code import static_video_variables
from config import Config, create_video_configs_from_global_config
from script_writing import write_video_scripts, write_main_script, create_file


def run_script(path: str, name: str) -> None:
    os.chdir(path)
    os.system('chmod +x *.bash')
    os.system(f'bash {name}')


def validate_arguments(arguments: list) -> None:
    if len(arguments) < 3:
        print('Please pass the config yaml and export path.')
        exit(1)

    if not os.path.exists(arguments[1]):
        print('Passed yaml file does not exist!')
        exit(2)


def load_yaml_config_from_file(filename: str) -> dict:
    with open(filename, 'r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def create_config_from_arguments(arguments: list) -> Config:
    [_, yaml_path, export_path] = arguments
    raw_config = load_yaml_config_from_file(yaml_path)
    return Config(raw_config, export_path)


def main(arguments: list) -> int:
    validate_arguments(arguments)

    config = create_config_from_arguments(arguments)
    video_configs = create_video_configs_from_global_config(config, append_variables=static_video_variables)

    write_video_scripts(video_configs)

    main_script_name = 'generate.bash'
    main_script = create_file(config.get_export_path(), main_script_name)

    write_main_script(main_script, video_configs, config.get_variables())

    run_script(config.get_export_path(), main_script_name)

    return 0


def init():
    if __name__ == "__main__":
        exit(main(argv))


init()
