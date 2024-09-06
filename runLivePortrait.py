import subprocess
import glob
import os
from datetime import datetime
import helpers
import shutil
from config_manager import config
from logger import logger  # Import the logger

LIVEPORTRAIT_SCRIPT = config.get("LivePortrait", "script")
OUTPUT_DIR = config.get("LivePortrait", "output_dir")

def run_liveportrait(root_dir, input_image_path, input_video_path, output_dir):
    logger.info("Starting LivePortrait processing")
    LivePortrait_output_dir = os.path.join(root_dir, OUTPUT_DIR)
    # get command for setting cuda env
    cuda_env_command = helpers.get_cuda_env_path()

    full_commands = [helpers.get_conda_source_command(), 
                     cuda_env_command[0], cuda_env_command[1], 
                     f"cd {root_dir}", "conda activate liveportrait",  "nvcc --version"]

    # construct the command to run LivePortrait
    inference_command = [
        "python",
        LIVEPORTRAIT_SCRIPT,
        "-s", f'"{input_image_path}"',
        "-d", f'"{input_video_path}"',
        "-o", f'"{LivePortrait_output_dir}"',
        "--flag_crop_driving_video"
    ]

    # Join inference_command into a single string
    inference_command = " ".join(inference_command)

    # Add the inference command to the list of WSL commands
    full_commands.append(inference_command) 

    try:
        # Execute the commands in a shell
        helpers.run_commands(full_commands)
        # get the latest file in the output directory
        s_filename = os.path.splitext(os.path.basename(input_image_path))[0]
        d_filename = os.path.splitext(os.path.basename(input_video_path))[0]
        logger.info(f"s_filename: {s_filename}, d_filename: {d_filename}")
        output_video_path = get_output_video_path(LivePortrait_output_dir, s_filename, d_filename)
        shutil.move(output_video_path, output_dir)
        output_path = os.path.join(output_dir, os.path.basename(output_video_path))


        logger.info(f"LivePortrait processing complete. Output saved to: {output_video_path}")
        return True, output_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running LivePortrait: {e}")
        return False, None

# returns the path of output video file(latest file in output directory)
def get_output_video_path(output_dir, s_filename, d_filename):
    try:
        file_name = f"{s_filename}--{d_filename}"
        files = sorted(glob.glob(os.path.join(output_dir, '*')), key=os.path.getmtime, reverse=True)
        logger.info(output_dir)
        logger.info(f"Files(1) in output directory: {files}")
        
        for file in files:
            if file.endswith('_concat.mp4'):
                concat_dir = os.path.join(output_dir, 'concat')
                os.makedirs(concat_dir, exist_ok=True)
                shutil.move(file, concat_dir)
                logger.info(f"Moved file to: {os.path.join(concat_dir, os.path.basename(file))}")

        files = sorted(glob.glob(os.path.join(output_dir, '*')), key=os.path.getmtime, reverse=True)
        logger.info(f"Files(2) in output directory: {files}")

        for file in files:
            if os.path.basename(file) == file_name:
                return file
            elif s_filename in os.path.basename(file):
                return file
        
        logger.warning("No suitable output file found.")
        return None
    except Exception as e:
        logger.error(f"Error in get_output_video_path: {e}")
        return None



