# yt-srt-gen

`yt-srt-gen` is a Python tool for downloading YouTube videos, generating subtitles using OpenAI Whisper, and translating them into another language (e.g., English) automatically.

## Features

* Download YouTube videos using `yt-dlp`.
* Generate subtitles with OpenAI Whisper.
* Translate subtitles to a target language using `googletrans`.
* Supports multiple subtitle formats: `srt`, `vtt`, `txt`, `tsv`, `json`.

## Installation

You can install `yt-srt-gen` via `pip`:

```bash
pip install git+https://github.com/fertkir/yt-srt-gen.git
```

Or clone the repository and install manually:

```bash
git clone https://github.com/fertkir/yt-srt-gen.git
cd yt-srt-gen
pip install .
```

## Usage

```bash
yt-srt-gen <YouTube URL> [OPTIONS]
```

### Arguments

* `<YouTube URL>`: URL of the YouTube video.

### Options

* `--ydl-format`: Format for `yt-dlp` (default: `bestvideo+bestaudio/best`).
* `--model`: Whisper model to use (default: `turbo`).
* `--device`: Device for Whisper (`cpu` or `cuda`, default: `cpu`).
* `--source-language`: Language spoken in the audio (default: `sr`).
* `--target-language`: Language for translated subtitles (default: `en`).
* `--output-format`, `-f`: Subtitle output format (`txt`, `vtt`, `srt`, `tsv`, `json`, `all`, default: `srt`).

### Example

```bash
yt-srt-gen https://www.youtube.com/watch?v=dQw4w9WgXcQ --source-language es --target-language en --output-format srt
```

This will download the video, generate Spanish subtitles, and append English translations.

## Dependencies

* `yt-dlp` - for downloading YouTube videos.
* `openai-whisper` - for automatic subtitle generation.
* `googletrans` - for translating subtitles.
* `tqdm` - for showing progress bars.

## License

This project is licensed under the GPL-3.0-or-later license.

## Author

Kirill Fertikov — [kirill.fertikov@gmail.com](mailto:kirill.fertikov@gmail.com)
