import argparse
import sys
import os
from glob import glob
from .core import VideoProcessor
from .utils import (
    get_ffmpeg_path,
    print_error,
    print_warning,
    print_success
)

def main():
    try:
        parser = argparse.ArgumentParser(
            usage="revidx INPUTFILES ... [OPTIONS]",
            description="reVidx: Convert HEVC to AVC and Audio to MP3/AAC.",
            epilog="Requires 'ffmpeg' and 'ffprobe'.\n"
            "Docs & issues: https://github.com/voidsnax/reVidx",
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser.add_argument('inputfiles', nargs='+', help='Input video files')
        parser.add_argument('-o',metavar='PATH/NAME' ,nargs='?', const=None, help='Output directory or filename')
        parser.add_argument('-skip', action='store_true', help='Skip video encoding (copy)')
        parser.add_argument('-burn', metavar='INDEX/PATH',nargs='?', const='DEFAULT', help='Burn subtitles into the video (default: 0)')
        parser.add_argument('-aindex', metavar='INDEX',type=int, help='Audio index (default: 0)')
        parser.add_argument('-audio', action='store_true', help='Extract only audio to AAC')
        parser.add_argument('-crf', metavar='VALUE',type=float, help='CRF value (default: 20)')

        args = parser.parse_args()

        # Check Dependencies
        ffmpeg_path, ffprobe_path = get_ffmpeg_path()
        if not ffmpeg_path or not ffprobe_path:
            print_error("'ffmpeg' and 'ffprobe' not found.")
            sys.exit(1)

        processor = VideoProcessor(ffmpeg_path, ffprobe_path)

        multi_input = len(args.inputfiles) > 1
        if multi_input and args.burn != 'DEFAULT':
            print_error("Cannot provide subtitle stream for multiple inputs.")
            print_warning("Leave it empty for using the default.")
            sys.exit(1)

        # Options
        options = {
            'skip_video': args.skip,
            'burn': args.burn,
            'aindex': args.aindex if args.aindex is not None else 0,
            'audio_only': args.audio,
            'crf': args.crf if args.crf is not None else 20
        }

        if multi_input and args.burn:
            print_warning("Processing multiple files with -burn. Default subtitles used.")

        input_files = []
        counter = 0

        for input_arg in args.inputfiles:
            input_files.extend(glob(input_arg))
        if not input_files:
            print_error(f"No valid files found")
            sys.exit(1)

        total_files = len(input_files)

        # Process
        for file in input_files:
            if os.path.isdir(file):
                print_error(f"{file} is a directory")
                sys.exit(1)

            counter += 1
            base_name = os.path.splitext(os.path.basename(file))[0]

            output_video_path = ""
            output_audio_path = ""

            if args.o:
                if multi_input:
                    if not os.path.isdir(args.o):
                        print_error(f"With multiple inputs, -o must be a directory.")
                        sys.exit(1)
                    out_dir = args.o
                    output_video_path = os.path.join(out_dir, f"{base_name}-AvcMp3.mp4")
                    output_audio_path = os.path.join(out_dir, f"{base_name}.aac")
                else:
                    if os.path.isdir(args.o):
                        output_video_path = os.path.join(args.o, f"{base_name}-AvcMp3.mp4")
                        output_audio_path = os.path.join(args.o, f"{base_name}.aac")
                    else:
                        if args.audio and not args.burn:
                            output_audio_path = args.o
                            output_video_path = None
                        else:
                            output_video_path = args.o
                            if args.audio:
                                output_audio_path = os.path.splitext(args.o)[0] + ".aac"
            else:
                output_video_path = f"{base_name}-AvcMp3.mp4"
                output_audio_path = f"{base_name}.aac"

            output_config = {
                'video': output_video_path,
                'audio': output_audio_path
            }

            cmd = processor.construct_commands(file, output_config, options)

            out_file = cmd[-1]
            # print(*cmd)
            success = processor.run_ffmpeg(cmd, file, os.path.basename(file), total_files, counter)

            if success:
                print_success(f">> ",end='')
                print(f"{out_file}")
            else:
                print_error(f">> ",end='')
                print(f"{out_file}")

            if not counter == total_files:
                print()

    except KeyboardInterrupt:
        print_warning("\n>> ",end='')
        print(f"{out_file}")
        print_error("\nProcess Aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()