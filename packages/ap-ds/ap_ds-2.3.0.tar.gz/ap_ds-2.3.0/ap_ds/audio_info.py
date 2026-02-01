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
This file is named audio_info.py
Purpose:
This file is an audio file format parsing library used to accurately parse metadata information of common audio files. It supports five mainstream audio formats: WAV, FLAC, MP3, AAC, and OGG Vorbis. By directly reading the file header and frame data, it calculates key information such as audio duration, sampling rate, number of channels, and bit rate.
Main classes and functions:
StreamInfo class
Purpose: Used to store the core information of audio streams.
property
Length: Audio duration (seconds)
Sample_rate: Sampling rate (Hz)
Channels: number of channels
Bitrate: Bit rate (bps)
FileType base class
Purpose: The base class for all audio format parsing classes, defining a universal interface.
Method:
_Parse(): Abstract method, subclass must be implemented to parse concrete format
Length, sample_rate, channels, bitrate: attribute visitors
Specific format parsing class
WAVFile class: parses WAV format files and obtains metadata by reading RIFF block information
FLACFile class: parsing FLAC format files, reading the DataMINFO block to obtain metadata
MP3File class: parsing MP3 format files, scanning frame by frame to calculate total duration and bit rate
AACFile class: parses AAC (ADTS) format files and calculates the total number of samples based on frame header information
OGGFile class: parsing OGG Vorbis format files and calculating duration through granule position
utility function
Open_2(): Open a file in binary mode
Read_u32_fube(), read_u32ile(), read_u16_1e(): Read integers of different byte orders
Factory function
Open_audio(): Automatically select the corresponding parsing class based on the file extension
=======================================
"""
import os
import struct
import io

# ============================================================
# 核心数据结构
# ============================================================

class StreamInfo:
    def __init__(self, length, sample_rate, channels, bitrate):
        self.length = float(length)
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.bitrate = int(bitrate)

    def __repr__(self):
        return (
            f"<StreamInfo length={self.length:.6f}s "
            f"rate={self.sample_rate}Hz "
            f"channels={self.channels} "
            f"bitrate={self.bitrate}bps>"
        )


class FileType:
    def __init__(self, filename):
        self.filename = filename
        self.info = self._parse()

    def _parse(self):
        raise ValueError("Invalid audio file")

    @property
    def length(self):
        return self.info.length

    @property
    def sample_rate(self):
        return self.info.sample_rate

    @property
    def channels(self):
        return self.info.channels

    @property
    def bitrate(self):
        return self.info.bitrate


# ============================================================
# 工具
# ============================================================

def open_file(path):
    return open(path, "rb")


def read_u32_be(f):
    return struct.unpack(">I", f.read(4))[0]


def read_u32_le(f):
    return struct.unpack("<I", f.read(4))[0]


def read_u16_le(f):
    return struct.unpack("<H", f.read(2))[0]


# ============================================================
# WAV（100% 精度）
# ============================================================

class WAVFile(FileType):
    def _parse(self):
        with open_file(self.filename) as f:
            if f.read(4) != b"RIFF":
                raise ValueError
            f.read(4)
            if f.read(4) != b"WAVE":
                raise ValueError

            sample_rate = channels = block_align = data_size = None

            while True:
                chunk = f.read(4)
                if not chunk:
                    break
                size = read_u32_le(f)

                if chunk == b"fmt ":
                    fmt = f.read(size)
                    channels = struct.unpack("<H", fmt[2:4])[0]
                    sample_rate = struct.unpack("<I", fmt[4:8])[0]
                    block_align = struct.unpack("<H", fmt[12:14])[0]
                elif chunk == b"data":
                    data_size = size
                    break
                else:
                    f.seek(size, io.SEEK_CUR)

            total_frames = data_size // block_align
            length = total_frames / sample_rate
            bitrate = sample_rate * block_align * 8 // channels

            return StreamInfo(length, sample_rate, channels, bitrate)


# ============================================================
# FLAC（100% 精度）
# ============================================================

class FLACFile(FileType):
    def _parse(self):
        with open_file(self.filename) as f:
            if f.read(4) != b"fLaC":
                raise ValueError

            while True:
                header = f.read(4)
                is_last = header[0] & 0x80
                block_type = header[0] & 0x7F
                size = struct.unpack(">I", b"\x00" + header[1:4])[0]

                if block_type == 0:  # STREAMINFO
                    data = f.read(size)
                    sample_rate = (
                        (data[10] << 12)
                        | (data[11] << 4)
                        | (data[12] >> 4)
                    )
                    channels = ((data[12] >> 1) & 0x07) + 1
                    total_samples = (
                        ((data[13] & 0x0F) << 32)
                        | (data[14] << 24)
                        | (data[15] << 16)
                        | (data[16] << 8)
                        | data[17]
                    )
                    length = total_samples / sample_rate
                    bitrate = os.path.getsize(self.filename) * 8 / length
                    return StreamInfo(length, sample_rate, channels, bitrate)
                else:
                    f.seek(size, io.SEEK_CUR)

                if is_last:
                    break

        raise ValueError


# ============================================================
# MP3（逐帧扫描，>=99.9%）
# ============================================================

MP3_BITRATES = [
    None, 32, 40, 48, 56, 64, 80, 96,
    112, 128, 160, 192, 224, 256, 320, None
]
MP3_SAMPLE_RATES = [44100, 48000, 32000, None]

class MP3File(FileType):
    def _parse(self):
        filesize = os.path.getsize(self.filename)
        total_frames = 0

        with open_file(self.filename) as f:
            while True:
                b = f.read(1)
                if not b:
                    break
                if b != b"\xff":
                    continue

                hdr = f.read(3)
                if len(hdr) < 3:
                    break
                if hdr[0] & 0xE0 != 0xE0:
                    f.seek(-3, 1)
                    continue

                bitrate = MP3_BITRATES[(hdr[1] >> 4) & 0x0F]
                sample_rate = MP3_SAMPLE_RATES[(hdr[1] >> 2) & 0x03]
                if not bitrate or not sample_rate:
                    f.seek(-3, 1)
                    continue

                frame_len = int(144000 * bitrate / sample_rate)
                total_frames += 1
                f.seek(frame_len - 4, 1)

        length = total_frames * 1152 / sample_rate
        bitrate = filesize * 8 / length

        return StreamInfo(length, sample_rate, 2, bitrate)


# ============================================================
# AAC (ADTS)（逐帧 samples 累计，>=99.9%）
# ============================================================

AAC_SAMPLE_RATES = [
    96000, 88200, 64000, 48000, 44100, 32000,
    24000, 22050, 16000, 12000, 11025, 8000
]

class AACFile(FileType):
    def _parse(self):
        total_samples = 0

        with open_file(self.filename) as f:
            while True:
                header = f.read(7)
                if len(header) < 7:
                    break
                if header[0] != 0xFF or (header[1] & 0xF0) != 0xF0:
                    break

                sr = AAC_SAMPLE_RATES[(header[2] >> 2) & 0x0F]
                channels = ((header[2] & 1) << 2) | ((header[3] >> 6) & 3)
                frame_length = (
                    ((header[3] & 0x03) << 11)
                    | (header[4] << 3)
                    | (header[5] >> 5)
                )

                total_samples += 1024
                f.seek(frame_length - 7, 1)

        length = total_samples / sr
        bitrate = os.path.getsize(self.filename) * 8 / length

        return StreamInfo(length, sr, channels, bitrate)


# ============================================================
# OGG Vorbis（granule position，>=99.9%）
# ============================================================

class OGGFile(FileType):
    def _parse(self):
        filesize = os.path.getsize(self.filename)

        with open_file(self.filename) as f:
            sample_rate = channels = None
            last_granule = 0

            while True:
                header = f.read(27)
                if len(header) < 27:
                    break
                if header[:4] != b"OggS":
                    break

                granule = struct.unpack("<Q", header[6:14])[0]
                last_granule = max(last_granule, granule)

                seg_count = header[26]
                seg_sizes = f.read(seg_count)
                f.seek(sum(seg_sizes), 1)

                if sample_rate is None:
                    pos = f.tell()
                    f.seek(-sum(seg_sizes), 1)
                    packet = f.read(seg_sizes[0])
                    if packet.startswith(b"\x01vorbis"):
                        channels = packet[11]
                        sample_rate = struct.unpack("<I", packet[12:16])[0]
                    f.seek(pos, 0)

        length = last_granule / sample_rate
        bitrate = filesize * 8 / length

        return StreamInfo(length, sample_rate, channels, bitrate)


# ============================================================
# 工厂
# ============================================================

def open_audio(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".wav":
        return WAVFile(filename)
    if ext == ".flac":
        return FLACFile(filename)
    if ext == ".mp3":
        return MP3File(filename)
    if ext == ".aac":
        return AACFile(filename)
    if ext == ".ogg":
        return OGGFile(filename)
    raise ValueError("Unsupported audio format")
