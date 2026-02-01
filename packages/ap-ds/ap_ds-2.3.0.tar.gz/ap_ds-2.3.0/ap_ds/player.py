"""
=======================================
DVS Audio Library © （ap_ds ©）
The copyright of this project belongs to Dvs (DvsXT). Unauthorized modifications are prohibited.
Version number: v2.3.0
The official website of this project is: https://www.dvsyun.top/ap_ds
PyPi page address: https://pypi.org/project/ap-ds/
Developer: Dvs (DvsXT)
Developer's personal webpage: https://dvsyun.top/me/dvs

This file is named player.py
This is the main program of AP_DS. It provides complete audio playback, control, caching, and metadata management functions, supports multiple audio formats, and can automatically download and load the required SDL2 library files.
=======================================
"""
import os
import sys
import time
import ctypes
import urllib.request  # Use Python's built-in library instead of external requests
from ctypes import *
from collections import defaultdict
import struct
from typing import *
import json
try:
    try:
        from audio_parser import get_audio_parser
        AUDIO_PARSER_AVAILABLE = True
    except:
        from .audio_parser import get_audio_parser
        AUDIO_PARSER_AVAILABLE = True
except ImportError:
    AUDIO_PARSER_AVAILABLE = False

    print("Warning: audio_parser module not available, using fallback duration methods")
