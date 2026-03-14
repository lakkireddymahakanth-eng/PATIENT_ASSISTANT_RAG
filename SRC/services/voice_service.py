import whisper
import sounddevice as sd
import scipy.io.wavfile as wav
from gtts import gTTS
import os

model = whisper.load_model("base")


def speech_to_text():

    samplerate = 16000
    duration = 5

    print("Listening...")

    audio = sd.rec(int(duration * samplerate),
                   samplerate=samplerate,
                   channels=1)

    sd.wait()

    audio_path = "temp_audio.wav"
    wav.write(audio_path, samplerate, audio)

    result = model.transcribe(audio_path)

    return result["text"]


def text_to_speech(text):

    tts = gTTS(text=text, lang="en")

    file_path = "response.mp3"

    tts.save(file_path)

    return file_path