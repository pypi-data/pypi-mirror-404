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
This is an advanced audio playback library based on SDL2 and SDL2_mixer. It provides complete audio playback, control, caching, and metadata management functions, supports a variety of audio formats, and can automatically download and load the required SDL2 library files.

Main Functions
Audio format support: Supports MP3, WAV, OGG, FLAC, and other audio formats.
Playback control: Playback, pause, resume, stop, seek, and volume control.
Audio metadata: Acquire audio information such as duration, sample rate, number of channels, and bit rate.
Audio cache: Supports memory caching to improve repeated playback performance.
Multi-track management: Manages multiple audio tracks through the AID (Audio ID) system.
Automatic library management: Automatically downloads and loads SDL2 library files.

Core Classes and Functions
AudioLibrary Class
The main class of the audio library manages all audio playback functions.

Main Methods:
Playback-related:
Play_audio(aid) - Plays or resumes the audio of the specified AID.
Play_from_memory(file_path, loops, start_pos) - Plays audio from the memory cache.
Play_from_file(file_path, loops, start_pos) - Plays audio directly from the file.
New_aid(file_path) - Loads the file into memory and returns the AID (does not play immediately).

Control-related:
Pause_audio(aid) - Pauses the audio of the specified AID.
Stop_audio(aid) - Stops playback and returns the played duration.
Seek_audio(aid, position) - Seeks to the specified position (in seconds).
Set_volume(aid, volume) - Sets the volume (range 0-128).
Get_volume(aid) - Gets the current volume.

Metadata-related:
Get_audio_duration(source, is_file) - Gets the audio duration (in seconds).
Get_audio_metadata(source, is_file) - Gets complete audio metadata.
Get_audio_metadata_by_aid(aid) - Gets metadata via AID.
Get_audio_metadata_by_path(file_path) - Gets metadata via file path.

Resource management:
Clear_memory_cache() - Clears the memory cache.
Delay(ms) - SDL delay function.

Auxiliary Functions
Download_sdl_libraries() - Downloads SDL2 library files.
Import_sdl2() - Imports the SDL2 library.
Check_sdl_libraries_exist(directory) - Checks if the SDL2 libraries exist.
Load_sdl2_from_directory(directory) - Loads the SDL2 library from the specified directory.

SDL2 Wrapper Functions
SDL_Init(flags) - Initializes the SDL subsystem.
Mix_OpenAudio(frequency, format, channels, chunksize) - Opens the audio device.
Mix_LoadWAV(file) - Loads WAV audio files.
Mix_LoadMUS(file) - Loads music files.
Mix_PlayChannel(channel, chunk, loops) - Plays audio chunks.
Mix_PlayMusic(music, loops) - Plays music.

Usage Process
Initialize an AudioLibrary instance.
Load audio via new_aid() or play directly.
Use the AID to control audio playback.
Audio metadata can be obtained at any time.
Resources are automatically cleaned up after use.

This library is designed to be easy to use yet powerful, suitable for Python applications that require audio playback functionality.
=======================================
"""

from .player import *
print("""
=======================================
DVS Audio Library © （ap_ds ©）
The copyright of this project belongs to Dvs (DvsXT). Unauthorized modifications are prohibited.
Version number: v2.3.0
The official website of this project is: https://www.dvsyun.top/ap_ds
PyPi page address: https://pypi.org/project/ap-ds/
Developer: Dvs (DvsXT)
Developer's personal webpage: https://dvsyun.top/me/dvs
=======================================
""")
