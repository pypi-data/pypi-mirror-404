import subprocess
import sys
import time
import os
from colorama import Fore, Style
from .utils import (
    escape_path_for_filter,
    print_error,
    print_warning,
    print_info,
    format_bytes,
    format_seconds_hms,
    is_android
)


class VideoProcessor:
    def __init__(self, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe"):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path

    def get_total_duration(self, input_path):
        """Gets total duration of the input video."""
        cmd = [
            self.ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0.0

    def run_ffmpeg(self, args, input_path, filename, file_count, counter):
        """
        Runs FFmpeg.
        """
        cmd = [self.ffmpeg] + args
        cmd.extend(['-progress', 'pipe:1', '-nostats', '-v', 'error'])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            total_duration = self.get_total_duration(input_path)

            # --- Spinner Setup ---
            spinners = ['|', '/', '-', '\\']
            spinner_idx = 0

            print_info(f"<< ",end='')
            print(f"{filename}")

            if file_count > 1:
                print(f"{Fore.GREEN}{counter}{Style.RESET_ALL} of {Fore.BLUE}{file_count}{Style.RESET_ALL}")
            else:
                print()

            # If duration is 0
            if total_duration == 0.0:
                print_error("Duration unknown.File Error")
                return False

            else:
                current_time = 0.0
                total_size = 0
                start_clock = time.time()
                last_display_time = 0

                while True:
                    if process.stdout:
                        line = process.stdout.readline()

                    if not line and process.poll() is not None:
                        break

                    if '=' in line:
                        key, value = line.strip().split('=', 1)

                        if key == 'out_time_us':
                            current_time = int(value) / 1_000_000

                        elif key == 'total_size':
                            total_size = int(value)

                        elif key == 'progress' and value == 'end':
                            percent = 100
                            elapsed_wall_clock = time.time() - start_clock
                            size_str = format_bytes(total_size)
                            cur_str = format_seconds_hms(current_time)

                            if is_android():
                                status = (
                                    f"{cur_str} {Fore.YELLOW}{size_str:>9}{Style.RESET_ALL}"
                                    f"{Fore.GREEN}{percent:>8}%{Style.RESET_ALL}   "
                                    f"✓ {elapsed_str}"
                                )
                            else:
                                status = (
                                    f"[ {Fore.GREEN}✓{Style.RESET_ALL} ] "
                                    f"Size: {Fore.YELLOW}{size_str:>9}{Style.RESET_ALL}    {"Time: "}{cur_str}/{tot_str}"
                                    f"{Fore.GREEN}{percent:>8}%{Style.RESET_ALL}    "
                                    f"{"Elapsed: "}{elapsed_str}"
                                )

                            print(f"\r{status}", end='')
                            break

                    # Update display every 0.5s
                    now = time.time()
                    if (now - last_display_time > 0.5) and (current_time > 0):
                        last_display_time = now
                        elapsed_wall_clock = now - start_clock
                        percent = (current_time / total_duration) * 100

                        cur_str = format_seconds_hms(current_time)
                        tot_str = format_seconds_hms(total_duration)
                        elapsed_str = format_seconds_hms(elapsed_wall_clock)

                        size_str = format_bytes(total_size)
                        spinner_idx = (spinner_idx + 1) % 4
                        spinner = spinners[spinner_idx]

                        if is_android():
                            # Time | Size | % | Spinner | Elapsed
                            status = (
                                f"{cur_str} {Fore.YELLOW}{size_str:>9}{Style.RESET_ALL}"
                                f"{Fore.GREEN}{percent:>8.1f}%{Style.RESET_ALL}   "
                                f"{Fore.BLUE}{spinner}{Style.RESET_ALL} {elapsed_str}"
                            )

                        else:
                            # Spinner | Size | Time/Total | % | Elapsed
                            status = (
                                f"[ {Fore.BLUE}{spinner}{Style.RESET_ALL} ] "
                                f"Size: {Fore.YELLOW}{size_str:>9}{Style.RESET_ALL}    {"Time: "}{cur_str}/{tot_str}"
                                f"{Fore.GREEN}{percent:>8.1f}%{Style.RESET_ALL}    "
                                f"{"Elapsed: "}{elapsed_str}"
                            )

                        print(f"\r{status}", end='')
                        sys.stdout.flush()

                print()

            # --- Check Result ---
            if process.returncode is None:
                process.wait()

            if process.returncode == 0:
                return True
            else:
                if process.stderr:
                    stderr_output = process.stderr.read()
                    print_error(f"FFmpeg exited with error code")
                    print_warning(f"{stderr_output}")
                return False

        except KeyboardInterrupt:
            process.kill()
            raise

        except Exception as e:
            print_error(f"Error occured while processing file")
            print_error(f"{e}")
            if process.poll() is None:
                process.kill()
            return False

    def construct_commands(self, input_path, output_config, options):
        """
        Constructs the ffmpeg argument list.Returns a list.
        """
        a_idx = options.get('aindex')
        audio_map = ['-map', f'0:a:{a_idx}']

        # --- Burn Logic ---
        vf_filter = ""
        if options.get('burn'):
            burn_val = options['burn']
            if burn_val == 'DEFAULT':
                sub_path = escape_path_for_filter(input_path)
                vf_filter = f"subtitles={sub_path}"
            elif os.path.exists(burn_val):
                sub_path = escape_path_for_filter(burn_val)
                vf_filter = f"subtitles={sub_path}"
            else:
                sub_path = escape_path_for_filter(input_path)
                vf_filter = f"subtitles={sub_path}:si={burn_val}"

        if options.get('audio_only'):
            output_file = output_config['audio']
            cmd = ['-y', '-i', input_path]
            cmd.extend([
                '-vn',
                '-c:a', 'aac',
                '-b:a', '128k',
                *audio_map
            ])
            cmd.append(output_file)

        else:
            output_file = output_config['video']
            cmd = ['-y', '-i', input_path, '-map', '0:v:0']

            if options.get('skip_video'):
                cmd.extend(['-c:v', 'copy'])
            else:
                crf_val = options.get('crf')
                cmd.extend([
                    '-c:v', 'libx264',
                    '-crf', str(crf_val),
                    '-preset', 'veryfast',
                    '-pix_fmt', 'yuv420p',
                    '-color_range', 'tv'
                ])
                if vf_filter: cmd.extend(['-vf', vf_filter])

            cmd.extend([
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ac', '2',
                '-af', 'loudnorm=I=-16:LRA=5:TP=-1.5',
                *audio_map
            ])
            cmd.append(output_file)

        return cmd