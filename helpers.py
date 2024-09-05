import os
import shutil
from pydub import AudioSegment
import subprocess
from datetime import datetime
from config_manager import config
from logger import logger  # Import the logger
import csv

# CONSTANTS
HOME_DIR = config.get("Paths", "HOME_DIR")
SILENCE_TIME = config.get("Values", "SILENCE_TIME")
DEFAULT_CUDA_VERSION = config.get("Values", "default_cuda_version")

# Function to find a specific directory in given search paths
def find_directory(dir_name, search_paths):
    for path in search_paths:
        full_path = os.path.join(path, dir_name)
        if os.path.isdir(full_path):
            return full_path
    return None

# Function to get the necessary directory paths
def get_directories():
    # Get the current script's path and its parent directories
    script_path = os.path.abspath(__file__)
    pipeline_dir = os.path.dirname(script_path)
    parent_dir = os.path.dirname(pipeline_dir)

    # Define search paths for SadTalker and LivePortrait directories
    search_paths = [HOME_DIR, parent_dir]

    # Find SadTalker and LivePortrait directories
    sadTalker_dir = find_directory("SadTalker", search_paths)
    livePortrait_dir = find_directory("LivePortrait", search_paths)

    # Raise exceptions if directories are not found
    if not sadTalker_dir:
        raise FileNotFoundError("SadTalker directory not found in the specified locations.")
    if not livePortrait_dir:
        raise FileNotFoundError("LivePortrait directory not found in the specified locations.")

    return parent_dir, pipeline_dir, sadTalker_dir, livePortrait_dir

def get_pipeline_directories(pipeline_dir):
    # Define input and output directories
    mp3_dir = os.path.join(pipeline_dir, "input_audio_mp3")
    wav_dir = os.path.join(pipeline_dir, "input_audio_wav")
    img_dir = os.path.join(pipeline_dir, "input_image")
    int_dir = os.path.join(pipeline_dir, "intermediate_videos")
    output_dir = os.path.join(pipeline_dir, "output_videos")

    return mp3_dir, wav_dir, img_dir, int_dir, output_dir

# Process audio file. MP3 -> WAV(add some silence)
def process_audio(input_dir, audio_file=None):
    logger.info("Starting audio processing")
    # TODO: for if using list of input audio files
    if audio_file:
        pass

    count = 0
    # Process each mp3 file in the mp3 directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".mp3"):
            wav_file_name = os.path.splitext(filename)[0] + ".wav"
            wav_file_path = os.path.join(input_dir, wav_file_name)
            
            # Skip if the wav file already exists
            if os.path.exists(wav_file_path):
                logger.info(f"Skipping {filename}, WAV file already exists.")
                continue

            # Convert MP3 to WAV and add silence at the beginning
            mp3_file_path = os.path.join(input_dir, filename)
            audio = AudioSegment.from_mp3(mp3_file_path)
            silence = AudioSegment.silent(duration=int(SILENCE_TIME))
            audio_with_silence = silence + audio

            # Export the processed audio as WAV
            audio_with_silence.export(wav_file_path, format="wav")
            # TODO: add metadata to the wav file
            logger.info(f"Converted {filename} to {wav_file_name}")

            # Move processed mp3 file to processed folder
            processed_dir = os.path.join(input_dir, "audio_mp3")
            os.makedirs(processed_dir, exist_ok=True)
            
            # Generate new filename with datetime if file already exists
            dest_path = os.path.join(processed_dir, filename)
            if os.path.exists(dest_path):
                base_name, ext = os.path.splitext(filename)
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{base_name}_{current_time}{ext}"
                dest_path = os.path.join(processed_dir, new_filename)
            
            # Move the file
            shutil.move(mp3_file_path, dest_path)
            logger.info(f"Moved {filename} to {dest_path}")
            count += 1

    logger.info(f"Processed {count} audio files.")

def run_commands(commands):
    """
    Run a list of shell commands sequentially in WSL or Ubuntu.
    Args:
        commands (list): A list of shell commands to run.
    Returns:
        None
    """
    # Combine the commands into a single string using '&&' to run them sequentially
    full_command = " && ".join(commands)

    # Execute the commands in a shell
    process = subprocess.run(full_command, shell=True, executable='/bin/bash', capture_output=True, text=True)

    # Print the output
    logger.info(process.stdout)

    # Check for errors
    if process.returncode != 0:
        logger.error(f"Error: {process.stderr}")

