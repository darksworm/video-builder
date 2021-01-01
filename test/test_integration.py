import os
import shutil
import subprocess
import tempfile
import unittest
from io import StringIO

import psutil

from bash_writer.builders import BashCodeBuilder
from builder import load_yaml_config_from_file, build_videos, get_static_video_config_preprocessors
from config.builder import build_video_configs_from_config
from config.config import Config
from bash_writer.writers import StaticBashCodeBuilder, BashScriptWriter, write_main_script


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


class TestBashScript(unittest.TestCase):
    def setUp(self) -> None:
        self.line1 = "#!/bin/bash"
        self.line2 = "set -e -u"

        writers = [
            StaticBashCodeBuilder(self.line1),
            StaticBashCodeBuilder(self.line2),
        ]

        self.mock_file = StringIO()
        self.script = BashScriptWriter(self.mock_file, writers)
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
        self.script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.config = Config(self.raw_config, '', self.script_file.name)
        self.videos = build_video_configs_from_config(self.config, get_static_video_config_preprocessors(self.config))

        self.video_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.video_script_file.write('#!/bin/bash')
        self.video_script_file.close()

    def tearDown(self) -> None:
        for file in [self.script_file, self.video_script_file]:
            file.close()
            os.unlink(file.name)

    def write_and_get_contents(self):
        write_main_script(self.config, self.videos)
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
        self.temporary_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.config = Config(self.raw_config, '', self.temporary_file.name)
        self.videos = build_video_configs_from_config(self.config, get_static_video_config_preprocessors(self.config))

    def tearDown(self) -> None:
        self.temporary_file.close()
        os.unlink(self.temporary_file.name)

    def test_written_script_executes_successfully(self):
        write_main_script(self.config, self.videos)
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
        build_videos(self.config_file.name, self.temp_dir)
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
        build_videos(self.config_file.name, self.temp_dir)
        actual = subprocess.check_output(['/bin/bash', self.probe_script.name])
        actual = actual.decode('UTF-8').rstrip()
        self.assertEqual(str(self.video1['duration'] + self.video2['duration']), str(actual))


if __name__ == '__main__':
    unittest.main()
