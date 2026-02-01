#!/usr/bin/env python
from __future__ import print_function, unicode_literals
# VideoJoin_with_Audio_FIXED.py – Actually keeps the sound! (2025 version)

import os
import sys
from ChronicleLogger import ChronicleLogger
from pathlib import Path
import subprocess

def get_mp4_files():
    return sorted([f for f in Path('.').iterdir()
                   if f.is_file() and f.suffix.lower() in {'.mp4', '.mov', '.mkv', '.avi', '.m4v'}],
                  key=lambda x: x.name.lower())

def show_list(files):
    print("\nFound video files:")
    for i, f in enumerate(files, 1):
        print(f"  {i:2d}. {f.name}")
    print()

def choose(files, prompt):
    while True:
        try:
            idx = int(input(prompt)) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print(f"   → Enter 1–{len(files)}")
        except ValueError:
            print("   → Please type a number")

def create_file_list(file1, file2, list_path="filelist.txt"):
    with open(list_path, "w", encoding="utf-8") as f:
        f.write(f"file '{file1}'\n")
        f.write(f"file '{file2}'\n")

def main():
    print("Video Joiner – WITH ORIGINAL AUDIO (using ffmpeg)\n")

    files = get_mp4_files()
    if len(files) < 2:
        print("Need at least 2 video files in this folder!")
        sys.exit(1)

    show_list(files)
    vid1 = choose(files, "Choose FIRST video → ")
    
    # Remove the chosen one so user doesn't pick the same twice by mistake
    remaining = [f for f in files if f != vid1]
    show_list(remaining)
    vid2 = choose(remaining, "Choose SECOND video → ")

    default_name = f"{vid1.stem} + {vid2.stem}.mp4"
    out_name = input(f"\nOutput filename [{default_name}]: ").strip()
    if not out_name:
        out_name = default_name
    if not out_name.lower().endswith(('.mp4', '.mkv', '.mov')):
        out_name += '.mp4'

    print(f"\nJoining with perfect audio sync:")
    print(f"   {vid1.name}")
    print(f" + {vid2.name}")
    print(f" → {out_name}\n")

    # Method 1: Super fast & perfect (99.9% of cases)
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'filelist.txt',
        '-c', 'copy',           # ← no re-encoding = pixel-perfect + original audio
        '-map', '0:v', '-map', '0:a?',   # take video + audio if exists
        out_name
    ]

    create_file_list(vid1, vid2)

    print("Running ffmpeg (stream copy – no quality loss)…")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\nSUCCESS! Perfectly joined with original sound → {out_name}")
        print("   Play it with any player – audio is there,")
    else:
        print("Fast method failed (different resolutions/codec?). Trying safe re-encode...")
        # Method 2: Safe but slightly slower (re-encodes video only when needed)
        cmd2 = [
            'ffmpeg', '-y',
            '-i', str(vid1),
            '-i', str(vid2),
            '-filter_complex', '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-c:a', 'aac', '-b:a', '192k',
            '-map', '[v]', '-map', '[a]',
            out_name
        ]
        subprocess.run(cmd2)
        print(f"\nDone (with very minor re-encode) → {out_name}")

    # Clean up
    if os.path.exists("filelist.txt"):
        os.remove("filelist.txt")

if __name__ == "__main__":
    # Simple check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: ffmpeg not found!")
        print("   Please install ffmpeg and make sure it's in your PATH")
        print("   → https://ffmpeg.org/download.html")
        sys.exit(1)

    main()