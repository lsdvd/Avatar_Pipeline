import os
import sys
import shutil
import helpers
import runSadTalker
import runLivePortrait
from config_manager import config
from logger import logger  # Import the logger


DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
OUTPUT_LOG_PATH = "output_list.log"

def init_in_out_directories():
    cwd = os.getcwd()
    
    input_folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT_DIR
    output_folder = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR

    input_dir = os.path.join(cwd, input_folder)
    output_dir = os.path.join(cwd, output_folder)

    for directory in [input_dir, output_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

    return input_dir, output_dir

def main():
    input_dir, output_dir = init_in_out_directories()
    inter_dir = os.path.join(os.getcwd(), "intermediate_videos")
    if not os.path.exists(inter_dir):
        os.makedirs(inter_dir)
        logger.info(f"Created directory: {inter_dir}")
    logger.info("Starting main pipeline")
    
    parent_dir, pipeline_dir, sadTalker_dir, livePortrait_dir = helpers.get_directories()

    # mp3_dir, wav_dir, img_dir, intermediate_dir, output_dir = helpers.get_pipeline_directories(pipeline_dir)

    # process mp3 to wav
    helpers.process_audio(input_dir)

    # get input audio path
    get_input_audio_success, input_audio_path = helpers.get_input_audio_path(input_dir)
    # get input image path
    get_input_image_success, input_image_path = helpers.get_input_image_path(input_dir)

    if not (get_input_audio_success and get_input_image_success):
        logger.error("Failed to get input audio or image path")
        sys.exit(1)

    # Run SadTalker
    sadTalker_success, sadTalker_output = runSadTalker.run_sadtalker(sadTalker_dir, input_audio_path, output_path=inter_dir)
    if sadTalker_success:
        print("SadTalker processing complete.")
        print(sadTalker_output)
    else:
        print("SadTalker processing failed.")
        sys.exit(1)

    # Rename SadTalker output: {audio_filename}_{sadTalker_output(date_time)}
    new_path = os.path.join(
        os.path.dirname(sadTalker_output),
        f"{os.path.splitext(os.path.basename(input_audio_path))[0]}_{os.path.basename(sadTalker_output)}"
    )
    os.rename(sadTalker_output, new_path)
    logger.info(f"Renamed SadTalker output: {new_path}")

    # Update sadTalker_output variable with the new path
    sadTalker_output = new_path

    # Run LivePortrait
    livePortrait_success, livePortrait_output = runLivePortrait.run_liveportrait(livePortrait_dir, input_image_path, sadTalker_output, output_dir=output_dir)

    if livePortrait_success:
        logger.info("LivePortrait processing complete.")
        logger.info(f"LivePortrait output: {livePortrait_output}")
        
        # Check if the output is in the correct directory
        if os.path.dirname(livePortrait_output) == output_dir:
            logger.info("LivePortrait output is in the correct directory.")
        else:
            logger.warning("LivePortrait output is not in the expected output directory.")
            # Optionally, move the file to the correct directory
            new_path = os.path.join(output_dir, os.path.basename(livePortrait_output))
            shutil.move(livePortrait_output, new_path)
            logger.info(f"Moved LivePortrait output to: {new_path}")
            livePortrait_output = new_path
    else:
        logger.error("LivePortrait processing failed.")
        sys.exit(1)

    # clean up input & intermediate files
    helpers.cleanup_completed_files(input_dir)
    helpers.cleanup_completed_files(inter_dir)

    input_audio_file = os.path.basename(input_audio_path)
    input_image_file = os.path.basename(input_image_path)
    helpers.save_to_output_file([input_audio_file, input_image_file, livePortrait_output], "output_list.log")
    print(f"""Process complete.
          input audio: {input_audio_file}
          input image: {input_image_file}
          final output: {livePortrait_output}""")

if __name__ == "__main__":
    main()











    # #####################################################

    # TESTING CODE (preserved but not executed)
    # input_files_list = "input_files_list.txt"
    # input_files = helpers.get_input_filenames(input_files_list)
    # logger.info(f"input_files: {input_files}")
    # validated_files = helpers.validate_and_update_filenames(input_files, wav_dir, img_dir)
    # logger.info(f"validated_files: {validated_files}")
    
    # for audio_file, image_file in validated_files:
    #     success = process_single_pair(audio_file, image_file, wav_dir, img_dir, intermediate_dir, output_dir, sadTalker_dir, livePortrait_dir)
    #     if not success:
    #         logger.error(f"Processing failed for {audio_file} and {image_file}")
    # #####################################################


    # test audio input file
    # input_audio_path = os.path.join(wav_dir, "AWS_Sample1-10s.wav")
    # input_image_path = os.path.join(img_dir, "sample_1.jpg")
    # input_audio_filename = os.path.splitext(os.path.basename(input_audio_path))[0]
    # input_image_filename = os.path.splitext(os.path.basename(input_image_path))[0]

    # # Check if input files exist
    # if not os.path.exists(input_audio_path):
    #     logger.error(f"Input audio file not found: {input_audio_path}")
    #     sys.exit(1)
    # if not os.path.exists(input_image_path):
    #     logger.error(f"Input image file not found: {input_image_path}")
    #     sys.exit(1)