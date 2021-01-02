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

from builder import build_videos


def build_videos_from_cli(arguments: list) -> int:
    [_, yaml_file_path, export_path] = arguments
    return build_videos(yaml_file_path, export_path)


def are_cli_arguments_valid(arguments: list) -> bool:
    if len(arguments) < 3:
        print('Please pass the config yaml and export path.')
        return False

    if not os.path.exists(arguments[1]):
        print('Passed yaml file does not exist!')
        return False

    if not os.path.exists(arguments[2]):
        print('Passed export directory does not exist!')
        return False

    return True


def init():
    if __name__ == "__main__":
        exit(build_videos_from_cli(argv) if are_cli_arguments_valid(argv) else 1)


init()
