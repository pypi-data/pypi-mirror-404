import os
import platform
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def get_ffmpeg_path():
    """Returns ffmpeg and ffprobe paths."""
    from shutil import which
    ffmpeg = which("ffmpeg")
    ffprobe = which("ffprobe")
    if not ffmpeg or not ffprobe:
        return None,None
    return ffmpeg, ffprobe

def escape_path_for_filter(path):
    """Escapes a file path for use in ffmpeg filtergraphs."""
    abs_path = os.path.abspath(path)
    escaped = abs_path.replace("\\", "/")
    if platform.system() == "Windows":
        escaped = escaped.replace(":", "\\:")
    return f"'{escaped}'"

def format_bytes(size_bytes):
    """Converts bytes to KB/MB/GB dynamically."""
    if size_bytes == 0: return "0B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_bytes >= 1024 and i < len(units)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{units[i]}"

def format_seconds_hms(seconds):
    """Converts float seconds to HH:MM:SS string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- Colored Output Helpers ---
def print_error(msg,end='\n'): print(f"{Fore.RED}{msg}",end=end)

def print_success(msg,end='\n',flush=False): print(f"{Fore.GREEN}{msg}",end=end,flush=flush)

def print_warning(msg,end='\n',flush=False): print(f"{Fore.YELLOW}{msg}",end=end,flush=flush)

def print_info(msg,end='\n'): print(f"{Fore.CYAN}{msg}",end=end)

def is_android():
    import sys
    return hasattr(sys, 'getandroidapilevel')
