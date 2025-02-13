# -*- coding: utf-8 -*-
"""newsubtitles.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N7h7pd4-HWwoq4-7VZbSEYCkVP36qyMW
"""

import os

##mp4videoURL = "https://github.com/ramsrigouthamg/Supertranslate.ai/raw/main/Descript_like_wordhighlights_subtitles/Intro.mp4"
videofilename = "ffinal.mp4"
print (videofilename)

!pip install ffmpeg-python==0.2.0

import ffmpeg

audiofilename ="audiosub.mp3"

# Create the ffmpeg input stream
input_stream = ffmpeg.input(videofilename)

# Extract the audio stream from the input stream
audio = input_stream.audio

# Save the audio stream as an MP3 file
output_stream = ffmpeg.output(audio, audiofilename)

# Overwrite output file if it already exists
output_stream = ffmpeg.overwrite_output(output_stream)

ffmpeg.run(output_stream)

print (audiofilename)

!pip install faster-whisper==0.7.0

from faster_whisper import WhisperModel

model_size = "medium"
model = WhisperModel(model_size)

segments, info = model.transcribe(audiofilename, word_timestamps=True)
segments = list(segments)  # The transcription will actually run here.
for segment in segments:
    for word in segment.words:
        print("[%.2fs -> %.2fs] %s" % (word.start, word.end, word.word))

wordlevel_info = []

for segment in segments:
    for word in segment.words:
      wordlevel_info.append({'word':word.word,'start':word.start,'end':word.end})

import json
with open('data1.json', 'w') as f:
    json.dump(wordlevel_info, f,indent=4)

import json

with open('data1.json', 'r') as f:
    wordlevel_info_modified = json.load(f)

def split_text_into_lines(data):

    MaxChars = 30
    #maxduration in seconds
    MaxDuration = 2.5
    #Split if nothing is spoken (gap) for these many seconds
    MaxGap = 1.5

    subtitles = []
    line = []
    line_duration = 0
    line_chars = 0


    for idx,word_data in enumerate(data):
        word = word_data["word"]
        start = word_data["start"]
        end = word_data["end"]

        line.append(word_data)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)


        # Check if adding a new word exceeds the maximum character count or duration
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration
        chars_exceeded = new_line_chars > MaxChars
        if idx>0:
          gap = word_data['start'] - data[idx-1]['end']
          # print (word,start,end,gap)
          maxgap_exceeded = gap > MaxGap
        else:
          maxgap_exceeded = False


        if duration_exceeded or chars_exceeded or maxgap_exceeded:
            if line:
                subtitle_line = {
                    "word": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "textcontents": line
                }
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0
                line_chars = 0


    if line:
        subtitle_line = {
            "word": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "textcontents": line
        }
        subtitles.append(subtitle_line)

    return subtitles
linelevel_subtitles = split_text_into_lines(wordlevel_info_modified)

for line in linelevel_subtitles:
  json_str = json.dumps(line, indent=4)

!pip install moviepy==2.0.0.dev2
!pip install imageio==2.25.1

!apt install imagemagick

!cat /etc/ImageMagick-6/policy.xml | sed 's/none/read,write/g'> /etc/ImageMagick-6/policy.xml

from moviepy.editor import TextClip, CompositeVideoClip, ColorClip
import numpy as np


