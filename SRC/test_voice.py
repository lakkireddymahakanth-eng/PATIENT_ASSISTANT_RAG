import sounddevice as sd
import numpy as np
import whisper
import tempfile
import scipy.io.wavfile as wav

# -------------------------
# LOAD WHISPER
# -------------------------
model = whisper.load_model("base")

# -------------------------
# LIST DEVICES
# -------------------------
print("\n🎤 Available Audio Devices:\n")
devices = sd.query_devices()

for i, d in enumerate(devices):
    print(f"{i}: {d['name']} (inputs={d['max_input_channels']})")

print("\n👉 Choose device index with input > 0\n")

device_index = int(input("Enter device index: "))


# -------------------------
# RECORD TEST AUDIO
# -------------------------
def record_test(fs=16000, duration=5):

    print("\n🎤 Speak now for 5 seconds...\n")

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=device_index)
    sd.wait()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav.write(temp_file.name, fs, audio)

    return temp_file.name


# -------------------------
# RUN TEST
# -------------------------
audio_file = record_test()

print("\n🧠 Transcribing...\n")

result = model.transcribe(audio_file)

print("🗣 You said:", result["text"])