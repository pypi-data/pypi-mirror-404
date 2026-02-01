import argparse
import asyncio
import sys
from pathlib import Path

from googletrans import Translator
from tqdm import tqdm
from whisper.transcribe import cli as whisper_cli
from yt_dlp import YoutubeDL


def download_video(url: str, ydl_format: str):
    with YoutubeDL({'format': ydl_format}) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
    return video_path


def generate_srt(video_path, model: str, device: str, lang: str, output_format: str):
    srt_filepath = Path(video_path).with_suffix(".srt")
    if srt_filepath.exists():
        print(str(srt_filepath) + " already exists, skipping the step")
    else:
        old_argv = sys.argv.copy()
        try:
            sys.argv = [
                "whisper", video_path,
                "--model", model,
                "--device", device,
                "--language", lang,
                "--output_format", output_format,
            ]
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
    translator = Translator()

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
    parser.add_argument("--ydl-format", default="bestvideo+bestaudio/best", help="format for yt-dlp")
    parser.add_argument("--model", default="turbo", help="name of the Whisper model to use")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"],
                        help="Processor to use for OpenAI Whisper to run")
    parser.add_argument("--source-language", default="sr",
                        help="language spoken in the audio, specify None to perform language detection")
    parser.add_argument("--target-language", default="en", help="language for translated subtitles")
    parser.add_argument("--output-format", "-f", default="srt", choices=["txt", "vtt", "srt", "tsv", "json", "all"],
                        help="format of the output file")
    args = parser.parse_args().__dict__

    print("\n[+] Downloading video...")
    video_path = download_video(args["url"], args["ydl_format"])

    print("\n[+] Generating subtitles...")
    srt_path = generate_srt(video_path, args["model"], args["device"], args["source_language"], args["output_format"])

    print("[+] Translating subtitles...")
    asyncio.run(append_english_translation(
        str(srt_path),
        args["source_language"],
        args["target_language"]))

    print(f"[+] Done! Translated subtitles saved as: {srt_path}")
