# reVidx

[![Python 3.7+](https://img.shields.io/badge/python-black?logo=python)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/ffmpeg-black?logo=FFmpeg&logoColor=green)](https://ffmpeg.org/)

reVidx is a cross-platform CLI tool designed to re-encode video files to AVC (H.264) codec and audio to MP3 for compatibility with legacy devices and players.

Built on top of FFmpeg, it offers a simple, fast interface for batch processing video conversion, subtitle burning, and audio extraction (aac) with a minimal terminal progress bar.

## Table of Contents

- [Requirements](#Requirements)
- [Installation](#Installation)
- [Features](#Features)
- [Usage](#Usage)
- [Notes](#Notes)
- [License](#license)

## Requirements

- [Python](https://www.python.org/)

- [FFmpeg](https://ffmpeg.org/) and [FFprobe](https://ffmpeg.org/ffprobe.html)
Download builds from [here](https://ffmpeg.org/download.html)

    <details>
    <summary>or</summary>

    - On Windows:
        ```bash
        winget install BtbN.FFmpeg.GPL
        ```
        or
        ```bash
        winget install Gyan.FFmpeg
        ```

    - On Termux (android):
        ```bash
        pkg install ffmpeg
        ```

    - On Mac (using Homebrew):
        ```bash
        brew install ffmpeg
        ```

    - On Arch Linux:
        ```bash
        sudo pacman -S ffmpeg
        ```

    - On Ubuntu/Debian:
        ```bash
        sudo apt install ffmpeg
        ```
    </details>


## Installation

- Install reVidx directly via pip:

     ```bash
     pip install revidx
     ```

- Or install from source:

    ```bash
    git clone https://github.com/voidsnax/reVidx.git
    cd reVidx
    pip install -e .
    ```

## Features
- **Video Conversion**: Converts `HEVC` (H.265) to `AVC` (H.264) with proper pixel format and colour range settings for older device compatibility.

- **Audio Conversion**: Encodes audio to  `mp3` (192kbps) for video files.

- **Audio Extraction**: Extracts audio directly to `aac` (128kbps).

- **Subtitle Burning**: Hardcode subtitles into the video track.

- **Progress Bar**: Displays real-time stats including `Size`, `Duration`, `Percentage`, and `Elapsed Time`.

- **Fast Encoding**: Uses `crf` 20 (default) with `veryfast` preset for a balance of speed and quality.

- **Batch Processing**: Process multiple video files sequentially with a single command.

## Usage

```txt
usage: revidx INPUTFILES ... [OPTIONS]

positional arguments:
  inputfiles          Input video files

options:
  -h, --help          show this help message and exit
  -o [PATH/NAME]      Output directory or filename
  -skip               Skip video encoding (copy)
  -burn [INDEX/PATH]  Burn subtitles into the video (default: 0)
  -aindex INDEX       Audio index (default: 0)
  -audio              Extract only audio to AAC
  -crf VALUE          CRF value (default: 20)
```
*Note: You can use ffprobe to get file info*

### Basic Conversion

Convert a video file to `avc/mp3`. The output will be saved as `input-AvcMp3.mp4`.

```bash
revidx inputvideo
```

### Skip Video Encoding

Convert the audio to `mp3` and Keep the original video stream.

```bash
revidx inputvideo -skip
```

### Specify Output Path

Convert a videofile and save it with specific name or convert multiple files and save them to specific folder.

```bash
revidx inputvideo -o ~/Covertedvideo.mp4
```

```bash
revidx inputvideo -o ./ConvertedVideos
```

### Burn Subtitles

Burn the first subtitle track into the video.
```bash
revidx inputvideo -burn
```
Burn a specific subtitle stream from input video.
```bash
revidx inputvideo -burn 2
```
Burn a specific external subtitle file.

```bash
revidx inputvideo -burn pathtosubfile
```

### Extract Audio Only

Extract the audio track to an `aac` file.

```bash
revidx inputvideo -audio
```

### Batch Processing

Convert all `mkv` files in current dir to `avc/mp3`

```bash
revidx *.mkv inputvideo
```

Convert all files in current dir to `avc/mp3`

```bash
revidx ./* inputvideo
```

## Notes

- **Output Extensions**: When using `-o` to specify a filename, ensure it ends with `.mp4` or .`mkv` (video) or `.aac` (audio).
- **Automatic Naming**: If no name is provided, output is saved as `input-AvcMp3.mp4` or `input.aac`.
- **Overwriting**: The tool automatically overwrites existing files without prompting.
- **Subtitles**: Subtitle index start from `0` and ensure proper subtitle formats are passed when `-burn` is provided with external path.
- **Interrupting**: Press `Ctrl+C` to abort the current encoding.
- **File Size**: The tool converts video from `HEVC` (H.265) to `AVC` (H.264). Since `AVC` is less efficient than `HEVC`, the output file size will likely increase to maintain the same visual quality.

## License

MIT License
