#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MiniCPM-o utils: 视频 / 音频处理等通用工具。
#
# 该模块设计为可以通过：
#   from minicpmo.utils import ...
# 在外部项目中直接使用。

import base64
import logging
import math
import os
import subprocess
import tempfile
from io import BytesIO

import librosa
import numpy as np
from decord import cpu
from decord import VideoReader
from PIL import Image

logger = logging.getLogger(__name__)

MAX_NUM_FRAMES = int(os.getenv("MAX_NUM_FRAMES", 64))
VIDEO_MME_DURATION = os.getenv("VIDEO_MME_DURATION", "ALL")


def concat_images(images, bg_color=(255, 255, 255), cell_size=None, line_color=(0, 0, 0), line_width=6):
    """
    images: List[PIL.Image.Image]
    Layout rules: 3 images -> 1x3; 4 images -> 2x2; 9 images -> 3x3; others: 1xN
    Only draw separator lines at joints (no outer border).
    """

    _converted_images = []
    for im in images:
        if isinstance(im, Image.Image):
            _converted_images.append(im)
        elif isinstance(im, (bytes, bytearray)):
            _converted_images.append(Image.open(BytesIO(im)).convert("RGB"))
        elif isinstance(im, str):
            b64 = im.split(",")[-1] if ";base64," in im else im
            img_bytes = base64.b64decode(b64)
            _converted_images.append(Image.open(BytesIO(img_bytes)).convert("RGB"))
        else:
            raise TypeError(f"Unsupported image type: {type(im)}")
    images = _converted_images
    n = len(images)
    if n == 0:
        raise ValueError("images is empty")

    if n == 4:
        rows, cols = 2, 2
    elif n == 3:
        # 动态选择 1x3 / 3x1，使得最终画布更接近正方形
        if cell_size is None:
            cell_w = max(im.width for im in images)
            cell_h = max(im.height for im in images)
        else:
            cell_w, cell_h = cell_size

        candidates = [(1, 3), (3, 1)]

        def canvas_ratio(r, c):
            W = c * cell_w + (c - 1) * line_width
            H = r * cell_h + (r - 1) * line_width
            return W / max(1, H)

        ratios = [abs(canvas_ratio(r, c) - 1.0) for (r, c) in candidates]
        best_idx = int(np.argmin(ratios))
        rows, cols = candidates[best_idx]
    elif n == 1:
        rows, cols = 1, 1
    elif n == 2:
        # 动态选择 1x2 / 2x1，使得最终画布更接近正方形
        if cell_size is None:
            cell_w = max(im.width for im in images)
            cell_h = max(im.height for im in images)
        else:
            cell_w, cell_h = cell_size
        candidates = [(1, 2), (2, 1)]

        def canvas_ratio(r, c):
            W = c * cell_w + (c - 1) * line_width
            H = r * cell_h + (r - 1) * line_width
            return W / max(1, H)

        ratios = [abs(canvas_ratio(r, c) - 1.0) for (r, c) in candidates]
        if ratios[0] == ratios[1]:
            avg_ar = np.mean([im.width / max(1, im.height) for im in images])
            rows, cols = (1, 2) if avg_ar >= 1.0 else (2, 1)
        else:
            best_idx = int(np.argmin(ratios))
            rows, cols = candidates[best_idx]
    else:
        rows, cols = 1, n

    if cell_size is None:
        cell_w = max(im.width for im in images)
        cell_h = max(im.height for im in images)
    else:
        cell_w, cell_h = cell_size

    def letterbox(im, tw, th):
        im = im.convert("RGB")
        w, h = im.size
        s = min(tw / w, th / h)
        nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
        try:
            im_r = im.resize((nw, nh), Image.Resampling.BICUBIC)
        except AttributeError:
            im_r = im.resize((nw, nh), Image.BICUBIC)
        canvas = Image.new("RGB", (tw, th), bg_color)
        canvas.paste(im_r, ((tw - nw) // 2, (th - nh) // 2))
        return canvas

    W = cols * cell_w + (cols - 1) * line_width
    H = rows * cell_h + (rows - 1) * line_width
    canvas = Image.new("RGB", (W, H), line_color)

    for i, im in enumerate(images[: rows * cols]):
        r, c = divmod(i, cols)
        cell = letterbox(im, cell_w, cell_h)
        x = c * (cell_w + line_width)
        y = r * (cell_h + line_width)
        canvas.paste(cell, (x, y))

    return canvas


def uniform_sample(l, n):
    if len(l) <= n:
        return l
    idxs = np.linspace(0, len(l) - 1, n, dtype=int)
    return [l[i] for i in idxs]


def get_audio_segments(
    timestamps, duration, video_path, audio_path=None, sr=16000, adjust_length=False, use_ffmpeg=False
):
    """
    根据时间戳切分音频。
    """
    import subprocess
    import warnings

    if audio_path is None:
        if use_ffmpeg:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                temp_audio_path = temp_audio_file.name
            try:
                cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", str(sr), temp_audio_path]
                subprocess.run(cmd, check=True, capture_output=True)
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="PySoundFile failed")
                    audio_np, sr = librosa.load(temp_audio_path, sr=sr, mono=True)
            finally:
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
        else:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="PySoundFile failed")
                    audio_np, sr = librosa.load(video_path, sr=sr, mono=True)
            except Exception:
                try:
                    from moviepy import VideoFileClip  # moviepy >= 2.0
                except ImportError:
                    from moviepy.editor import VideoFileClip  # moviepy < 2.0

                video_clip = VideoFileClip(video_path)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                    temp_audio_file_path = temp_audio_file.name
                    video_clip.audio.write_audiofile(temp_audio_file_path, codec="pcm_s16le", fps=sr)
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message="PySoundFile failed")
                        audio_np, sr = librosa.load(temp_audio_file_path, sr=sr, mono=True)
    else:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="PySoundFile failed")
            audio_np, sr = librosa.load(audio_path, sr=sr, mono=True)

    if adjust_length:
        num_frames = len(timestamps)
        target_length = num_frames * sr
        current_length = len(audio_np)
        if current_length < target_length:
            padding = np.zeros(target_length - current_length, dtype=audio_np.dtype)
            audio_np = np.concatenate([audio_np, padding])
        elif current_length > target_length:
            audio_np = audio_np[:target_length]

        audio_segments = []
        for i in range(len(timestamps)):
            start_sample = i * sr
            end_sample = (i + 1) * sr
            segment = audio_np[start_sample:end_sample]
            audio_segments.append(segment)
    else:
        audio_segments = []
        for i in range(len(timestamps)):
            start_time = timestamps[i]
            if i < len(timestamps) - 1:
                end_time = timestamps[i + 1]
            else:
                end_time = duration

            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            segment = audio_np[start_sample:end_sample]

            if i == len(timestamps) - 1 and len(segment) < 1600:
                segment = np.concatenate([segment, np.zeros(1600 - len(segment), dtype=segment.dtype)])
            audio_segments.append(segment)

    return audio_segments


