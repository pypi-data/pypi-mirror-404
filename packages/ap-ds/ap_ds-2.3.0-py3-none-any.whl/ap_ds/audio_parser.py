"""
=======================================
DVS Audio Library © （ap_ds ©）
The copyright of this project belongs to Dvs (DvsXT). Unauthorized modifications are prohibited.
Version number: v2.3.0
The official website of this project is: https://www.dvsyun.top/ap_ds
PyPi page address: https://pypi.org/project/ap-ds/
Developer: Dvs (DvsXT)
Developer's personal webpage: https://dvsyun.top/me/dvs
=======================================
This file is named audio_ parser.py
Purpose:
This file is an encapsulation of audio_info.exe, providing a simpler and more user-friendly interface for extracting audio metadata. It adopts a singleton pattern design, providing a unified API for upper level applications to obtain audio duration and complete metadata information.
Main classes and functions:
AudioParser class
Purpose: The main implementation class of an audio parser, which encapsulates the functions of opening audio files and extracting metadata.
Core method:
_Open_audio(): Internal method that attempts to open an audio file and returns a parsed object
Duration extraction interface (maintaining backward compatibility):
Get-audio-duration (): Get audio duration (seconds)
get_ogg_duration()、get_flac_duration()、get_mp3_duration()、get_wav_duration()： Obtain duration for specific formats
Get_ duration_fy_extension(): Get duration based on extension
Unified metadata API:
Get-audio'metadata (): Returns a dictionary containing complete audio metadata
Get-audio-info (): an alias for get-audio-metadata (), providing a compatible interface
The returned metadata dictionary contains:
Path: file path
Format: file format (extension)
Duration: integer duration (seconds)
Length: Floating point duration (seconds)
Sample_rate: Sampling rate
Channels: number of channels
Bitrate: Bit rate
Single instance management function
Get_ audio_ parser (): Get a globally unique AudioParser instance to ensure efficient resource utilization
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio_info


class AudioParser:
    """
    轻量音频解析器
    依赖 audio_info.py
    只提供：时长 + 基础流信息
    """

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # 核心内部方法
    # ---------------------------------------------------------

    def _open_audio(self, file_path):
        if not os.path.exists(file_path):
            return None
        try:
            return audio_info.open_audio(file_path)
        except Exception:
            return None

    # ---------------------------------------------------------
    # 时长接口（向后兼容）
    # ---------------------------------------------------------

    def get_audio_duration(self, file_path):
        audio = self._open_audio(file_path)
        if not audio:
            return 0
        return int(audio.length)

    def get_ogg_duration(self, file_path):
        return self.get_audio_duration(file_path)

    def get_flac_duration(self, file_path):
        return self.get_audio_duration(file_path)

    def get_mp3_duration(self, file_path):
        return self.get_audio_duration(file_path)

    def get_wav_duration(self, file_path):
        return self.get_audio_duration(file_path)

    def get_duration_by_extension(self, file_path):
        return self.get_audio_duration(file_path)

    # ---------------------------------------------------------
    # 新增：统一元数据 API
    # ---------------------------------------------------------

    def get_audio_metadata(self, file_path):
        """
        返回音频基础元数据（不含标签）

        返回 dict，失败返回 None
        """
        audio = self._open_audio(file_path)
        if not audio or not hasattr(audio, "info"):
            return None

        info = audio.info
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        return {
            "path": file_path,
            "format": ext,
            "duration": int(info.length),
            "length": float(info.length),
            "sample_rate": info.sample_rate,
            "channels": info.channels,
            "bitrate": info.bitrate,
        }

    def get_audio_info(self, file_path):
        """
        兼容命名接口（别名）
        """
        return self.get_audio_metadata(file_path)


# ---------------------------------------------------------
# 单例模式（保持原有使用方式）
# ---------------------------------------------------------

_audio_parser = None


def get_audio_parser():
    global _audio_parser
    if _audio_parser is None:
        _audio_parser = AudioParser()
    return _audio_parser