def create_caption(textJSON, framesize,font = "Helvetica",color='white', highlight_color='yellow',stroke_color='black',stroke_width=1.5):
    wordcount = len(textJSON['textcontents'])
    full_duration = textJSON['end']-textJSON['start']

    word_clips = []
    xy_textclips_positions =[]

    x_pos = 0
    y_pos = 0
    line_width = 0  # Total width of words in the current line
    frame_width = framesize[0]
    frame_height = framesize[1]

    x_buffer = frame_width*1/10

    max_line_width = frame_width - 2 * (x_buffer)

    fontsize = int(frame_height * 0.075) #7.5 percent of video height

    space_width = ""
    space_height = ""

    for index,wordJSON in enumerate(textJSON['textcontents']):
      duration = wordJSON['end']-wordJSON['start']
      word_clip = TextClip(wordJSON['word'], font = font,fontsize=fontsize, color=color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
      word_clip_space = TextClip(" ", font = font,fontsize=fontsize, color=color).set_start(textJSON['start']).set_duration(full_duration)
      word_width, word_height = word_clip.size
      space_width,space_height = word_clip_space.size
      if line_width + word_width+ space_width <= max_line_width:
            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width, y_pos))

            x_pos = x_pos + word_width+ space_width
            line_width = line_width+ word_width + space_width
      else:
            # Move to the next line
            x_pos = 0
            y_pos = y_pos+ word_height+10
            line_width = word_width + space_width

            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width , y_pos))
            x_pos = word_width + space_width


      word_clips.append(word_clip)
      word_clips.append(word_clip_space)


    for highlight_word in xy_textclips_positions:

      word_clip_highlight = TextClip(highlight_word['word'], font = font,fontsize=fontsize, color=highlight_color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(highlight_word['start']).set_duration(highlight_word['duration'])
      word_clip_highlight = word_clip_highlight.set_position((highlight_word['x_pos'], highlight_word['y_pos']))
      word_clips.append(word_clip_highlight)

    return word_clips,xy_textclips_positions

from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips,VideoFileClip, ColorClip
input_video = VideoFileClip(videofilename)
frame_size = input_video.size

all_linelevel_splits=[]

for line in linelevel_subtitles:
  out_clips,positions = create_caption(line,frame_size)

  max_width = 0
  max_height = 0

  for position in positions:
    # print (out_clip.pos)
    # break
    x_pos, y_pos = position['x_pos'],position['y_pos']
    width, height = position['width'],position['height']

    max_width = max(max_width, x_pos + width)
    max_height = max(max_height, y_pos + height)

  color_clip = ColorClip(size=(int(max_width*1.1), int(max_height*1.1)),
                       color=(64, 64, 64))
  color_clip = color_clip.set_opacity(.6)
  color_clip = color_clip.set_start(line['start']).set_duration(line['end']-line['start'])

  # centered_clips = [each.set_position('center') for each in out_clips]

  clip_to_overlay = CompositeVideoClip([color_clip]+ out_clips)
  clip_to_overlay = clip_to_overlay.set_position("bottom")


  all_linelevel_splits.append(clip_to_overlay)

input_video_duration = input_video.duration


final_video = CompositeVideoClip([input_video] + all_linelevel_splits)

# Set the audio of the final video to be the same as the input video
final_video = final_video.set_audio(input_video.audio)

# Save the final clip as a video file with the audio included
final_video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

### make sure that CUDA is available in Edit -> Nootbook settings -> GPU
!nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

# Commented out IPython magic to ensure Python compatibility.
!update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python3.8 2
!update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python3.9 1
!sudo apt install python3.8

!sudo apt-get install python3.8-distutils

!python --version

!apt-get update

!apt install software-properties-common

!sudo dpkg --remove --force-remove-reinstreq python3-pip python3-setuptools python3-wheel

!apt-get install python3-pip

print('Git clone project and install requirements...')
!git clone https://github.com/Winfredy/SadTalker &> /dev/null
# %cd SadTalker
!export PYTHONPATH=/content/SadTalker:$PYTHONPATH
!python3.8 -m pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
!apt update
!apt install ffmpeg &> /dev/null
!python3.8 -m pip install -r requirements.txt

print('Download pre-trained models...')
!rm -rf checkpoints
!bash scripts/download_models.sh

# borrow from makeittalk
import ipywidgets as widgets
import glob
import matplotlib.pyplot as plt
print("Choose the image name to animate: (saved in folder 'examples/')")
img_list = glob.glob1('/content/SadTalker/examples/source_image/', '*.png')
img_list.sort()
img_list = [item.split('.')[0] for item in img_list]
default_head_name = widgets.Dropdown(options=img_list, value='full3')
def on_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        plt.imshow(plt.imread('/content/SadTalker/examples/source_image/art_0.png'.format(default_head_name.value)))
        plt.axis('off')
        plt.show()
default_head_name.observe(on_change)
display(default_head_name)
plt.imshow(plt.imread('/content/SadTalker/examples/source_image/art_0.png'.format(default_head_name.value)))
plt.axis('off')
plt.show()

pip install moviepy

from moviepy.editor import VideoFileClip

# Load the MP4 video file
video_path = '/content/output.mp4'
video_clip = VideoFileClip(video_path)

# Extract the audio
audio_clip = video_clip.audio

# Define the output WAV file path
output_wav_path = 'output_audio.wav'

# Save the audio as a WAV file
audio_clip.write_audiofile(output_wav_path, codec="pcm_s16le")

# Close the video and audio clips
video_clip.close()
audio_clip.close()

# selected audio from exmaple/driven_audio
img = '/content/SadTalker/examples/source_image/art_0.png'.format(default_head_name.value)
print(img)
!python3.8 inference.py --driven_audio ./output_audio.wav \
           --source_image {img} \
           --result_dir ./results

# visualize code from makeittalk
from IPython.display import HTML
from base64 import b64encode
import os, sys

# get the last from results

results = sorted(os.listdir('./results/'))

mp4_name = glob.glob('./results/*.mp4')[0]

mp4 = open('{}'.format(mp4_name),'rb').read()
data_url = "data:video/mp4;base64," + b64encode(mp4).decode()

print('Display animation: {}'.format(mp4_name), file=sys.stderr)
display(HTML("""
  <video width=256 controls>
        <source src="%s" type="video/mp4">
  </video>
  """ % data_url))

from moviepy.editor import VideoFileClip

# Input and output file paths
input_video_file = "/content/SadTalker/results/2023_12_12_06.41.45/temp_art_0##output_audio.mp4"
output_video_file = "output_no_audio.mp4"

# Load the video clip
video_clip = VideoFileClip(input_video_file)

# Set the audio to None to remove it
video_clip = video_clip.set_audio(None)

# Write the video clip without audio
video_clip.write_videofile(output_video_file, codec="libx264")

print(f"Audio removed: {input_video_file} -> {output_video_file}")

from moviepy.editor import *
clip2=VideoFileClip('/content/ffinal3.mp4')
clip1=VideoFileClip('output_no_audio.mp4')
fc=clips_array([[clip1,clip2]])
fc.write_videofile("result1.mp4")