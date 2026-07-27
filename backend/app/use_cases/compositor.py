import subprocess

_ASPECT_TO_SIZE = {"9:16": "720x1280", "1:1": "1080x1080", "16:9": "1280x720"}
_ENCODE_ARGS = ["-preset", "ultrafast", "-threads", "1"]


def _run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {result.returncode}): {result.stderr.decode(errors='replace')[-2000:]}"
        )


def overlay_avatar_on_background(background_path: str, avatar_path: str, output_path: str) -> None:
    """Scales the avatar clip to ~60% width and centers it over the background, audio taken from avatar."""
    filter_complex = (
        "[1:v]scale=iw*0.6:-1[avatar];"
        "[0:v][avatar]overlay=(W-w)/2:(H-h)/2:shortest=1[v]"
    )
    _run_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", background_path,
            "-i", avatar_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a?",
            "-c:v", "libx264", *_ENCODE_ARGS, "-c:a", "aac",
            output_path,
        ]
    )


def concat_clips(clip_paths: list[str], output_path: str) -> None:
    if len(clip_paths) == 1:
        _run_ffmpeg(["ffmpeg", "-y", "-i", clip_paths[0], "-c", "copy", output_path])
        return

    list_file = output_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")
    _run_ffmpeg(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
    )


def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> None:
    escaped_srt = srt_path.replace(":", "\\:")
    _run_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles={escaped_srt}:force_style='FontSize=18,Outline=2'",
            "-c:v", "libx264", *_ENCODE_ARGS, "-c:a", "copy",
            output_path,
        ]
    )


def export_final(video_path: str, output_path: str, aspect_ratio: str) -> None:
    size = _ASPECT_TO_SIZE.get(aspect_ratio, "720x1280")
    _run_ffmpeg(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"scale={size}:force_original_aspect_ratio=decrease,pad={size}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", *_ENCODE_ARGS, "-c:a", "aac", "-movflags", "+faststart",
            output_path,
        ]
    )
