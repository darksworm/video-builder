concat_function_1 = """\
# combine all files from arguments with ffmpeg using filter_complex and map
function concat_videos() {
  videos=("$@")

  lim=`expr ${#videos[@]} - 1`
  filter_complex=""

  for i in `seq 0 $lim`; do
      filter_complex="$filter_complex[$i:v][$i:a]"
  done

  ffmpeg \\
    -y \\
    ${videos[@]/#/-i } \\
    -filter_complex "${filter_complex}concat=n=${#videos[@]}:v=1:a=1[a][v]" \\
    -map "[v]" \\
    -map "[a]" \\
"""
concat_function_2 = """\
    $output_file
}
"""

script_return_command = """\
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $output_file | cut -d. -f1\
"""

skip_regenerate_existing_video = f"""\
# if the md5 stored in the video file matches this scripts md5, there is no
# need to regenerate the video as it is up to date.
if [ -f "$output_file" ] && [ "$script_md5" = "$video_md5" ]; then
    >&2 echo "$output_file already up to date, skipping it!"
    {script_return_command}
    exit 1
fi
>&2 echo "Generating $output_file..."
"""

concat_video_md5 = """\
# for concatenated videos, generate the script hash from the combination of all
# consumed video scripts
for video in "${videos[@]}"
do
    dir=$(dirname $script_path)
    name=export_$(echo $video | cut -d"." -f1 | xargs).bash
    script_md5=${script_md5}$(md5sum $dir/$name | cut -d" " -f1)
done
script_md5=$(echo $script_md5 | md5sum | cut -d" " -f1)
"""

static_video_variables = {
    'video_title': '{video_title}',
    'output_file': '$video_title.mp4',
    'script_path': '$(readlink --canonicalize-existing "$0")',
    'script_md5': '$(md5sum $script_path | cut -d" " -f1)',
    'video_md5': '$(exiftool $output_file | grep Artist | cut -d":" -f2 | xargs)'
}