def download_sdl_libraries():
    """Download SDL2 libraries to package directory based on platform"""
    import sys
    import urllib.request
    import os
    import tempfile
    import shutil
    import subprocess
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Package directory: {current_dir}")
    
    platform = sys.platform
    
    if platform == "win32":
        # Windows - download .dll files
        files = [
            {
                "url": "https://dvsyun.top/ap_ds/download/SDL2",
                "expected_name": "SDL2.dll",
            },
            {
                "url": "https://dvsyun.top/ap_ds/download/SDL2_M", 
                "expected_name": "SDL2_mixer.dll",
            }
        ]
        
        for file_info in files:
            file_path = os.path.join(current_dir, file_info["expected_name"])
            if os.path.exists(file_path):
                print(f"{file_info['expected_name']} already exists")
                continue
                
            print(f"Downloading {file_info['expected_name']} to package directory...")
            try:
                with urllib.request.urlopen(file_info["url"], timeout=30) as response:
                    content = response.read()
                    print(f"Downloaded {len(content)} bytes")
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    print(f"Successfully downloaded {file_info['expected_name']} to package directory")
                    
            except Exception as e:
                print(f"Download failed: {str(e)}")
                continue
    
    elif platform == "darwin":
        # macOS - download .dmg files and extract .framework
        print("🍎 macOS detected, downloading SDL2 frameworks...")
        
        # Define framework download URLs
        frameworks = [
            {
                "name": "SDL2",
                "url": "https://dvsyun.top/ap_ds/download/SDL2/MAC",
                "dmg_name": "SDL2.dmg",
                "framework_name": "SDL2.framework",
                "library_name": "SDL2"  # Note: no extension!
            },
            {
                "name": "SDL2_mixer",
                "url": "https://dvsyun.top/ap_ds/download/SDL2_M/MAC",
                "dmg_name": "SDL2_mixer.dmg",
                "framework_name": "SDL2_mixer.framework",
                "library_name": "SDL2_mixer"  # Note: no extension!
            }
        ]
        
        for framework_info in frameworks:
            framework_path = os.path.join(current_dir, framework_info["framework_name"])
            
            # Check if already exists
            if os.path.exists(framework_path):
                print(f"{framework_info['framework_name']} already exists")
                continue
            
            # Download .dmg to temp file
            print(f"Downloading {framework_info['dmg_name']}...")
            temp_dmg = tempfile.NamedTemporaryFile(suffix=".dmg", delete=False)
            temp_dmg.close()
            
            try:
                # Download .dmg
                urllib.request.urlretrieve(framework_info["url"], temp_dmg.name)
                print(f"✅ Downloaded {framework_info['dmg_name']}")
                
                # Extract .framework from .dmg
                mount_point = tempfile.mkdtemp(prefix=f"{framework_info['name']}_mount_")
                
                try:
                    # Mount the .dmg
                    cmd = ["hdiutil", "attach", temp_dmg.name, "-mountpoint", mount_point, "-nobrowse", "-quiet"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"❌ Failed to mount {framework_info['dmg_name']}: {result.stderr}")
                        continue
                    
                    print(f"✅ Mounted to: {mount_point}")
                    
                    # Find .framework in the mounted volume
                    framework_src = None
                    for root, dirs, files in os.walk(mount_point):
                        if framework_info["framework_name"] in dirs:
                            framework_src = os.path.join(root, framework_info["framework_name"])
                            break
                    
                    # Alternative search paths
                    if not framework_src:
                        possible_paths = [
                            os.path.join(mount_point, framework_info["framework_name"]),
                            os.path.join(mount_point, framework_info["name"], framework_info["framework_name"]),
                            os.path.join(mount_point, "Frameworks", framework_info["framework_name"]),
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                framework_src = path
                                break
                    
                    if not framework_src:
                        print(f"❌ Could not find {framework_info['framework_name']} in dmg")
                        subprocess.run(["hdiutil", "detach", mount_point, "-quiet"])
                        continue
                    
                    # Copy .framework to package directory
                    shutil.copytree(framework_src, framework_path)
                    print(f"✅ Extracted {framework_info['framework_name']} to package directory")
                    
                    # Unmount
                    subprocess.run(["hdiutil", "detach", mount_point, "-quiet"])
                    print(f"✅ Unmounted {framework_info['dmg_name']}")
                    
                except Exception as e:
                    print(f"❌ Extraction failed: {e}")
                    # Clean up mount point
                    try:
                        subprocess.run(["hdiutil", "detach", mount_point, "-force", "-quiet"])
                    except:
                        pass
                    continue
                
                finally:
                    # Clean up temp .dmg file
                    os.unlink(temp_dmg.name)
                    
            except Exception as e:
                print(f"❌ Download failed: {str(e)}")
                continue
    
    elif platform.startswith("linux"):
        # Linux - just raise error
        raise ImportError(
            "🚫 Linux is not supported by ap_ds.\n"
            "Reason: Linux desktop audio requirements are minimal and better served by existing tools.\n"
            "Server usage should use HTML5 Audio tags, not local playback libraries.\n"
            "If you really need it, compile it yourself from source."
        )
    
    else:
        raise ImportError(f"Unsupported platform: {platform}")
    
    print(f"Files in package directory after download: {os.listdir(current_dir)}")


def check_sdl_libraries_exist(directory):
    """Check if SDL2 library files exist in the specified directory based on platform"""
    import sys
    
    platform = sys.platform
    
    if platform == "win32":
        # Windows - check for .dll files
        sdl2_path = os.path.join(directory, "SDL2.dll")
        sdl2_mixer_path = os.path.join(directory, "SDL2_mixer.dll")
        return os.path.exists(sdl2_path) and os.path.exists(sdl2_mixer_path)
    
    elif platform == "darwin":
        # macOS - check for .framework directories
        sdl2_framework = os.path.join(directory, "SDL2.framework")
        sdl2_mixer_framework = os.path.join(directory, "SDL2_mixer.framework")
        
        # Also check for the actual library files inside frameworks
        sdl2_lib = os.path.join(sdl2_framework, "SDL2")  # Note: no extension!
        sdl2_mixer_lib = os.path.join(sdl2_mixer_framework, "SDL2_mixer")  # Note: no extension!
        
        return (os.path.exists(sdl2_framework) and 
                os.path.exists(sdl2_mixer_framework) and
                os.path.exists(sdl2_lib) and 
                os.path.exists(sdl2_mixer_lib))
    
    else:
        return False


def load_sdl2_from_directory(directory):
    """Load SDL2 libraries from the specified directory based on platform"""
    import sys
    from ctypes import CDLL
    
    platform = sys.platform
    
    if platform == "win32":
        # Windows - load .dll files
        # Add DLL search path
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(directory)
        
        # Set DLL search path
        os.environ['PATH'] = directory + os.pathsep + os.environ.get('PATH', '')
        
        # Build full DLL paths
        sdl2_path = os.path.join(directory, "SDL2.dll")
        sdl2_mixer_path = os.path.join(directory, "SDL2_mixer.dll")
        
        if os.path.exists(sdl2_path) and os.path.exists(sdl2_mixer_path):
            _sdl_lib = CDLL(sdl2_path)
            _mix_lib = CDLL(sdl2_mixer_path)
            return _sdl_lib, _mix_lib
        else:
            raise FileNotFoundError(f"SDL2 libraries not found in {directory}")
    
    elif platform == "darwin":
        # macOS - load from .framework directories
        sdl2_framework = os.path.join(directory, "SDL2.framework")
        sdl2_mixer_framework = os.path.join(directory, "SDL2_mixer.framework")
        
        # The actual library files are inside frameworks (no extension!)
        sdl2_lib_path = os.path.join(sdl2_framework, "SDL2")
        sdl2_mixer_lib_path = os.path.join(sdl2_mixer_framework, "SDL2_mixer")
        
        # Also try the Versions/Current/ path for better compatibility
        sdl2_lib_alt = os.path.join(sdl2_framework, "Versions", "Current", "SDL2")
        sdl2_mixer_lib_alt = os.path.join(sdl2_mixer_framework, "Versions", "Current", "SDL2_mixer")
        
        # Try primary paths first, then alternatives
        lib_paths_to_try = [
            (sdl2_lib_path, sdl2_mixer_lib_path),
            (sdl2_lib_alt, sdl2_mixer_lib_alt),
        ]
        
        for sdl_path, mixer_path in lib_paths_to_try:
            if os.path.exists(sdl_path) and os.path.exists(mixer_path):
                try:
                    # macOS may need framework path in DYLD_FRAMEWORK_PATH
                    framework_dir = os.path.dirname(os.path.dirname(sdl_path))
                    if 'DYLD_FRAMEWORK_PATH' not in os.environ:
                        os.environ['DYLD_FRAMEWORK_PATH'] = framework_dir
                    else:
                        os.environ['DYLD_FRAMEWORK_PATH'] = framework_dir + ':' + os.environ['DYLD_FRAMEWORK_PATH']
                    
                    _sdl_lib = CDLL(sdl_path)
                    _mix_lib = CDLL(mixer_path)
                    return _sdl_lib, _mix_lib
                except Exception as e:
                    print(f"Warning: Failed to load from {sdl_path}: {e}")
                    continue
        
        # If all else fails, try using ctypes.util.find_library
        try:
            import ctypes.util
            sdl_path = ctypes.util.find_library("SDL2")
            mixer_path = ctypes.util.find_library("SDL2_mixer")
            
            if sdl_path and mixer_path:
                _sdl_lib = CDLL(sdl_path)
                _mix_lib = CDLL(mixer_path)
                return _sdl_lib, _mix_lib
        except:
            pass
        
        raise FileNotFoundError(
            f"SDL2 frameworks not found or could not be loaded.\n"
            f"Checked paths:\n"
            f"  SDL2: {sdl2_lib_path}\n"
            f"  SDL2_mixer: {sdl2_mixer_lib_path}\n"
            f"Framework directories should be in: {directory}"
        )
    
    else:
        raise ImportError(f"Unsupported platform: {platform}")


def import_sdl2():
    """Main function: Import SDL2 libraries with cross-platform support"""
    import sys
    from ctypes import CDLL
    
    global _sdl_lib, _mix_lib  
    
    # Get current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Platform-specific library names
    platform = sys.platform
    
    if platform == "win32":
        lib_names = ("SDL2.dll", "SDL2_mixer.dll")
    elif platform == "darwin":
        lib_names = ("SDL2", "SDL2_mixer")  # No extensions for macOS frameworks
    elif platform.startswith("linux"):
        # Linux is explicitly not supported
        raise ImportError(
            "🚫 Linux is not supported by ap_ds.\n"
            "This is a deliberate design choice:\n"
            "1. Linux desktop users have better audio options already\n"
            "2. Server usage should use HTML5 Audio tags\n"
            "3. Supporting Linux would increase complexity 10x for <2% of users\n"
            "\n"
            "If you need audio on Linux:\n"
            "• For desktop: Use system players or command-line tools\n"
            "• For servers: Use HTML5 Audio or other web-based solutions\n"
            "• If you really want this library: Fork it and port it yourself"
        )
    else:
        raise ImportError(f"Unsupported platform: {platform}")
    
    try:
        # First try to load from current directory
        if check_sdl_libraries_exist(current_dir):
            return load_sdl2_from_directory(current_dir)
        
        # If not found in current directory, try system path (Windows only)
        if platform == "win32":
            try:
                _sdl_lib = CDLL("SDL2.dll")
                _mix_lib = CDLL("SDL2_mixer.dll")
                return _sdl_lib, _mix_lib
            except:
                pass
        elif platform == "darwin":
            # macOS: try system framework paths
            try:
                import ctypes.util
                sdl_path = ctypes.util.find_library("SDL2")
                mixer_path = ctypes.util.find_library("SDL2_mixer")
                
                if sdl_path and mixer_path:
                    _sdl_lib = CDLL(sdl_path)
                    _mix_lib = CDLL(mixer_path)
                    return _sdl_lib, _mix_lib
            except:
                pass
        
        # If loading fails, download library files
        print(f"SDL2 libraries not found for {platform}, downloading...")
        download_sdl_libraries()
        
        # After download, try to load from current directory again
        if check_sdl_libraries_exist(current_dir):
            return load_sdl2_from_directory(current_dir)
        else:
            print(f"Files in current directory: {os.listdir(current_dir)}")
            raise ImportError(
                f"Failed to load SDL libraries after download!\n"
                f"Platform: {platform}\n"
                f"Current directory: {current_dir}\n"
                f"Error details: Files were downloaded but could not be loaded"
            )
            
    except Exception as e:
        if platform.startswith("linux"):
            # Re-raise the Linux-specific error
            raise
        else:
            raise ImportError(
                f"Failed to load SDL2 for {platform}: {e}\n"
                f"Current directory: {current_dir}\n"
                f"Library search path: {os.environ.get('PATH', 'N/A')}"
            )


# Usage example
try:
    _sdl_lib, _mix_lib = import_sdl2()
    print(f"✅ Successfully loaded SDL2 libraries for {sys.platform}")
except ImportError as e:
    print(f"Failed to load SDL2: {e}")
# SDL2 and SDL2_mixer constants and structures

# SDL base type definitions
SDL_bool = c_int
SDL_TRUE = 1
SDL_FALSE = 0

# SDL initialization flags
SDL_INIT_TIMER = 0x00000001
SDL_INIT_AUDIO = 0x00000010
SDL_INIT_VIDEO = 0x00000020
SDL_INIT_JOYSTICK = 0x00000200
SDL_INIT_HAPTIC = 0x00001000
SDL_INIT_GAMECONTROLLER = 0x00002000
SDL_INIT_EVENTS = 0x00004000
SDL_INIT_EVERYTHING = (SDL_INIT_TIMER | SDL_INIT_AUDIO | SDL_INIT_VIDEO |
                      SDL_INIT_JOYSTICK | SDL_INIT_HAPTIC |
                      SDL_INIT_GAMECONTROLLER | SDL_INIT_EVENTS)

# SDL audio format constants
AUDIO_U8 = 0x0008
AUDIO_S8 = 0x8008
AUDIO_U16LSB = 0x0010
AUDIO_S16LSB = 0x8010
AUDIO_U16MSB = 0x1010
AUDIO_S16MSB = 0x9010
AUDIO_U16 = AUDIO_U16LSB
AUDIO_S16 = AUDIO_S16LSB
AUDIO_S32LSB = 0x8020
AUDIO_S32MSB = 0x9020
AUDIO_S32 = AUDIO_S32LSB
AUDIO_F32LSB = 0x8120
AUDIO_F32MSB = 0x9120
AUDIO_F32 = AUDIO_F32LSB

if sys.byteorder == 'little':
    AUDIO_U16SYS = AUDIO_U16LSB
    AUDIO_S16SYS = AUDIO_S16LSB
    AUDIO_S32SYS = AUDIO_S32LSB
    AUDIO_F32SYS = AUDIO_F32LSB
else:
    AUDIO_U16SYS = AUDIO_U16MSB
    AUDIO_S16SYS = AUDIO_S16MSB
    AUDIO_S32SYS = AUDIO_S32MSB
    AUDIO_F32SYS = AUDIO_F32MSB

MIX_DEFAULT_FORMAT = AUDIO_S16SYS

# SDL_mixer constants
MIX_INIT_FLAC = 0x00000001
MIX_INIT_MOD = 0x00000002
MIX_INIT_MP3 = 0x00000008
MIX_INIT_OGG = 0x00000010
MIX_INIT_MID = 0x00000020
MIX_INIT_OPUS = 0x00000040

# Channel control constants
MIX_CHANNEL_POST = -2
MIX_DEFAULT_CHANNELS = 2

# Music type constants
MUS_NONE = 0
MUS_CMD = 1
MUS_WAV = 2
MUS_MOD = 3
MUS_MID = 4
MUS_OGG = 5
MUS_MP3 = 6
MUS_FLAC = 7
MUS_OPUS = 8

# SDL structure definitions
class SDL_AudioSpec(ctypes.Structure):
    _fields_ = [
        ("freq", c_int),
        ("format", c_uint16),
        ("channels", c_uint8),
        ("silence", c_uint8),
        ("samples", c_uint16),
        ("padding", c_uint16),
        ("size", c_uint32),
        ("callback", c_void_p),
        ("userdata", c_void_p)
    ]

class Mix_Chunk(ctypes.Structure):
    _fields_ = [
        ("allocated", c_int),
        ("abuf", ctypes.POINTER(c_uint8)),
        ("alen", c_uint32),
        ("volume", c_uint8)
    ]

# Usage example
try:
    _sdl_lib, _mix_lib = import_sdl2()
except ImportError as e:
    print(f"Failed to load SDL2: {e}")    
# SDL function definitions
def SDL_Init(flags):
    return _sdl_lib.SDL_Init(flags)

def SDL_InitSubSystem(flags):
    return _sdl_lib.SDL_InitSubSystem(flags)

def SDL_Quit():
    _sdl_lib.SDL_Quit()

def SDL_QuitSubSystem(flags):
    _sdl_lib.SDL_QuitSubSystem(flags)

def SDL_WasInit(flags):
    return _sdl_lib.SDL_WasInit(flags)

def SDL_GetError():
    return _sdl_lib.SDL_GetError()

# SDL_mixer function definitions
def Mix_OpenAudio(frequency, format, channels, chunksize):
    return _mix_lib.Mix_OpenAudio(frequency, format, channels, chunksize)

def Mix_CloseAudio():
    _mix_lib.Mix_CloseAudio()

def Mix_QuerySpec(frequency, format, channels):
    return _mix_lib.Mix_QuerySpec(ctypes.byref(frequency),
                                ctypes.byref(format),
                                ctypes.byref(channels))

def Mix_LoadWAV(file):
    if isinstance(file, str):
        file = file.encode('utf-8')
    elif isinstance(file, bytes):
        pass
    else:
        file = str(file).encode('utf-8')
    
    return _mix_lib.Mix_LoadWAV_RW(_sdl_lib.SDL_RWFromFile(file, b"rb"), 1)

def Mix_LoadMUS(file: Union[str, bytes]) -> Any:
    if isinstance(file, str):
        file = file.encode('utf-8')
    elif isinstance(file, bytes):
        pass
    else:
        file = str(file).encode('utf-8')
    
    return _mix_lib.Mix_LoadMUS_RW(_sdl_lib.SDL_RWFromFile(file, b"rb"), 1)

def Mix_FreeChunk(chunk):
    _mix_lib.Mix_FreeChunk(chunk)

def Mix_FreeMusic(music):
    _mix_lib.Mix_FreeMusic(music)

def Mix_PlayChannel(channel, chunk, loops):
    return _mix_lib.Mix_PlayChannel(channel, chunk, loops)

def Mix_PlayMusic(music, loops):
    return _mix_lib.Mix_PlayMusic(music, loops)

def Mix_Pause(channel):
    _mix_lib.Mix_Pause(channel)

def Mix_PauseMusic():
    _mix_lib.Mix_PauseMusic()

def Mix_Resume(channel):
    _mix_lib.Mix_Resume(channel)

def Mix_ResumeMusic():
    _mix_lib.Mix_ResumeMusic()

def Mix_HaltChannel(channel):
    return _mix_lib.Mix_HaltChannel(channel)

def Mix_HaltMusic():
    return _mix_lib.Mix_HaltMusic()

def Mix_SetMusicPosition(position):
    return _mix_lib.Mix_SetMusicPosition(position)

def Mix_MusicDuration(music):
    return _mix_lib.Mix_MusicDuration(music)

def Mix_Volume(channel, volume):
    return _mix_lib.Mix_Volume(channel, volume)

def Mix_VolumeMusic(volume):
    return _mix_lib.Mix_VolumeMusic(volume)

def Mix_AllocateChannels(numchans):
    return _mix_lib.Mix_AllocateChannels(numchans)

def Mix_GetMusicType(music):
    return _mix_lib.Mix_GetMusicType(music)

def Mix_FadingMusic():
    return _mix_lib.Mix_FadingMusic()

def Mix_FadeInMusic(music, loops, ms):
    return _mix_lib.Mix_FadeInMusic(music, loops, ms)

def Mix_FadeOutMusic(ms):
    return _mix_lib.Mix_FadeOutMusic(ms)

def Mix_FadeInChannel(channel, chunk, loops, ms):
    return _mix_lib.Mix_FadeInChannel(channel, chunk, loops, ms)

def Mix_FadeOutChannel(channel, ms):
    return _mix_lib.Mix_FadeOutChannel(channel, ms)

def Mix_Playing(channel):
    return _mix_lib.Mix_Playing(channel)

def Mix_PlayingMusic():
    return _mix_lib.Mix_PlayingMusic()

def Mix_Paused(channel):
    return _mix_lib.Mix_Paused(channel)

def Mix_PausedMusic():
    return _mix_lib.Mix_PausedMusic()

def Mix_SetPanning(channel, left, right):
    return _mix_lib.Mix_SetPanning(channel, left, right)

def Mix_SetDistance(channel, distance):
    return _mix_lib.Mix_SetDistance(channel, distance)

def Mix_SetPosition(channel, angle, distance):
    return _mix_lib.Mix_SetPosition(channel, angle, distance)

def Mix_SetReverseStereo(channel, flip):
    return _mix_lib.Mix_SetReverseStereo(channel, flip)

# Set up function prototypes for Windows
if sys.platform.startswith('win32'):
    # SDL function prototypes
    _sdl_lib.SDL_Init.argtypes = [c_uint32]
    _sdl_lib.SDL_Init.restype = c_int
    
    _sdl_lib.SDL_InitSubSystem.argtypes = [c_uint32]
    _sdl_lib.SDL_InitSubSystem.restype = c_int
    
    _sdl_lib.SDL_Quit.argtypes = []
    _sdl_lib.SDL_Quit.restype = None
    
    _sdl_lib.SDL_QuitSubSystem.argtypes = [c_uint32]
    _sdl_lib.SDL_QuitSubSystem.restype = None
    
    _sdl_lib.SDL_WasInit.argtypes = [c_uint32]
    _sdl_lib.SDL_WasInit.restype = c_uint32
    
    _sdl_lib.SDL_GetError.argtypes = []
    _sdl_lib.SDL_GetError.restype = c_char_p
    
    _sdl_lib.SDL_RWFromFile.argtypes = [c_char_p, c_char_p]
    _sdl_lib.SDL_RWFromFile.restype = c_void_p
    
    _sdl_lib.SDL_Delay.argtypes = [c_uint32]
    _sdl_lib.SDL_Delay.restype = None

    # SDL_mixer function prototypes
    _mix_lib.Mix_OpenAudio.argtypes = [c_int, c_uint16, c_int, c_int]
    _mix_lib.Mix_OpenAudio.restype = c_int
    
    _mix_lib.Mix_CloseAudio.argtypes = []
    _mix_lib.Mix_CloseAudio.restype = None
    
    _mix_lib.Mix_QuerySpec.argtypes = [ctypes.POINTER(c_int),
                                     ctypes.POINTER(c_uint16),
                                     ctypes.POINTER(c_int)]
    _mix_lib.Mix_QuerySpec.restype = c_int
    
    _mix_lib.Mix_LoadWAV_RW.argtypes = [c_void_p, c_int]
    _mix_lib.Mix_LoadWAV_RW.restype = ctypes.POINTER(Mix_Chunk)
    
    _mix_lib.Mix_LoadMUS_RW.argtypes = [c_void_p, c_int]
    _mix_lib.Mix_LoadMUS_RW.restype = c_void_p
    
    _mix_lib.Mix_FreeChunk.argtypes = [ctypes.POINTER(Mix_Chunk)]
    _mix_lib.Mix_FreeChunk.restype = None
    
    _mix_lib.Mix_FreeMusic.argtypes = [c_void_p]
    _mix_lib.Mix_FreeMusic.restype = None
    
    _mix_lib.Mix_PlayChannel.argtypes = [c_int, ctypes.POINTER(Mix_Chunk), c_int]
    _mix_lib.Mix_PlayChannel.restype = c_int
    
    _mix_lib.Mix_PlayMusic.argtypes = [c_void_p, c_int]
    _mix_lib.Mix_PlayMusic.restype = c_int
    
    _mix_lib.Mix_Pause.argtypes = [c_int]
    _mix_lib.Mix_Pause.restype = None
    
    _mix_lib.Mix_PauseMusic.argtypes = []
    _mix_lib.Mix_PauseMusic.restype = None
    
    _mix_lib.Mix_Resume.argtypes = [c_int]
    _mix_lib.Mix_Resume.restype = None
    
    _mix_lib.Mix_ResumeMusic.argtypes = []
    _mix_lib.Mix_ResumeMusic.restype = None
    
    _mix_lib.Mix_HaltChannel.argtypes = [c_int]
    _mix_lib.Mix_HaltChannel.restype = c_int
    
    _mix_lib.Mix_HaltMusic.argtypes = []
    _mix_lib.Mix_HaltMusic.restype = c_int
    
    _mix_lib.Mix_SetMusicPosition.argtypes = [c_double]
    _mix_lib.Mix_SetMusicPosition.restype = c_int
    
    if hasattr(_mix_lib, 'Mix_MusicDuration'):
        _mix_lib.Mix_MusicDuration.argtypes = [c_void_p]
        _mix_lib.Mix_MusicDuration.restype = c_float
    
    _mix_lib.Mix_Volume.argtypes = [c_int, c_int]
    _mix_lib.Mix_Volume.restype = c_int
    
    _mix_lib.Mix_VolumeMusic.argtypes = [c_int]
    _mix_lib.Mix_VolumeMusic.restype = c_int
    
    _mix_lib.Mix_AllocateChannels.argtypes = [c_int]
    _mix_lib.Mix_AllocateChannels.restype = c_int
    
    _mix_lib.Mix_GetMusicType.argtypes = [c_void_p]
    _mix_lib.Mix_GetMusicType.restype = c_int
    
    _mix_lib.Mix_FadingMusic.argtypes = []
    _mix_lib.Mix_FadingMusic.restype = c_int
    
    _mix_lib.Mix_FadeInMusic.argtypes = [c_void_p, c_int, c_int]
    _mix_lib.Mix_FadeInMusic.restype = c_int
    
    _mix_lib.Mix_FadeOutMusic.argtypes = [c_int]
    _mix_lib.Mix_FadeOutMusic.restype = c_int
    
    _mix_lib.Mix_FadeInChannel.argtypes = [c_int, ctypes.POINTER(Mix_Chunk), c_int, c_int]
    _mix_lib.Mix_FadeInChannel.restype = c_int
    
    _mix_lib.Mix_FadeOutChannel.argtypes = [c_int, c_int]
    _mix_lib.Mix_FadeOutChannel.restype = c_int
    
    _mix_lib.Mix_Playing.argtypes = [c_int]
    _mix_lib.Mix_Playing.restype = c_int
    
    _mix_lib.Mix_PlayingMusic.argtypes = []
    _mix_lib.Mix_PlayingMusic.restype = c_int
    
    _mix_lib.Mix_Paused.argtypes = [c_int]
    _mix_lib.Mix_Paused.restype = c_int
    
    _mix_lib.Mix_PausedMusic.argtypes = []
    _mix_lib.Mix_PausedMusic.restype = c_int
    
    _mix_lib.Mix_SetPanning.argtypes = [c_int, c_uint8, c_uint8]
    _mix_lib.Mix_SetPanning.restype = c_int
    
    _mix_lib.Mix_SetDistance.argtypes = [c_int, c_uint8]
    _mix_lib.Mix_SetDistance.restype = c_int
    
    _mix_lib.Mix_SetPosition.argtypes = [c_int, c_uint16, c_uint8]
    _mix_lib.Mix_SetPosition.restype = c_int
    
    _mix_lib.Mix_SetReverseStereo.argtypes = [c_int, c_int]
    _mix_lib.Mix_SetReverseStereo.restype = c_int

# Set up SDL_Delay parameters and return type
_sdl_lib.SDL_Delay.argtypes = [ctypes.c_uint32]
_sdl_lib.SDL_Delay.restype = None

class AudioLibrary:
    def __init__(self, frequency: int = 44100, format: int = MIX_DEFAULT_FORMAT,
                 channels: int = 2, chunksize: int = 2048):
        """Initialize the audio library"""
        # Initialize SDL audio
        if SDL_Init(SDL_INIT_AUDIO) != 0:
            raise RuntimeError(f"SDL initialization failed")
        
        if Mix_OpenAudio(frequency, format, channels, chunksize) != 0:
            raise RuntimeError(f"Mixer initialization failed")
        
        # Audio state tracking
        self._audio_cache = {}  # File path -> Mix_Chunk
        self._music_cache = {}  # File path -> Mix_Music
        self._channel_info = {}  # Channel ID -> Playback info
        self._aid_to_filepath = {}  # Store AID to file mapping
        self._aid_counter = 0
        self._sample_rate = frequency
        self._format = format
        self._channels = channels
        
        # Initialize DAP recordings list
        self._dap_recordings = []  # List of DAP format recordings

    def Delay(self, ms):
        _sdl_lib.SDL_Delay(ms)

    # Core playback functionality ======================================================
    def play_audio(self, aid: int) -> None:
        """Play/resume audio with specified AID"""
        channel = self._find_channel_by_aid(aid)
        if channel is None:
            raise ValueError("Invalid AID")
        
        info = self._channel_info[channel]
        if info['paused']:
            if info['is_music']:
                Mix_ResumeMusic()
            else:
                Mix_Resume(channel)
            info['paused'] = False
            info['start_time'] = time.time() - info['paused_position']
    # DAP recording functionality ======================================================
    
    def play_from_file(self, file_path: str, loops: int = 0, start_pos: float = 0.0) -> int:
        """
        Play audio directly from file, return AID.
        For .ap-ds-dap files: ONLY RECORD METADATA, NO PLAYBACK.
        
        Args:
            file_path: Path to audio file
            loops: Number of loops (ignored for DAP files)
            start_pos: Starting position (ignored for DAP files)
            
        Returns:
            int: Audio ID (AID)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Generate AID
        self._aid_counter += 1
        aid = self._aid_counter
        
        # Record to DAP list without playing
        self._add_to_dap_recordings(file_path)
        self._aid_to_filepath[aid] = file_path

        # Normal audio file playback (MP3, OGG, FLAC, WAV)
        # Music file handling
        if self._is_music_file(file_path):
            music = Mix_LoadMUS(file_path.encode())
            if not music:
                raise RuntimeError(f"Failed to load music file")
            
            if Mix_PlayMusic(music, loops) != 0:
                Mix_FreeMusic(music)
                raise RuntimeError(f"Failed to play music")
            
            channel = -1
            self._music_cache[file_path] = music
        
        # Sound effect handling
        else:
            audio = Mix_LoadWAV(file_path.encode())
            if not audio:
                raise RuntimeError(f"Failed to load audio file")
            
            channel = Mix_PlayChannel(-1, audio, loops)
            if channel == -1:
                Mix_FreeChunk(audio)
                raise RuntimeError(f"Failed to play audio")
            
            self._audio_cache[file_path] = audio
        
        # Record playback information
        self._channel_info[channel] = {
            'aid': aid,
            'start_time': time.time() - start_pos,
            'paused': False,
            'file_path': file_path,
            'is_music': channel == -1,
            'loops': loops
        }
        
        # Seek to specified position
        if start_pos > 0:
            self._seek_audio(channel, start_pos)
        self._aid_to_filepath[aid] = file_path
        
        return aid
    
    def play_from_memory(self, file_path: str, loops: int = 0, start_pos: float = 0.0) -> int:
        """
        Play audio from memory cache, return AID.

        Args:
            file_path: Path to audio file
            loops: Number of loops (ignored for DAP files)
            start_pos: Starting position (ignored for DAP files)
            
        Returns:
            int: Audio ID (AID)
        """
        # Generate AID
        self._aid_counter += 1
        aid = self._aid_counter
        

        # Record to DAP list without playing
        self._add_to_dap_recordings(file_path)
        self._aid_to_filepath[aid] = file_path

        # Normal audio file playback
        if file_path in self._music_cache:
            if Mix_PlayMusic(self._music_cache[file_path], loops) != 0:
                raise RuntimeError(f"Failed to play music")
            channel = -1
        elif file_path in self._audio_cache:
            channel = Mix_PlayChannel(-1, self._audio_cache[file_path], loops)
            if channel == -1:
                raise RuntimeError(f"Failed to play audio")
        else:
            raise ValueError("Audio not loaded in memory")
        
        # Record playback information
        self._channel_info[channel] = {
            'aid': aid,
            'start_time': time.time() - start_pos,
            'paused': False,
            'file_path': file_path,
            'is_music': channel == -1,
            'loops': loops
        }
        
        if start_pos > 0:
            self._seek_audio(channel, start_pos)
        self._aid_to_filepath[aid] = file_path
        
        return aid
    
    def new_aid(self, file_path: str) -> int:
        """
        Generate AID for file. 
        
        Args:
            file_path: Path to audio file
            
        Returns:
            int: Audio ID (AID)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Generate AID
        self._aid_counter += 1
        aid = self._aid_counter
        

        # Record to DAP list without loading
        self._add_to_dap_recordings(file_path)
        self._aid_to_filepath[aid] = file_path

        # Normal audio file loading
        if self._is_music_file(file_path):
            if file_path not in self._music_cache:
                music = Mix_LoadMUS(file_path.encode())
                if not music:
                    raise RuntimeError(f"Failed to load music file")
                self._music_cache[file_path] = music
        else:
            if file_path not in self._audio_cache:
                audio = Mix_LoadWAV(file_path.encode())
                if not audio:
                    raise RuntimeError(f"Failed to load audio file")
                self._audio_cache[file_path] = audio
        
        self._aid_to_filepath[aid] = file_path
        
        return aid
    
    def _add_to_dap_recordings(self, file_path: str) -> None:
        """
        Add .ap-ds-dap file metadata to memory list. NO FILE LOADING.
        
        Args:
            file_path
        """

        # Get metadata using audio_parser (only reads metadata, doesn't load file)
        metadata = self.get_audio_metadata_by_path(file_path)
            
        if metadata:
            # Create DAP record
            dap_record = {
                'path': file_path,
                'duration': metadata.get('duration', 0),      # from metadata function
                'bitrate': metadata.get('bitrate', 0),       # from metadata function
                'channels': metadata.get('channels', 2)      # from metadata function
                }
                
            # Add to memory list if not already present
            if not any(entry['path'] == file_path for entry in self._dap_recordings):
                self._dap_recordings.append(dap_record)
                print(f"📝 Recorded DAP file: {file_path}")
    
    def save_dap_to_json(self, save_path: str) -> bool:
        """
        Save DAP recordings to JSON file. ONLY WHEN USER CALLS THIS FUNCTION.
        
        Args:
            save_path: Path to save JSON file
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If file extension is not .ap-ds-dap
        """
        try:
            # Validate file extension
            if not save_path.lower().endswith('.ap-ds-dap'):
                raise ValueError(
                    f"Invalid file extension. Expected '.ap-ds-dap' but got '{os.path.splitext(save_path)[1]}'"
                )
            
            # Save to JSON with UTF-8 encoding
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._dap_recordings, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Saved {len(self._dap_recordings)} DAP records to: {save_path}")
            return True
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error saving DAP to JSON: {str(e)}")
            return False
    
    def get_dap_recordings(self) -> List[Dict]:
        """
        Get current DAP recordings from memory.
        
        Returns:
            List[Dict]: List of DAP records
        """
        return self._dap_recordings.copy()
    
    def clear_dap_recordings(self) -> None:
        """Clear all DAP recordings from memory."""
        self._dap_recordings.clear()
        print("🗑️ Cleared all DAP recordings")
    def _is_music_file(self, file_path: str) -> bool:
        """
        Check if file is a music file format.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            bool: True if music file (MP3, OGG, FLAC), False if other (WAV, etc.)
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.mp3', '.ogg', '.flac']
    # Control functionality ======================================================
    
    def pause_audio(self, aid: int) -> None:
        """Pause audio with specified AID"""
        channel = self._find_channel_by_aid(aid)
        if channel is None:
            raise ValueError("Invalid AID")
        
        info = self._channel_info[channel]
        if not info['paused']:
            if info['is_music']:
                Mix_PauseMusic()
            else:
                Mix_Pause(channel)
            info['paused'] = True
            info['paused_position'] = time.time() - info['start_time']

    def stop_audio(self, aid: int) -> float:
        """Stop playback and return played duration"""
        channel = self._find_channel_by_aid(aid)
        if channel is None:
            return 0.0
        
        info = self._channel_info[channel]
        played_time = time.time() - info['start_time'] if not info['paused'] else info['paused_position']
        
        if info['is_music']:
            Mix_HaltMusic()
        else:
            Mix_HaltChannel(channel)
        
        del self._channel_info[channel]
        return played_time

    def seek_audio(self, aid: int, position: float) -> None:
        """Seek to specified position (seconds)"""
        channel = self._find_channel_by_aid(aid)
        if channel is not None:
            self._seek_audio(channel, position)

    def _seek_audio(self, channel: int, position: float) -> None:
        """Internal method: seek audio"""
        info = self._channel_info.get(channel)
        if not info:
            return
        
        # Music seeking
        if info['is_music']:
            Mix_HaltMusic()
            music = Mix_LoadMUS(info['file_path'].encode())
            if Mix_PlayMusic(music, info['loops']) != 0:
                Mix_FreeMusic(music)
                return
            
            if hasattr(Mix_SetMusicPosition, '__call__'):
                Mix_SetMusicPosition(position)
            
            self._music_cache[info['file_path']] = music
            self._channel_info[channel] = {
                **info,
                'start_time': time.time() - position,
                'paused': False
            }
        # Sound effect seeking
        else:
            Mix_HaltChannel(channel)
            audio = self._audio_cache.get(info['file_path'])
            new_channel = Mix_PlayChannel(-1, audio, info['loops'])
            
            self._channel_info[new_channel] = {
                **info,
                'start_time': time.time() - position,
                'paused': False
            }
            del self._channel_info[channel]


    def set_volume(self, aid: int, volume: int) -> bool:
        """Set audio volume
    
        Args:
            aid: Audio ID
            volume: Volume value (0-128)
    
        Returns:
            bool: Whether the setting was successful
        """
        channel = self._find_channel_by_aid(aid)
        if channel is None:
            return False
    
        info = self._channel_info[channel]
        volume = max(0, min(128, volume))  # Ensure volume is within 0-128 range
    
        if info['is_music']:
            return Mix_VolumeMusic(volume) == volume
        else:
            return Mix_Volume(channel, volume) == volume

    def get_volume(self, aid: int) -> int:
        """Get current audio volume
    
        Args:
            aid: Audio ID
    
        Returns:
            int: Current volume value (0-128)
        """
        channel = self._find_channel_by_aid(aid)
        if channel is None:
            return 0
    
        info = self._channel_info[channel]
        if info['is_music']:
            return Mix_VolumeMusic(-1)  # -1 means get without setting
        else:
            return Mix_Volume(channel, -1)  # -1 means get without setting


    # Helper methods ======================================================
    
    def _find_channel_by_aid(self, aid: int) -> Optional[int]:
        """Find channel by AID"""
        for channel, info in self._channel_info.items():
            if info['aid'] == aid:
                return channel
        return None

    
    def _get_file_path_by_aid(self, aid: int) -> Optional[str]:
        """Get file path by AID"""
        for info in self._channel_info.values():
            if info['aid'] == aid:
                return info['file_path']
        return None
    

    def get_audio_duration(self, source: Union[str, int], is_file: bool = False) -> Union[int, Tuple[int, str]]:
        """
        Get the duration of an audio file in seconds
        
        This method supports both file paths and AID (Audio ID) as input sources.
        It automatically detects the file format and uses the appropriate parser
        to calculate the duration accurately.
        
        Args:
            source: Either a file path string or an integer AID
            is_file: If True, treats source as file path; if False, as AID
            
        Returns:
            Union[int, Tuple[int, str]]: 
                - On success: Integer duration in seconds (rounded)
                - On failure: Tuple (0, error_message_string)
                
        Examples:
            >>> # Get duration by file path
            >>> duration = lib.get_audio_duration("audio/song.mp3", is_file=True)
            >>> # Get duration by AID
            >>> duration = lib.get_audio_duration(123, is_file=False)
        """
        try:
            # Case 1: Get duration by AID (Audio ID)
            if not is_file and isinstance(source, int):
                if source not in self._aid_to_filepath:
                    return (0, f"Invalid AID: {source}")
                
                file_path = self._aid_to_filepath[source]
                return self._get_duration_by_filepath(file_path)
            
            # Case 2: Get duration by file path
            file_path = str(source)
            return self._get_duration_by_filepath(file_path)
            
        except Exception as e:
            return (0, f"Error getting audio duration: {str(e)}")

    def _get_duration_by_filepath(self, file_path: str) -> Union[int, Tuple[int, str]]:
        try:
            if not os.path.exists(file_path):
                return (0, f"File not found: {file_path}")
        
            if AUDIO_PARSER_AVAILABLE:
                try:
                    parser = get_audio_parser()
                    duration = parser.get_audio_duration(file_path)
                    if duration > 0:
                        return duration
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext == '.mp3':
                        duration = parser.get_mp3_duration(file_path)
                    elif file_ext == '.ogg':
                        duration = parser.get_ogg_duration(file_path)
                    elif file_ext == '.flac':
                        duration = parser.get_flac_duration(file_path)
                    elif file_ext == '.wav':
                        duration = parser.get_wav_duration(file_path)
                    
                    if duration > 0:
                        return duration
                except Exception as e:
                    print(f"Audio parser DLL error: {e}")
            
        except Exception as e:
            return (0, f"Error calculating audio duration: {str(e)}")
    
    def simple_mp3_duration_estimation(self, filename: str) -> float:
        """
        Estimate MP3 duration based on file size and common bitrates
        
        This provides a fallback when frame-by-frame parsing fails.
        
        Args:
            filename: Path to the MP3 file
            
        Returns:
            float: Estimated duration in seconds, 0 on error
        """
        try:
            file_size = os.path.getsize(filename)
            
            # Estimate audio data size (subtract possible ID3 tag)
            audio_data_size = max(file_size - 2048, file_size * 0.98)
            
            # Estimate bitrate based on file size
            if file_size < 2 * 1024 * 1024:  # < 2MB
                bitrate = 128
            elif file_size < 5 * 1024 * 1024:  # < 5MB
                bitrate = 192
            elif file_size < 10 * 1024 * 1024:  # < 10MB
                bitrate = 256
            else:
                bitrate = 320
            
            # Calculate duration: (file_size_bytes * 8) / (bitrate_bps)
            duration = (audio_data_size * 8) / (bitrate * 1000)
            return duration
            
        except Exception as e:
            print(f"MP3 duration estimation error: {e}")
            return 0

    def get_audio_metadata_by_aid(self, aid: int) -> Optional[Dict]:
        """
        Obtain complete metadata of audio files based on AID
            
        Args:
        Aid: Audio ID
                
        Returns:
        Dict: Dictionary containing complete audio metadata, failure returns None
        Contains fields: path, format, duration, length, sample_rate, channels, bitrate
                
        Raises:
        ValueError: thrown when AID is invalid
        """
        try:
            if aid not in self._aid_to_filepath:
                raise ValueError(f"Invalid AID: {aid}")
            
            file_path = self._aid_to_filepath[aid]
            
            if AUDIO_PARSER_AVAILABLE:
                parser = get_audio_parser()
                return parser.get_audio_metadata(file_path)
                
        except Exception as e:
            print(f"Error getting audio metadata by AID: {str(e)}")
            return None

    def get_audio_metadata_by_path(self, file_path: str) -> Optional[Dict]:
        """
        Directly obtain the complete metadata of an audio file based on its file path
    
        Args:
            file_path: Audio file path
            
        Returns:
            dict: a dictionary containing complete audio metadata, returns None on failure
            Fields included: path, format, duration, length, sample_rate, channels, bitrate

        """
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None
            
            if AUDIO_PARSER_AVAILABLE:
                parser = get_audio_parser()
                return parser.get_audio_metadata(file_path)
            
        except Exception as e:
            print(f"Error getting audio metadata by path: {str(e)}")
            return None
            

    def get_audio_metadata(self, source: Union[str, int], is_file: bool = False) -> Optional[Dict]:
        """
        Retrieve audio metadata based on AID (Audio Identifier) or audio file path.

        Args:
        
        Source: AID or audio file path.
                    
        Returns:
        
            Dict: Dictionary containing complete audio metadata, failure returns None
            Contains fields: path, format, duration, length, sample_rate, channels, bitrate
        """
        if is_file or isinstance(source, str):
            return self.get_audio_metadata_by_path(str(source))
        elif isinstance(source, int):
            return self.get_audio_metadata_by_aid(source)
        else:
            raise TypeError(f"Invalid source type: {type(source)}. Expected str or int.")
    def _get_sample_rate(self, source: Union[str, int]) -> int:
        """Get the actual sample rate from audio metadata.
        
        Args:
            source: Audio source (file path string or AID integer)
            
        Returns:
            int: Sample rate in Hz. Returns 44100 as fallback if metadata not available.
        """
        try:
            metadata = self.get_audio_metadata(source, is_file=isinstance(source, str))
            if metadata and 'sample_rate' in metadata:
                return metadata['sample_rate']
        except Exception:
            pass
        
        return 44100  # Fallback default value

    def _get_channels(self, source: Union[str, int]) -> int:
        """Get the actual channel count from audio metadata.
        
        Args:
            source: Audio source (file path string or AID integer)
            
        Returns:
            int: Number of audio channels. Returns 2 as fallback if metadata not available.
        """
        try:
            metadata = self.get_audio_metadata(source, is_file=isinstance(source, str))
            if metadata and 'channels' in metadata:
                return metadata['channels']
        except Exception:
            pass
        
        return 2  # Fallback default value
    def _get_aid_for_audio(self, file_path: str) -> Optional[int]:
        """Find corresponding AID by file path"""
        for channel, info in self._channel_info.items():
            if info.get('file_path') == file_path and not info.get('is_music', True):
                return info.get('aid')
        return None

    def _get_aid_for_music(self, file_path: str) -> Optional[int]:
        """Find corresponding AID by music file path"""
        for channel, info in self._channel_info.items():
            if info.get('file_path') == file_path and info.get('is_music', False):
                return info.get('aid')
        return None
    
    def _get_playing_duration(self, aid: int) -> float:
        """Get total duration of playing audio"""
        file_path = self._get_file_path_by_aid(aid)
        return self._get_file_duration(file_path) if file_path else 0.0
    def _get_file_duration(self, file_path: str) -> float:
        result = self._get_duration_by_filepath(file_path)
        if isinstance(result, tuple):
            return 0.0  
        return float(result)

    # Resource management ======================================================
    
    def clear_memory_cache(self) -> None:
        """Clear memory cache"""
        for audio in self._audio_cache.values():
            if audio:
                Mix_FreeChunk(audio)
        for music in self._music_cache.values():
            if music:
                Mix_FreeMusic(music)
        self._audio_cache.clear()
        self._music_cache.clear()

    def __del__(self):
        """Clean up resources"""
        self.clear_memory_cache()
        Mix_CloseAudio()
        SDL_Quit()
