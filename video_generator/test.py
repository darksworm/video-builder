import unittest
from unittest import mock

from config import VideoConfig, Config, \
    create_video_configs_from_global_config
from generate_video import validate_arguments


class TestMainExecuted(unittest.TestCase):
    def test_main_executed(self):
        import generate_video
        with mock.patch.object(generate_video, "main", return_value=42):
            with mock.patch.object(generate_video, "__name__", "__main__"):
                with mock.patch.object(generate_video, 'exit') as mock_exit:
                    generate_video.init()
                    self.assertEqual(42, mock_exit.call_args[0][0])


class TestValidateArguments(unittest.TestCase):
    def test_validate_arguments_exits_on_less_than_3_args(self):
        fail_cases = [[1, 2], [1], []]

        for fail_case in fail_cases:
            with self.assertRaises(SystemExit):
                validate_arguments(fail_case)

    def test_validate_arguments_exits_on_nonexistant_file(self):
        with self.assertRaises(SystemExit):
            validate_arguments(["something!!!", "", ""])


class TextEmptyVideoConfigClass(unittest.TestCase):
    def setUp(self) -> None:
        self.title = "things"
        self.video = VideoConfig({"title": self.title})

    def test_video_initializes_script_name(self):
        self.assertIn(self.title, self.video.get_script_name())

    def test_video_script_name_longer_than_title(self):
        self.assertLess(len(self.title), len(self.video.get_script_name()))

    def test_video_script_name_has_dot(self):
        self.assertIn('.', self.video.get_script_name())

    def test_get_title_gets_title(self):
        self.assertEqual(self.title, self.video.get_title())

    def test_video_script_name_dot_is_not_trailing(self):
        self.assertNotEqual('.', self.video.get_script_name()[-1])

    def test_get_options_returns_empty_array_if_key_doesnt_exist(self):
        self.assertEqual([], self.video.get_options())

    def test_get_combine_returns_empty_array_if_key_doesnt_exist(self):
        self.assertEqual([], self.video.get_combine())

    def test_get_variables_returns_empty_dict_if_key_doesnt_exist(self):
        self.assertEqual({}, self.video.get_variables())

    def test_is_combination_false_if_combine_nonexistant(self):
        self.assertFalse(self.video.is_combination())


class TestPopulatedVideoConfigClass(unittest.TestCase):
    def setUp(self):
        self.raw_config = {
            'title': 'test',
            'variables': {
                'length': '30',
                'file': 'dankmemes.jpg'
            },
            'options': [
                '-y',
                '-i $file'
            ],
            'combine': [
                'video.mp4',
                'other_video.mp4'
            ]
        }
        self.config = VideoConfig(self.raw_config)

    def test_variables_returned_from_map(self):
        self.assertEqual(self.raw_config['variables'], self.config.get_variables())

    def test_options_returned_from_map(self):
        self.assertEqual(self.raw_config['options'], self.config.get_options())

    def test_combine_returned_from_map(self):
        self.assertEqual(self.raw_config['combine'], self.config.get_combine())

    def test_title_returned_from_map(self):
        self.assertEqual(self.raw_config['title'], self.config.get_title())


class TestEmptyConfig(unittest.TestCase):

    def test_export_dir_ends_with_slash(self):
        config = Config({}, 'export')
        self.assertEqual('/', config.get_export_path()[-1])

    def test_export_dir_doesnt_end_with_two_slashes(self):
        config = Config({}, 'export/')
        self.assertNotEqual('//', config.get_export_path()[-2:])

    def test_passed_export_path_part_of_get_export_path(self):
        name = 'export'
        config = Config({}, name)
        self.assertIn(name, config.get_export_path())

    def test_get_options_returns_empty_list_if_none_provided(self):
        config = Config({}, 'export')
        self.assertEqual([], config.get_options())

    def test_get_variables_returns_empty_dict_if_none_provided(self):
        config = Config({}, 'export')
        self.assertEqual({}, config.get_variables())

    def test_get_option_templates_returns_empty_dict_if_none_provided(self):
        config = Config({}, 'export')
        self.assertEqual({}, config.get_option_templates())

    def test_get_videos_returns_empty_dict_if_none_provided(self):
        config = Config({}, 'export')
        self.assertEqual({}, config.get_videos())


class TestPopulatedConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_config = {
            'shared_variables': {
                'var1': 'val1',
                'var2': 'val2',
                'var3': 'val3',
            },
            'shared_options': [
                '-yes',
                '-something'
            ],
            'videos': {
                'video1': {
                    'options': [
                        '-no',
                        'something'
                    ]
                },
                'video2': {
                    'options': [
                        '-maybe'
                    ]
                }
            },
            'option_templates': {
                'something': "-yes -no -maybe"
            }
        }
        self.config = Config(self.raw_config, 'export')

    def test_get_variables_returns_shared_variables(self):
        expected = self.raw_config['shared_variables']
        actual = self.config.get_variables()
        self.assertEqual(expected, actual)

    def test_get_options_returns_shared_options(self):
        expected = self.raw_config['shared_options']
        actual = self.config.get_options()
        self.assertEqual(expected, actual)

    def test_get_videos_returns_shared_videos(self):
        expected = self.raw_config['videos']
        actual = self.config.get_videos()
        self.assertEqual(expected, actual)

    def test_get_option_templates_returns_option_templates(self):
        expected = self.raw_config['option_templates']
        actual = self.config.get_option_templates()
        self.assertEqual(expected, actual)


class TestBuildVideoConfigs(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_config = {
            'shared_variables': {
                'var1': 'val1',
                'var2': 'val2',
                'var3': 'val3',
            },
            'shared_options': [
                '-yes',
                '-something'
            ],
            'videos': {
                'video1': {
                    'options': [
                        '-no',
                        'something'
                    ]
                },
                'video2': {
                    'options': [
                        '-maybe'
                    ]
                }
            },
            'option_templates': {
                'something': "-yes -no -maybe"
            }
        }
        self.config = Config(self.raw_config, 'export')

    def test_returned_video_count_matches_config(self):
        video_count = len(self.config.get_videos())
        config_count = len(create_video_configs_from_global_config(self.config, {}))
        self.assertEqual(video_count, config_count)

    def test_video_title_set(self):
        configs = create_video_configs_from_global_config(self.config, {})
        for config in configs:
            self.assertGreater(config.get_title(), "")

    def test_video_titles_present(self):
        configs = create_video_configs_from_global_config(self.config, {})
        expected_titles = [key for key, value in self.config.get_videos().items()]
        config_titles = [config.get_title() for config in configs]

        self.assertEqual(expected_titles, config_titles)

    def test_video_script_path_set(self):
        configs = create_video_configs_from_global_config(self.config, {})
        for config in configs:
            self.assertNotEqual("", config.get_script_path())

    def test_video_script_path_contains_name(self):
        configs = create_video_configs_from_global_config(self.config, {})
        for config in configs:
            self.assertIn(config.get_script_name(), config.get_script_path())

    def test_video_script_path_contains_export_path(self):
        configs = create_video_configs_from_global_config(self.config, {})
        for config in configs:
            self.assertIn(self.config.get_export_path(), config.get_script_path())

    def test_video_script_path_contains_slash(self):
        configs = create_video_configs_from_global_config(self.config, {})
        for config in configs:
            self.assertIn('/', config.get_script_path())


if __name__ == '__main__':
    unittest.main()