def get_cuda_env_path(version=DEFAULT_CUDA_VERSION):
    """
    Set the CUDA environment variables in the current shell.
    """
    version = str(version)
    return [f"export PATH=/usr/local/cuda-{version}/bin${{PATH:+:${{PATH}}}}",
            f"export LD_LIBRARY_PATH=/usr/local/cuda-{version}/lib64${{LD_LIBRARY_PATH:+:${{LD_LIBRARY_PATH}}}}"]

def rename_output_video(file_path, new_name):
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    
    # Get the directory and extension from the original file path
    directory = os.path.dirname(file_path)
    _, extension = os.path.splitext(file_path)

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create the new file name
    new_file_name = f"{new_name}_{timestamp}{extension}"

    # Construct the new file path
    new_file_path = os.path.join(directory, new_file_name)

    # Rename the file
    os.rename(file_path, new_file_path)

    # TODO: error handling

    return new_file_path

def rename_livePortrait_video(file_path, input_audio_filename, input_image_filename):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        
        final_filename = f"{input_audio_filename}-{input_image_filename}"
        return rename_output_video(file_path, final_filename)
    except Exception as e:
        logger.error(f"Error renaming LivePortrait video: {e}")
        return None

# TODO: WIP
def get_input_filenames(file_path):
    try:
        result = []
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file, skipinitialspace=True)
            for row in reader:
                if len(row) >= 2:
                    audio = row[0].strip().rstrip(',')
                    image = row[1].strip().rstrip(',')
                    if audio and image:  # Only append if both items are not empty
                        result.append((audio, image))
                    else:
                        logger.warning(f"Skipping row with empty value(s): {row}")
                else:
                    logger.warning(f"Skipping invalid row: {row}")
        
        if not result:
            logger.warning(f"No valid data found in {file_path}")
        
        return result
    except FileNotFoundError:
        logger.error(f"Input file {file_path} not found.")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
    
    return []

def validate_and_update_filenames(input_files, wav_dir, img_dir):
    """
    Validate and update filenames based on the contents of wav_dir and img_dir.
    
    Args:
    input_files (list): List of tuples containing (audio_file, image_file) pairs.
    wav_dir (str): Directory containing WAV files.
    img_dir (str): Directory containing image files.
    
    Returns:
    tuple: Two lists of validated audio and image filenames.
    """
    # Extract audio and image filenames from input_files
    audio_files, image_files = zip(*input_files) if input_files else ([], [])
    logger.info(f"files list: {input_files}")
    logger.info(f"audio files: {audio_files}")
    logger.info(f"image files: {image_files}")
    if len(audio_files) != len(image_files):
        logger.error(f"Mismatch: {len(audio_files)} audio files and {len(image_files)} image files")
        return []

    # Get lists of files from wav_dir and img_dir
    wav_dir_files = set(f for f in os.listdir(wav_dir) if f.endswith('.wav'))
    img_dir_files = set(f for f in os.listdir(img_dir) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg')))

    logger.info(f"Found {len(wav_dir_files)} WAV files in {wav_dir}")
    logger.info(f"wav_dir_files: {wav_dir_files}")
    logger.info(f"Found {len(img_dir_files)} image files in {img_dir}")
    logger.info(f"img_dir_files: {img_dir_files}")

    if not wav_dir_files:
        logger.warning(f"No WAV files found in {wav_dir}")
    if not img_dir_files:
        logger.warning(f"No image files found in {img_dir}")

    # Validate audio files
    validated_audio_files = []
    for audio_file in audio_files:
        if audio_file in wav_dir_files:
            logger.info(f"WAV file found: {audio_file}")
            validated_audio_files.append(audio_file)
        else:
            logger.warning(f"WAV file not found: {audio_file}")
            validated_audio_files.append(None)

    # Validate image files
    validated_image_files = []
    for image_file in image_files:
        if image_file in img_dir_files:
            logger.info(f"WAV file found: {image_file}")
            validated_image_files.append(image_file)
        else:
            logger.warning(f"WAV file not found: {image_file}")
            validated_image_files.append(None)

    # check validated files and combine them
    validated_pairs = []
    for i in range(len(validated_audio_files)):
        if validated_audio_files[i] is not None and validated_image_files[i] is not None:
            validated_pairs.append((validated_audio_files[i], validated_image_files[i]))
        else:
            logger.warning(f"Skipping pair: audio={validated_audio_files[i]}, image={validated_image_files[i]}")
    
    if not validated_pairs:
        logger.error("No valid audio-image pairs found")
    
    logger.info(f"Found {len(validated_pairs)} valid audio-image pairs")
    return validated_pairs

# For testing
def process_single_pair(audio_file, image_file, wav_dir, img_dir, intermediate_dir, output_dir, sadTalker_dir, livePortrait_dir):
    input_audio_path = os.path.join(wav_dir, audio_file)
    input_image_path = os.path.join(img_dir, image_file)
    input_audio_filename = os.path.splitext(audio_file)[0]
    input_image_filename = os.path.splitext(image_file)[0]

    # Check if input files exist
    if not os.path.exists(input_audio_path) or not os.path.exists(input_image_path):
        logger.error(f"Input file not found: {input_audio_path} or {input_image_path}")
        return False

    # Run SadTalker
    sadTalker_success, sadTalker_output = runSadTalker.run_sadtalker(sadTalker_dir, input_audio_path)
    if not sadTalker_success:
        logger.error("SadTalker processing failed.")
        return False

    # Rename and move output video to intermediate_videos
    try:
        inter_file_path = helpers.rename_output_video(sadTalker_output, input_audio_filename)
        inter_file_path = shutil.move(inter_file_path, intermediate_dir)
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return False

    # Run LivePortrait
    livePortrait_success, livePortrait_output = runLivePortrait.run_liveportrait(livePortrait_dir, input_image_path, inter_file_path)
    if not livePortrait_success:
        logger.error("LivePortrait processing failed.")
        return False

    # Rename and move output video to output directory
    final_output_path = helpers.rename_livePortrait_video(livePortrait_output, input_audio_filename, input_image_filename)
    final_output_path = shutil.move(final_output_path, output_dir)
    logger.info(f"Final output: {final_output_path}")

    return True


def get_input_audio_path(input_dir):
    # Get a list of all .wav files in the input directory
    wav_files = [f for f in os.listdir(input_dir) if f.endswith('.wav')]
    
    if not wav_files:
        logger.warning(f"No .wav files found in {input_dir}")
        return False, None
    
    # Sort wav_files by modification time (most recent first)
    wav_files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)), reverse=True)
    
    # Create full path for the most recent wav file
    wav_path = os.path.join(input_dir, wav_files[0])
    
    if len(wav_files) > 1:
        logger.warning(f"Found {len(wav_files)} .wav files in {input_dir}")

    logger.info(f"Input audio(wav) file: {wav_path}")
    return True, wav_path

