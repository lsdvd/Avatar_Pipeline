# Reference: https://elevenlabs.io/docs/api-reference/getting-started


import requests
import os
import json
from logger import logger  # Import the logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define constants for the script
CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
XI_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # ID of the voice model to use
TEXT_TO_SPEAK = "Hello world. This is an appel. FOO BAR!"  # Text you want to convert to speech
OUTPUT_PATH = "output.mp3"  # Path to save the output audio file



def get_voices_list():
    # This is the URL for the API endpoint we'll be making a GET request to.
    url = "https://api.elevenlabs.io/v1/voices"

    # Here, headers for the HTTP request are being set up. 
    # Headers provide metadata about the request. In this case, we're specifying the content type and including our API key for authentication.
    headers = {
      "Accept": "application/json",
      "xi-api-key": XI_API_KEY,
      "Content-Type": "application/json"
    }

    # A GET request is sent to the API endpoint. The URL and the headers are passed into the request.
    response = requests.get(url, headers=headers)

    # The JSON response from the API is parsed using the built-in .json() method from the 'requests' library. 
    # This transforms the JSON data into a Python dictionary for further processing.
    data = response.json()

    # A loop is created to iterate over each 'voice' in the 'voices' list from the parsed data. 
    # The 'voices' list consists of dictionaries, each representing a unique voice provided by the API.
    for voice in data['voices']:
      # For each 'voice', the 'name' and 'voice_id' are printed out. 
      # These keys in the voice dictionary contain values that provide information about the specific voice.
      print(f"{voice['name']}; {voice['voice_id']}")

def text_to_speech(text_to_speak=TEXT_TO_SPEAK, voice_id=VOICE_ID, output_path=OUTPUT_PATH):
    # Construct the URL for the Text-to-Speech API request
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    # Set up the data payload for the API request, including the text and voice settings
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    # Make the POST request to the TTS API with headers and data, enabling streaming response
    response = requests.post(tts_url, headers=headers, json=data, stream=True)

    # Check if the request was successful
    if response.ok:
        # Open the output file in write-binary mode
        with open(output_path, "wb") as f:
            # Read the response in chunks and write to the file
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        # Inform the user of success
        print("Audio stream saved successfully.")
    else:
        # Print the error message if the request was not successful
        print(response.text)

def main():
    text = TEXT_TO_SPEAK
    voice_id = VOICE_ID
    output_path = OUTPUT_PATH

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "input_audio_mp3", "tts.mp3")

    try:
        # Call the text_to_speech function with the configured parameters
        text_to_speech(text, voice_id, output_path)
        logger.info(f"Text-to-speech conversion completed. Audio saved to: {output_path}")
    except Exception as e:
        logger.error(f"An error occurred during text-to-speech conversion: {str(e)}")

if __name__ == "__main__":
    main()
