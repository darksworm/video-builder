# Multipart video ffmpeg script generation script.
# Uses yaml file (from first arg) to generate multi-section videos in export
# directory (second arg)
#
# example usage
# python generate_video.py prestream.yaml ../export
#
# see usage.md for more info

import os
import sys

from config import Config
from script_writing import write_video_scripts, write_main_script
from video import create_videos


def run_main_script(config: Config):
    os.chdir(config.get_export_path())
    os.system('chmod +x *.bash')
    os.system('bash generate.bash')


def validate_arguments(arguments: list):
    if len(arguments) < 3:
        print('Please pass the config yaml and export path.')
        sys.exit(1)

    if not os.path.exists(arguments[1]):
        print('Passed yaml file does not exist!')
        sys.exit(2)


def create_config_from_arguments(arguments: list):
    yaml_path = arguments[1]
    export_path = arguments[2]
    return Config(yaml_path, export_path)


def main(arguments: list):
    validate_arguments(arguments)

    config = create_config_from_arguments(arguments)
    videos = create_videos(config)

    write_video_scripts(videos, config)
    write_main_script(videos, config)

    run_main_script(config)


if __name__ == "__main__":
    main(sys.argv)
