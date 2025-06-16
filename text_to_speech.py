from gtts import gTTS
import os
import subprocess

def text_to_speech(text):
    # Initialize gTTS with the text to convert
    speech = gTTS(text)

    # Save the audio file to a temporary file
    speech_file = 'speech.mp3'
    speech.save(speech_file)

    # Play the audio file
    # os.system('afplay ' + speech_file)
    
    # # Command to be executed
    # command = [
    #     'python', 'inference.py',
    #     '--driven_audio', speech_file,
    #     '--source_image', 'raymondlew.png',
    #     '--enhancer', 'gfpgan'
    # ]

    # # Run the command
    # try:
    #     subprocess.run(command, check=True)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error executing the command: {e}")
    
# text_to_speech('Hello, world! This is a test.')