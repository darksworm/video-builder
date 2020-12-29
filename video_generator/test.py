import os
import shutil
import subprocess
import tempfile
import unittest
from io import StringIO
from typing import Dict

import psutil

from config import VideoConfig, VideoVariableListProvider, StaticVariableListProvider, Config, VideoConfigBuilder, \
    build_video_configs
from generate_video import validate_arguments, load_yaml_config_from_file, main
from script_writing import BashScript, BashCodeBuilder, StaticBashCodeBuilder, write_main_script


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


class TestVideoVariableListProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.config = VideoConfig({})
        self.provider = VideoVariableListProvider()

    def test_base_class_raises_exception_on_get(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get(self.config)


class TestStaticVariableListProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.video_title = "some_bond_flick"
        self.video_config = VideoConfig({'title': self.video_title})

    def provide(self, variable_map: Dict[str, str]):
        provider = StaticVariableListProvider(variable_map)
        return provider.get(self.video_config)

    def test_nothing_replaced_if_no_video_title_in_contents(self):
        variable_map = {
            "filename": "poop.jpg",
            "length": "30"
        }
        self.assertEqual(variable_map, self.provide(variable_map))

    def test_variable_names_not_replaced(self):
        variable_map = {
            "{video_title}": "somethingstatic.mp4",
            "{length}": "30",
            "{}": "30",
        }
        self.assertEqual(variable_map, self.provide(variable_map))

    def test_contents_change_when_video_title_replaced(self):
        variable_map = {
            "filename": "{video_title}.mp4"
        }
        self.assertNotEqual(variable_map, self.provide(variable_map))

    def test_video_title_replaced(self):
        variable_map = {
            "filename": "{video_title}.mp4",
        }
        expected = f'{self.video_title}.mp4'
        provided = self.provide(variable_map)['filename']
        self.assertEqual(expected, provided)


class TestYamlConfigLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        self.file.write("""
        dank_yaml:
          - sometimes
          - mostly
          - always
        """)
        self.file.close()

    def tearDown(self) -> None:
        os.unlink(self.file.name)

    def test_basic_yaml_loads(self):
        contents = load_yaml_config_from_file(self.file.name)
        self.assertEqual({'dank_yaml': ['sometimes', 'mostly', 'always']}, contents)

    def test_file_closed_after_loading(self):
        open_files_before = psutil.Process().open_files()
        load_yaml_config_from_file(self.file.name)
        open_files_after = psutil.Process().open_files()
        self.assertEqual(open_files_before, open_files_after)


class TestVideoConfigBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_video_config = {
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

        self.config = Config({
            'shared_variables': {
                'things': 'aregood',
                'stuff': 'isprettydecent'
            },
            'shared_options': [
                '-loop 1',
                '-shortest'
            ]
        }, 'export')

        self.provider = StaticVariableListProvider({
            "something": "else",
            "and": "somemore",
        })

        self.builder = VideoConfigBuilder(self.raw_video_config, self.config, self.provider)

        self.all_options = [
            *self.raw_video_config['options'],
            *self.config.get_options(),
        ]

        self.all_variables = {
            **self.config.get_variables(),
            **self.raw_video_config['variables'],
            **self.provider.get(VideoConfig(self.raw_video_config))
        }

    def test_all_options_present_in_built_options(self):
        built = self.builder.build()

        for option in self.all_options:
            self.assertIn(option, built.get_options())

        for name, value in self.all_variables.items():
            self.assertEqual(built.get_variables()[name], value)

    def test_provider_overwrites_global_config_variable(self):
        var_name = 'this_variable'
        final_value = "is_good"
        config = Config({
            'shared_variables': {
                var_name: 'isbad'
            }
        }, 'export')
        provider = StaticVariableListProvider({
            var_name: final_value,
        })

        builder = VideoConfigBuilder(self.raw_video_config, config, provider)
        built = builder.build()
        self.assertEqual(final_value, built.get_variables()[var_name])

    def test_provider_overwrites_video_config_variable(self):
        var_name = 'this_variable'
        final_value = "is_good"

        raw_video_config = {
            'title': 'yea',
            'variables': {
                var_name: 'not_good'
            }
        }

        provider = StaticVariableListProvider({
            var_name: final_value,
        })

        builder = VideoConfigBuilder(raw_video_config, self.config, provider)
        built = builder.build()

        self.assertEqual(final_value, built.get_variables()[var_name])

    def test_video_variable_overwrites_global_variable(self):
        var_name = 'this_variable'
        final_value = "is_good"

        raw_video_config = {
            'title': 'yea',
            'variables': {
                var_name: final_value
            }
        }
        config = Config({
            'shared_variables': {
                var_name: 'isbad'
            }
        }, 'export')

        builder = VideoConfigBuilder(raw_video_config, config, self.provider)
        built = builder.build()

        self.assertEqual(final_value, built.get_variables()[var_name])


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
        config_count = len(build_video_configs(self.config, StaticVariableListProvider({})))
        self.assertEqual(video_count, config_count)

    def test_video_title_set(self):
        configs = build_video_configs(self.config, StaticVariableListProvider({}))
        for config in configs:
            self.assertGreater(config.get_title(), "")

    def test_video_titles_present(self):
        configs = build_video_configs(self.config, StaticVariableListProvider({}))
        expected_titles = [key for key, value in self.config.get_videos().items()]
        config_titles = [config.get_title() for config in configs]

        self.assertEqual(expected_titles, config_titles)


class TestBashScript(unittest.TestCase):
    def setUp(self) -> None:
        self.line1 = "#!/bin/bash"
        self.line2 = "set -e -u"

        writers = [
            StaticBashCodeBuilder(self.line1),
            StaticBashCodeBuilder(self.line2),
        ]

        self.mock_file = StringIO()
        self.script = BashScript(self.mock_file, writers)
        self.script.write()

    def tearDown(self) -> None:
        self.script.close_file()

    def test_file_written_to(self):
        self.mock_file.seek(0)
        content = self.mock_file.read()
        self.assertNotEqual('', content)

    def test_file_lines_match_writer_contents(self):
        self.mock_file.seek(0)
        script_content = self.mock_file.read()
        expected_content = f'{self.line1}{self.line2}'
        self.assertEqual(expected_content.replace('\n', ''), script_content.replace('\n', ''))

    def test_script_executes_with_0_exit_code(self):
        self.mock_file.seek(0)
        script_content = self.mock_file.read()
        exit_code = os.system(script_content)
        self.assertEqual(0, exit_code)


class TestBashCodeWriter(unittest.TestCase):
    def test_bash_code_writer_throws_on_write(self):
        writer = BashCodeBuilder()
        with self.assertRaises(NotImplementedError):
            writer.build()


class TestStaticBashCodeBuilder(unittest.TestCase):
    def test_built_code_contains_passed_code(self):
        passed_code = "random_gibberish and such"
        builder = StaticBashCodeBuilder(passed_code)
        self.assertIn(passed_code, builder.build())


class TestWriteMainScript(unittest.TestCase):
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
                    ],
                    'variables': {
                        'testing': 30,
                        'something': 'yes'
                    }
                },
                'video2': {
                    'options': [
                        '-maybe'
                    ],
                    'variables': {
                        'length': 60,
                        'something': 'yes'
                    }
                }
            },
            'option_templates': {
                'something': "-yes -no -maybe"
            }
        }
        self.config = Config(self.raw_config, 'export')
        self.videos = build_video_configs(self.config, StaticVariableListProvider({}))
        self.script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')

        self.video_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.video_script_file.write('#!/bin/bash')
        self.video_script_file.close()

    def tearDown(self) -> None:
        for file in [self.script_file, self.video_script_file]:
            file.close()
            os.unlink(file.name)

    def test_file_closed_after_writing(self):
        write_main_script(self.script_file, self.videos, self.config.get_variables())
        self.assertTrue(self.script_file.closed)

    def write_and_get_contents(self):
        write_main_script(self.script_file, self.videos, self.config.get_variables())
        with open(self.script_file.name, 'r') as file:
            return file.read()

    def test_code_written_to_file(self):
        contents = self.write_and_get_contents()
        self.assertGreater(contents, "")

    def test_video_scripts_present_in_written_code(self):
        contents = self.write_and_get_contents()
        video_scripts = [video.get_script_name() for video in self.videos]
        for video_script in video_scripts:
            self.assertIn(video_script, contents)

    def test_variables_present_in_written_code(self):
        contents = self.write_and_get_contents()
        for name, value in self.config.get_variables().items():
            self.assertIn(name, contents)
            self.assertIn(value, contents)

    def test_written_code_executes_successfully(self):
        contents = self.write_and_get_contents()

        # replace script calls with the temp file
        video_scripts = [video.get_script_name() for video in self.videos]
        for video_script in video_scripts:
            contents = contents.replace(video_script, self.video_script_file.name)

        with open(self.script_file.name, 'w') as file:
            file.write(contents)

        exit_code = os.system(f'bash {self.script_file.name}')
        self.assertEqual(0, exit_code)


