from config import VideoConfig
from option_templates import insert_option_templates
from variables import get_static_video_variables


class Video:
    def __init__(self, config):
        self.config = config
        self.script_name = f'export_{config.get_title()}.bash'


def create_videos(config):
    videos = []
    for title, video_config in config.get_videos().items():
        video_config['title'] = title
        video_config = prepare_video_config(video_config, config)
        video = Video(video_config)
        videos.append(video)

    return videos


def prepare_video_config(video_config_dict, global_config):
    video_config = VideoConfig(video_config_dict)

    video_config_dict['variables'] = \
        prepare_video_variables(video_config, global_config)

    video_config_dict['options'] = \
        prepare_video_options(video_config, global_config)

    return VideoConfig(video_config_dict)


def prepare_video_options(video_config, global_config):
    config_dict = \
        [*global_config.get_options(), *video_config.get_options()]

    templates = global_config.get_option_templates()
    return insert_option_templates(config_dict, templates)


def prepare_video_variables(video_config, global_config):
    return {
        **global_config.get_variables(),
        **video_config.get_variables(),
        **get_static_video_variables(video_config.get_title())
    }
