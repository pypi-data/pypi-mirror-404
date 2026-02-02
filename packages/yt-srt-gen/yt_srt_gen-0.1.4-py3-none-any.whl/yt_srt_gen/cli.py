import argparse
import asyncio
import shlex
import sys
from pathlib import Path

import googletrans
from tqdm import tqdm
from whisper.tokenizer import LANGUAGES
from whisper.transcribe import cli as whisper_cli
from yt_dlp import YoutubeDL


def download_video(url: str):
    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
    return video_path


def generate_srt(video_path, lang: str, output_format: str, whisper_args: list[str]):
    srt_filepath = Path(video_path).with_suffix(".srt")
    if srt_filepath.exists():
        print(str(srt_filepath) + " already exists, skipping the step")
    else:
        old_argv = sys.argv.copy()
        try:
            sys.argv = [
                "whisper", video_path,
                "--language", lang,
                "--output_format", output_format,
            ] + whisper_args
            whisper_cli()
        finally:
            sys.argv = old_argv
    return srt_filepath


def has_translation_block(lines):
    """
    Returns True if there are multiple subtitle lines
    after the first timestamp.
    """
    after_timestamp = False
    text_lines = 0

    for line in lines:
        stripped = line.strip()

        if "-->" in stripped:
            after_timestamp = True
            continue

        if after_timestamp:
            if not stripped:
                break  # end of subtitle block

            if not stripped.isdigit():
                text_lines += 1

            if text_lines > 1:
                return True  # already translated

    return False


async def append_english_translation(srt_file: str, source_lang: str, target_lang: str):
    translator = googletrans.Translator()

    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if has_translation_block(lines):
        print("Detected translated subtitles — skipping")
        return

    new_lines = []

    with tqdm(total=len(lines), desc="Translating") as pbar:
        for line in lines:
            stripped = line.strip()
            new_lines.append(line)  # keep original line
            # Only translate lines that are not empty, numbers, or timestamps
            if stripped and not stripped.isdigit() and "-->" not in stripped:
                translated = (await translator.translate(stripped, src=source_lang, dest=target_lang)).text
                new_lines.append(translated + '\n')
            pbar.update(1)

    with open(srt_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def main():
    parser = argparse.ArgumentParser(description="Download YouTube video and generate translated subtitles.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--source-language", "-s", required=True,
                        choices=sorted(LANGUAGES.keys()),
                        help="Language spoken in the audio")
    parser.add_argument("--target-language", "-t", required=True,
                        choices=sorted(googletrans.LANGUAGES.keys()),
                        help="Language for translated subtitles")
    parser.add_argument("--output-format", "-f", default="srt",
                        choices=["txt", "vtt", "srt", "tsv", "json", "all"],
                        help="format of the output file")
    parser.add_argument("--whisper-args", "-w", default="",
                        help="Additional arguments to pass to openai-whisper")
    args = parser.parse_args().__dict__

    print("\n[+] Downloading video...")
    video_path = download_video(args["url"])

    print("\n[+] Generating subtitles...")
    srt_path = generate_srt(video_path, args["source_language"], args["output_format"], shlex.split(args["whisper_args"]))

    print("\n[+] Translating subtitles...")
    asyncio.run(append_english_translation(
        str(srt_path),
        args["source_language"],
        args["target_language"]))

    print(f"[+] Done! Translated subtitles saved as: {srt_path}")
