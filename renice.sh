#!/bin/sh
renice -n -5 $(pgrep nginx)
renice -n -10 $(pgrep ffmpeg)
