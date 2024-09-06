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

# Template Image path on avatar_pipeline dir
full_template_image_path = os.path.join(os.getcwd(), TEMPLATE_IMAGE_PATH)


def run_sadtalker(sadTalker_dir, input_audio_path, image_path=full_template_image_path, output_path=OUTPUT_PATH, expression_scale=EXPRESSION_SCALE, ref_blink=None, ref_head=None):
    logger.info("Starting SadTalker processing")

    # Get command for setting CUDA environment
    cuda_env_command = helpers.get_cuda_env_path()

    # Get the conda source command dynamically
    conda_source_command = helpers.get_conda_source_command()

    # Prepare the full commands to be executed in the shell
    full_commands = [
        conda_source_command,
        cuda_env_command[0], 
        cuda_env_command[1], 
        f"cd {sadTalker_dir}",
        "pwd",
        "conda activate sadtalker", 
        "nvcc --version"
    ]

    # Construct the SadTalker inference command
    inference_command = [
        "python",
        SADTALKER_SCRIPT,
        "--driven_audio", input_audio_path,
        "--source_image", image_path,
        "--result_dir", output_path,
        "--still",
        "--preprocess", "full",  # Using 'full' for better quality
        "--expression_scale", str(expression_scale)
    ]

    # Add optional parameters if provided
    if ref_blink is not None:
        inference_command.extend(["--ref_eyeblink", ref_blink])
    if ref_head is not None:
        inference_command.extend(["--ref_pose", ref_head])

    # Join inference_command into a single string for logging
    inference_command_str = " ".join(inference_command)
    logger.info(inference_command_str)

    # Append the SadTalker command to the list of commands
    full_commands.append(inference_command_str)

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
