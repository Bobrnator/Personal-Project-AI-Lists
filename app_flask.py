from flask import Flask, render_template, request, jsonify
import json
import os
import pyttsx3
import gigaam
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import time

app = Flask(__name__)

# === STT MODEL ===
stt_model = gigaam.load_model("v2_ctc")

# === TTS ===
def _speak(text):
    tts = pyttsx3.init()
    tts.setProperty("rate", 175)
    tts.say(text)
    tts.runAndWait()

def speak(text):
    threading.Thread(target=_speak, args=(text,), daemon=True).start()

# === DATA ===
DATA_FILE = "../lists_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lists = json.load(f)
else:
    lists = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lists, f, ensure_ascii=False, indent=2)

# === STT FUNCTION ===
def record_audio(duration=4, fs=16000):
    filename = "../voice_cmd.wav"
    if os.path.exists(filename):
        os.remove(filename)
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    return filename

def transcribe_file(path):
    text = stt_model.transcribe(path)
    return text.strip().lower()

# === ROUTES ===
@app.route("/")
def index():
    return render_template("index.html", lists=lists)

@app.route("/add_list", methods=["POST"])
def add_list():
    name = request.form.get("list_name")
    if name and name not in lists:
        lists[name] = []
        save_data()
        speak(f"Создан список {name}")
        return jsonify({"status": "ok", "name": name})
    return jsonify({"status": "error"})

@app.route("/delete_list", methods=["POST"])
def delete_list():
    name = request.form.get("list_name")
    if name in lists:
        del lists[name]
        save_data()
        speak(f"Список {name} удалён")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route("/add_item", methods=["POST"])
def add_item():
    list_name = request.form.get("list_name")
    item_text = request.form.get("item_text")
    if list_name in lists and item_text:
        lists[list_name].append([item_text, "normal"])
        save_data()
        speak("Позиция добавлена")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@app.route("/voice_command", methods=["POST"])
def voice_command():
    duration = int(request.form.get("duration", 4))
    filename = record_audio(duration)
    text = transcribe_file(filename)
    speak("Команда: " + text)
    return jsonify({"text": text})

if __name__ == "__main__":
    app.run(debug=True)