class TestWriteMainScriptWithoutVideos(unittest.TestCase):
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
            },
            'option_templates': {
                'something': "-yes -no -maybe"
            }
        }
        self.config = Config(self.raw_config, 'export')
        self.videos = build_video_configs(self.config, StaticVariableListProvider({}))
        self.temporary_file = tempfile.NamedTemporaryFile(delete=False, mode='w')

    def tearDown(self) -> None:
        self.temporary_file.close()
        os.unlink(self.temporary_file.name)

    def test_written_script_executes_successfully(self):
        write_main_script(self.temporary_file, self.videos, self.config.get_variables())
        exit_code = os.system(f'bash {self.temporary_file.name}')
        self.assertEqual(0, exit_code)


class Test3SecondBlankVideoCreated(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = '/tmp/python_test'
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.mkdir(self.temp_dir)

        self.duration = 3

        self.video_name = f'darkness_{self.duration}_sec'

        self.config_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.config_file.write(f"""\
            shared_options:
              - -y
              - -v warning
              - -hide_banner
              - -stats

            shared_variables:
              fps: 24

            option_templates:
              shared_options: |-
                -c:v h264
                -r $fps

            videos:
              {self.video_name}:
                variables:
                  duration: {self.duration}
                options:
                  - -f lavfi
                  - -i color=size=1920x1080:duration=$duration:rate=$fps:color=black
                  - -t $duration
                  - shared_options
        """)
        self.config_file.close()

        self.probe_script = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.probe_script.write(f"""
            ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
            {self.temp_dir}/{self.video_name}.mp4 | cut -d. -f1
        """)
        self.probe_script.close()

    def tearDown(self) -> None:
        self.config_file.close()
        os.unlink(self.config_file.name)
        os.unlink(self.probe_script.name)
        shutil.rmtree(self.temp_dir)

    def test_video_length_matches(self):
        main(['generate_video.py', self.config_file.name, self.temp_dir])
        actual = subprocess.check_output(['/bin/bash', self.probe_script.name])
        actual = actual.decode('UTF-8').rstrip()
        self.assertEqual(str(self.duration), str(actual))


class TestCombineWithBlankVideos(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = '/tmp/python_test'
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.mkdir(self.temp_dir)

        self.video1 = {
            'duration': 2,
            'name': 'video1'
        }
        self.video2 = {
            'duration': 3,
            'name': 'video2'
        }

        self.combine_video_name = 'result'

        self.config_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.config_file.write(f"""\
            shared_options:
              - -y
              - -v warning
              - -hide_banner
              - -stats

            shared_variables:
              fps: 24

            option_templates:
              shared_options: |-
                -f lavfi
                -i color=size=1920x1080:duration=$duration:rate=$fps:color=black
                -f lavfi
                -i anullsrc=channel_layout=stereo:sample_rate=44100
                -t $duration
                -c:v h264
                -r $fps

            videos:
              {self.video1['name']}:
                variables:
                  duration: {self.video1['duration']}
                options:
                  - shared_options

              {self.video2['name']}:
                variables:
                  duration: {self.video2['duration']}
                options:
                  - shared_options

              {self.combine_video_name}:
                combine:
                  - {self.video1['name']}
                  - {self.video2['name']}
        """)
        self.config_file.close()

        self.probe_script = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.probe_script.write(f"""
            ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
            {self.temp_dir}/{self.combine_video_name}.mp4 | cut -d. -f1
        """)
        self.probe_script.close()

    def tearDown(self) -> None:
        self.config_file.close()
        os.unlink(self.config_file.name)
        os.unlink(self.probe_script.name)
        shutil.rmtree(self.temp_dir)

    def test_video_length_matches(self):
        main(['generate_video.py', self.config_file.name, self.temp_dir])
        actual = subprocess.check_output(['/bin/bash', self.probe_script.name])
        actual = actual.decode('UTF-8').rstrip()
        self.assertEqual(str(self.video1['duration'] + self.video2['duration']), str(actual))


if __name__ == '__main__':
    unittest.main()