def get_input_image_path(input_dir):
    # Get a list of all image files in the input directory
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return False, None
    
    # Sort image_files by modification time (most recent first)
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)), reverse=True)
    
    # Create full path for the most recent image file
    image_path = os.path.join(input_dir, image_files[0])
    
    if len(image_files) > 1:
        logger.warning(f"Found {len(image_files)} image files in {input_dir}")

    logger.info(f"Input image file: {image_path}")
    return True, image_path



def cleanup_completed_files(source_dir):
    # Create a 'completed' subdirectory in the source directory
    completed_dir = os.path.join(source_dir, "completed")
    os.makedirs(completed_dir, exist_ok=True)

    # Move all files from the source directory to the 'completed' subdirectory
    for file in os.listdir(source_dir):
        source_path = os.path.join(source_dir, file)
        if os.path.isfile(source_path):
            dest_path = os.path.join(completed_dir, file)
            
            # If the file already exists in the completed directory
            if os.path.exists(dest_path):
                # Generate a new filename with datetime postfix
                base_name, ext = os.path.splitext(file)
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{base_name}_{current_time}{ext}"
                dest_path = os.path.join(completed_dir, new_filename)
            
            # Move the file
            shutil.move(source_path, dest_path)
            logger.info(f"Moved {file} to {dest_path}")

    # Log the cleanup operation
    logger.info(f"Completed moving files from {source_dir} to {completed_dir}")


def save_to_output_file(file_paths, output_file):
    """
    Save the given file paths to a text or CSV file with the current datetime.

    Args:
    file_paths (list): The list of file paths to be saved.
    output_file (str): The name of the output file (txt or csv) to save the paths to.
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        with open(output_file, 'a') as file:
            if output_file.lower().endswith('.csv'):
                writer = csv.writer(file)
                writer.writerow(['Datetime'] + [f'File {i+1}' for i in range(len(file_paths))])
                writer.writerow([current_datetime] + file_paths)
            else:
                file.write(f"{current_datetime}: {', '.join(file_paths)}\n")
        logger.info(f"File paths saved to: {output_file}")
    except IOError as e:
        logger.error(f"Error saving file paths: {e}")

