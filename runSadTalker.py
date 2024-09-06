import subprocess
import glob
import os
from datetime import datetime
import helpers
from config_manager import config
from logger import logger  # Import the logger

# Constants
SADTALKER_SCRIPT = config.get("SadTalker", "script")
CUDA_VERSION = config.get("SadTalker", "cuda_version")
EXPRESSION_SCALE = config.getfloat("SadTalker", "expression_scale")
TEMPLATE_IMAGE_PATH = config.get("SadTalker", "template_image")
REF_VIDEO_PATH = config.get("SadTalker", "ref_video")
OUTPUT_PATH = os.path.expanduser(config.get("SadTalker", "output_path"))

def run_sadtalker(sadTalker_dir, input_audio_path, image_path=TEMPLATE_IMAGE_PATH, output_path=OUTPUT_PATH, expression_scale=EXPRESSION_SCALE, ref_blink=None, ref_head=None):
    logger.info("Starting SadTalker processing")
    """
    Run the SadTalker model with the given inputs using WSL.
    
    reference doc: https://github.com/OpenTalker/SadTalker/blob/main/docs/best_practice.md
    configuration options:
    --driven_audio: Path to the input audio file
    --source_image: Path to the input image file
    --result_dir: Output directory (default: ./results)
    --still: Minimized head motion (default: False)
    --preprocess full: Makes video full image (default: crop) # full is better for LivePortrait
    --expression_scale: Expression scale factor (default: 1) # 1.1 is good
    # reference Mode for Blinking and Head Pose:
    --ref_eyeblink: video path(head). borrows eyeblink from this video    
    --ref_pose: video path(head). borrows head pose from this video    
    # noteworthy but not used:
    --enhancer: not necessary for LivePortrait
    --background_enhancer: not necessary for LivePortrait
    """

    # get command for setting cuda env
    cuda_env_command = helpers.get_cuda_env_path()

    full_commands = [helpers.get_conda_source_command(), 
                     cuda_env_command[0], cuda_env_command[1], 
                     f"cd {sadTalker_dir}","pwd", "conda activate sadtalker",  "nvcc --version"]

    # construct the command to run SadTalker
    inference_command = [
        "python",
        SADTALKER_SCRIPT,
        "--driven_audio", f'"{input_audio_path}"',
        "--source_image", f'"{image_path}"',
        "--result_dir", f'"{output_path}"',
        "--still",
        "--preprocess", "full", # TODO: do crop and handle full video using external code(faster)
        "--expression_scale", str(expression_scale)
    ]
    # add ref_blink and ref_head if they are not None
    if ref_blink is not None:
        inference_command.extend(["--ref_eyeblink", ref_blink])
    if ref_head is not None:
        inference_command.extend(["--ref_pose", ref_head])
    
    # Join wsl_command into a single string
    inference_command = " ".join(inference_command)
    logger.info(inference_command)
    
    # Add the SadTalker command to the list of WSL commands
    full_commands.append(inference_command)

    try:
        # Execute the commands in a shell
        helpers.run_commands(full_commands)
        
        # Look for mp4 files directly in the output path
        output_files = glob.glob(os.path.join(output_path, "*.mp4"))

        if not output_files:
            logger.error(f"No output files found in {output_path}")
            return False, None
        
        output_video_path = max(output_files, key=os.path.getctime)
        logger.info(f"SadTalker processing complete. Output saved to: {output_video_path}")

        return True, output_video_path
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running SadTalker: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error in run_sadtalker: {e}")
        return False, None

def main():
    print(os.getcwd())
    subprocess.run("echo 'Hello, World!'", shell=True)
    subprocess.run("cd ~/Projects/SadTalker", shell=True)
    subprocess.run("pwd", shell=True)
    subprocess.run("ls", shell=True)

if __name__ == "__main__":
    main()