def get_video_duration(video_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def get_video_frame_audio_segments(
    video_path, audio_path=None, last_vad_timestamp=None, stack_frames=1, use_ffmpeg=False, adjust_audio_length=False
):
    """
    同时抽取视频帧和对应音频片段，返回：
    - video_segments: List[PIL.Image]
    - audio_segments: List[np.ndarray]
    - stacked_video_segments: List[PIL.Image] or None
    """

    if use_ffmpeg:
        _duration = get_video_duration(video_path)
        _temp_dir = tempfile.TemporaryDirectory()
        _temp_dir_path = _temp_dir.name

        def _get_duration_and_fps():
            return _duration, None

        def _extract_frames_by_timestamps(timestamps, is_long_video):
            frames_dir = os.path.join(_temp_dir_path, "frames_1fps")
            os.makedirs(frames_dir, exist_ok=True)

            if is_long_video:
                fps_to_extract = 10
            else:
                fps_to_extract = 1

            frame_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vf",
                f"fps={fps_to_extract}",
                os.path.join(frames_dir, "frame_%06d.jpg"),
            ]
            subprocess.run(frame_cmd, capture_output=True, check=True)

            frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])

            if is_long_video:
                total_frames = len(frame_files)
                sampled_indices = uniform_sample(list(range(total_frames)), MAX_NUM_FRAMES)
                new_timestamps = [round(i / fps_to_extract, 1) for i in sampled_indices]
                frames = []
                for idx in sampled_indices:
                    frame_path = os.path.join(frames_dir, frame_files[idx])
                    frames.append(Image.open(frame_path).convert("RGB"))
                return frames, new_timestamps
            else:
                new_timestamps = list(range(len(frame_files)))
                frames = []
                for f in frame_files:
                    frame_path = os.path.join(frames_dir, f)
                    frames.append(Image.open(frame_path).convert("RGB"))
                return frames, new_timestamps

        def _extract_stack_frames(all_frame_timestamps, duration, num_seconds):
            stack_frames_dir = os.path.join(_temp_dir_path, "frames_stack")
            os.makedirs(stack_frames_dir, exist_ok=True)

            frame_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vf",
                f"fps={stack_frames}",
                os.path.join(stack_frames_dir, "frame_%06d.jpg"),
            ]
            subprocess.run(frame_cmd, capture_output=True, check=True)

            stack_frame_files = sorted([f for f in os.listdir(stack_frames_dir) if f.endswith(".jpg")])

            new_timestamps = []
            valid_frame_indices = []
            for i, f in enumerate(stack_frame_files):
                if i % stack_frames != 0:
                    ts = i / stack_frames
                    if ts < duration:
                        new_timestamps.append(ts)
                        valid_frame_indices.append(i)

            max_stack_frames_count = MAX_NUM_FRAMES * (stack_frames - 1)
            if len(valid_frame_indices) > max_stack_frames_count:
                sampled = uniform_sample(list(zip(valid_frame_indices, new_timestamps)), max_stack_frames_count)
                valid_frame_indices = [x[0] for x in sampled]
                new_timestamps = [x[1] for x in sampled]

            frames = []
            for idx in valid_frame_indices:
                frame_path = os.path.join(stack_frames_dir, stack_frame_files[idx])
                frames.append(Image.open(frame_path).convert("RGB"))

            return frames, new_timestamps

        def _cleanup():
            _temp_dir.cleanup()

    else:
        _vr = VideoReader(str(video_path), ctx=cpu(0))
        _avg_fps = _vr.get_avg_fps()
        _duration = len(_vr) / _avg_fps

        def _get_duration_and_fps():
            return _duration, _avg_fps

        def _extract_frames_by_timestamps(timestamps, is_long_video):
            if is_long_video:
                frame_idx = [min(int(ts * _avg_fps), len(_vr) - 1) for ts in timestamps]
                frame_idx = uniform_sample(frame_idx, MAX_NUM_FRAMES)
                new_timestamps = uniform_sample(timestamps, MAX_NUM_FRAMES)
            else:
                num_seconds = len(timestamps)
                frame_idx = [int(i * _avg_fps) for i in range(num_seconds)]
                new_timestamps = timestamps

            video = _vr.get_batch(frame_idx).asnumpy()
            frames = [Image.fromarray(v.astype("uint8")).convert("RGB") for v in video]
            return frames, new_timestamps

        def _extract_stack_frames(all_frame_timestamps, duration, num_seconds):
            stack_frame_idx = [min(int(ts * _avg_fps), len(_vr) - 1) for ts in all_frame_timestamps]

            max_stack_frames_count = MAX_NUM_FRAMES * (stack_frames - 1)
            if len(stack_frame_idx) > max_stack_frames_count:
                stack_frame_idx = uniform_sample(stack_frame_idx, max_stack_frames_count)
                new_timestamps = uniform_sample(all_frame_timestamps, max_stack_frames_count)
            else:
                new_timestamps = all_frame_timestamps

            stack_video = _vr.get_batch(stack_frame_idx).asnumpy()
            frames = [Image.fromarray(v.astype("uint8")).convert("RGB") for v in stack_video]
            return frames, new_timestamps

        def _cleanup():
            pass

    try:
        duration, avg_fps = _get_duration_and_fps()
        if last_vad_timestamp is not None:
            duration = last_vad_timestamp

        num_seconds = math.ceil(duration)
        second_timestamps = list(range(num_seconds))

        is_long_video = duration > MAX_NUM_FRAMES
        if is_long_video:
            timestamps = [round(i * 0.1, 1) for i in range(int(duration / 0.1))]
        else:
            timestamps = second_timestamps

        video_segments, timestamps = _extract_frames_by_timestamps(timestamps, is_long_video)

        stacked_video_segments = None
        if stack_frames > 1:
            all_frame_timestamps = []
            for sec in range(num_seconds):
                for i in range(1, stack_frames):
                    ts = sec + i / stack_frames
                    if ts < duration:
                        all_frame_timestamps.append(ts)

            all_frames, all_frame_timestamps = _extract_stack_frames(all_frame_timestamps, duration, num_seconds)

            stacked_video_segments = []
            frame_cursor = 0
            for sec in range(num_seconds):
                frames_this_second = []
                while frame_cursor < len(all_frame_timestamps) and all_frame_timestamps[frame_cursor] < sec + 1:
                    frames_this_second.append(all_frames[frame_cursor])
                    frame_cursor += 1

                if len(frames_this_second) > 0:
                    stacked_frame = concat_images(frames_this_second)
                    stacked_video_segments.append(stacked_frame)
                else:
                    stacked_video_segments.append(None)

        audio_segments = get_audio_segments(
            timestamps, duration, video_path, audio_path, adjust_length=adjust_audio_length, use_ffmpeg=use_ffmpeg
        )

        return video_segments, audio_segments, stacked_video_segments

    finally:
        _cleanup()


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_from_results(results_log: list, video_duration: float, output_srt_path: str) -> int:
    """
    从推理结果生成 SRT 字幕文件。
    """

    special_tokens = ["<|tts_pad|>", "<|turn_eos|>", "<|chunk_eos|>", "<|listen|>", "<|speak|>"]

    srt_lines = []
    subtitle_index = 1

    for result in results_log:
        chunk_idx = result["chunk_idx"]
        text = result.get("text", "")
        is_listen = result.get("is_listen", True)

        if not text or is_listen:
            continue

        clean_text = text
        for token in special_tokens:
            clean_text = clean_text.replace(token, "")
        clean_text = clean_text.strip()

        if not clean_text:
            continue

        start_time = chunk_idx + 1
        end_time = chunk_idx + 2

        if start_time >= video_duration:
            continue
        end_time = min(end_time, video_duration)

        start_str = format_srt_time(start_time)
        end_str = format_srt_time(end_time)

        srt_lines.append(f"{subtitle_index}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(clean_text)
        srt_lines.append("")

        subtitle_index += 1

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    return subtitle_index - 1


def generate_ai_audio_file(
    timed_output_audio: list,
    video_duration: float,
    output_sample_rate: int,
) -> str:
    import soundfile as sf

    max_end_time = 0
    for chunk_idx, audio in timed_output_audio:
        start_time = chunk_idx + 1
        duration = len(audio) / output_sample_rate
        end_time = start_time + duration
        max_end_time = max(max_end_time, end_time)

    total_duration = max(video_duration, max_end_time)
    total_samples = int(total_duration * output_sample_rate)
    ai_audio_track = np.zeros(total_samples, dtype=np.float32)

    for chunk_idx, audio in timed_output_audio:
        start_time = chunk_idx + 1
        start_sample = int(start_time * output_sample_rate)
        end_sample = start_sample + len(audio)

        if end_sample <= len(ai_audio_track):
            ai_audio_track[start_sample:end_sample] += audio
        else:
            available_len = len(ai_audio_track) - start_sample
            if available_len > 0:
                ai_audio_track[start_sample:] += audio[:available_len]

    ai_audio_track = np.clip(ai_audio_track, -1.0, 1.0)

    ai_audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    sf.write(
        ai_audio_path,
        (ai_audio_track * 32768).astype(np.int16),
        output_sample_rate,
        subtype="PCM_16",
    )

    return ai_audio_path


def generate_duplex_video(
    video_path: str,
    output_video_path: str,
    results_log: list,
    timed_output_audio: list,
    output_sample_rate: int = 24000,
):
    """
    使用 ffmpeg 合成带有 AI 回复与字幕的双声道视频。
    """
    import soundfile as sf

    try:
        video_duration = get_video_duration(video_path)
    except Exception as e:
        video_duration = 60.0
        logger.warning(f"  ffprobe duration failed: {e}, using 60s default")

    output_dir = os.path.dirname(output_video_path)
    srt_path = os.path.join(output_dir, "subtitles.srt")
    subtitle_count = generate_srt_from_results(results_log, video_duration, srt_path)

    ai_audio_path = None
    if timed_output_audio:
        ai_audio_path = generate_ai_audio_file(timed_output_audio, video_duration, output_sample_rate)

    has_original_audio = False
    try:
        probe_audio_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(probe_audio_cmd, capture_output=True, text=True)
        has_original_audio = result.stdout.strip() == "audio"
    except Exception:
        pass

    has_subtitles = subtitle_count > 0 and os.path.exists(srt_path)

    if has_subtitles:
        srt_path_escaped = srt_path.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")
        subtitle_filter = (
            f"subtitles='{srt_path_escaped}':"
            f"force_style='FontSize=28,"
            f"PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,"
            f"BorderStyle=3,"
            f"Outline=2,"
            f"Shadow=1,"
            f"MarginV=30,"
            f"Alignment=2'"
        )

    cmd = ["ffmpeg", "-y", "-i", video_path]

    if ai_audio_path:
        cmd.extend(["-i", ai_audio_path])

        if has_original_audio:
            if has_subtitles:
                filter_complex = f"[0:v]{subtitle_filter}[vout];[0:a][1:a]amix=inputs=2:duration=longest[aout]"
                cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "[aout]"])
            else:
                filter_complex = f"[0:a][1:a]amix=inputs=2:duration=longest[aout]"
                cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
        else:
            if has_subtitles:
                filter_complex = f"[0:v]{subtitle_filter}[vout]"
                cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"])
            else:
                cmd.extend(["-map", "0:v", "-map", "1:a"])
    else:
        if has_subtitles:
            cmd.extend(["-vf", subtitle_filter])
        if has_original_audio:
            cmd.extend(["-c:a", "copy"])

    cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-preset", "medium", "-crf", "23", output_video_path])

    try:
        _ = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        raise
    finally:
        if os.path.exists(srt_path):
            os.remove(srt_path)
        if ai_audio_path and os.path.exists(ai_audio_path):
            os.remove(ai_audio_path)

    return output_video_path


__all__ = [
    "concat_images",
    "uniform_sample",
    "get_audio_segments",
    "get_video_duration",
    "get_video_frame_audio_segments",
    "format_srt_time",
    "generate_srt_from_results",
    "generate_ai_audio_file",
    "generate_duplex_video",
]

