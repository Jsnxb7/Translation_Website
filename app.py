from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from gtts import gTTS
import time
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from faster_whisper import WhisperModel
import easyocr
import numpy as np
from PIL import Image
from vosk import Model, KaldiRecognizer
import wave
import json
import subprocess
import json
import uuid
from flask import session

app = Flask(__name__)

app.secret_key = "your_secret_key_here"

CHAT_FOLDER = "chat_data"

if not os.path.exists(CHAT_FOLDER):
    os.makedirs(CHAT_FOLDER)
def get_chat_file_path(unique_id):
    return os.path.join(CHAT_FOLDER, f"user_{unique_id}.json")

def read_chat_data(unique_id):
    path = get_chat_file_path(unique_id)

    if not os.path.exists(path):
        write_chat_data(unique_id, [])
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file corrupted, reset it
        write_chat_data(unique_id, [])
        return []

def write_chat_data(unique_id, data):
    path = get_chat_file_path(unique_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_next_serial_number(unique_id):
    chats = read_chat_data(unique_id)
    if not chats:
        return 1
    return max(c["serial_number"] for c in chats) + 1

DATA_FILE = "user_data.json"

def read_users():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

vosk_model = Model("models/vosk-model-small-hi-0.22")
reader_hi = easyocr.Reader(['en', 'hi'])
reader_ja = easyocr.Reader(['ja', 'en'])

model_size = "base"  

whisper_model = WhisperModel(
    model_size,
    device="cpu",   
    compute_type="int8" 
)

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        entered_username = request.form['username']
        entered_password = request.form['password']

        users = read_users()

        user_data = next(
            (u for u in users
             if u["username"] == entered_username and
                u["password"] == entered_password),
            None
        )

        if user_data:

            # ✅ STORE USER DATA IN SESSION
            session['unique_id'] = user_data['unique_id']
            session['name'] = user_data['name']
            session['post'] = user_data['post']

            # Redirect WITHOUT passing in URL
            return redirect(url_for('landing'))

        return jsonify({'error': 'Invalid username or password'})

    return render_template('login.html')

@app.route('/image_hi')
def image_hi():
    name = request.args.get('name')
    post = request.args.get('post')
    return render_template('image_hi.html', name=name, post=post)

@app.route('/upload_image_hi', methods=['POST'])
def upload_image_hi():

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    image_bytes = file.read()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_np = np.array(image)

    results = reader_hi.readtext(image_np, detail=0)
    extracted_text = " ".join(results)

    return jsonify({
        "ocr_text": extracted_text,
        "language": "hi"
    })

@app.route('/image_jp')
def image_jp():
    name = request.args.get('name')
    post = request.args.get('post')
    return render_template('image_jp.html', name=name, post=post)

@app.route('/upload_image_jp', methods=['POST'])
def upload_image_jp():

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 401

    file = request.files['image']
    image_bytes = file.read()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_np = np.array(image)

    results = reader_ja.readtext(image_np, detail=0)
    extracted_text = " ".join(results)

    return jsonify({
        "ocr_text": extracted_text,
        "language": "ja"
    })

@app.route('/landing')
def landing():
    name = request.args.get('name')
    post = request.args.get('post')
    unique_id = request.args.get('unique_id')
    serial_number = get_next_serial_number(unique_id)
    
    return render_template('landing.html', name=name, post=post, unique_id=unique_id, serial_number=serial_number)

@app.route('/Japanese')
def Japanese():
    name = request.args.get('name')
    post = request.args.get('post')
    unique_id = request.args.get('unique_id')

    return render_template('1jp.html', name=name, post=post, unique_id=unique_id)

@app.route('/Hindi')
def Hindi():
    name = request.args.get('name')
    post = request.args.get('post')
    unique_id = request.args.get('unique_id')

    return render_template('1hi.html', name=name, post=post, unique_id=unique_id)
     
@app.route('/signup1', methods=['POST'])
def update():
    name = request.form['name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    post = request.form['post']

    users = read_users()

    # Generate unique id
    unique_id = str(uuid.uuid4())
    # After writing user to user_data.json

    chat_path = get_chat_file_path(unique_id)

    if not os.path.exists(chat_path):
        with open(chat_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)

    user_data = {
        'unique_id': unique_id,
        'name': name,
        'username': username,
        'email': email,
        'password': password,
        'post': post,
        'tokens': 3000
    }

    users.append(user_data)
    write_users(users)

    # Create empty chat file
    write_chat_data(unique_id, [])

    return redirect(url_for('login'))

@app.route('/recordhi')
def recordhi():
    name = request.args.get('name')
    post = request.args.get('post')
    return render_template('recordhi.html', name=name, post=post)

@app.route('/recordjp')
def recordjp():
    name = request.args.get('name')
    post = request.args.get('post')
    return render_template('recordjp.html', name=name, post=post)

@app.route('/upload_audio_hi', methods=['POST'])
def upload_audio_hi():

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 403

    audio_file = request.files['audio']
    input_path = os.path.join("static", "input_hi.webm")
    output_path = os.path.join("static", "input_hi.wav")

    audio_file.save(input_path)

    # 🔥 Convert to 16kHz mono WAV
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ])

    wf = wave.open(output_path, "rb")

    if wf.getframerate() != 16000:
        return jsonify({"error": "Audio must be 16kHz"}), 400

    rec = KaldiRecognizer(vosk_model, 16000)

    full_text = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            full_text += result.get("text", "") + " "

    # Get final partial result
    final_result = json.loads(rec.FinalResult())
    full_text += final_result.get("text", "")

    print("Vosk Hindi Transcription:", full_text)

    return jsonify({
        "transcription": full_text.strip(),
        "language": "hi"
    }), 200

@app.route('/upload_audio_ja', methods=['POST'])
def upload_audio_ja():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 403

    audio_file = request.files['audio']
    save_path = os.path.join("static", "input_ja.wav")
    audio_file.save(save_path)

    print("Japanese audio saved at:", save_path)

    segments, info = whisper_model.transcribe(
        save_path,
        beam_size=5,
        language="ja" 
    )

    full_text = ""
    for segment in segments:
        full_text += segment.text + " "

    print("Transcription (JA):", full_text)

    return jsonify({
        "transcription": full_text.strip(),
        "language": "ja"
    }), 200

@app.route('/signup')
def sign_up():
    return render_template('signup.html')

tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-tatoeba-en-ja")
model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-tatoeba-en-ja")

def translatejp(text):
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt")

    # Generate translated output
    outputs = model.generate(**inputs)

    # Decode the output tokens
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(translated_text)
    return translated_text

@app.route('/translatjp', methods=['POST'])
def translatjp():
    data = request.get_json()
    unique_id = session.get('unique_id')
    tex = data.get('text')
    print("Received JSON:", data)
    print("Unique ID:", unique_id)
    print("Text:", tex)

    if not unique_id or not tex:
        return jsonify({'error': 'Missing data'}), 404

    translation = translatejp(tex)
    token_count = len(tex) * 3

    chats = read_chat_data(unique_id)
    serial_number = len(chats) + 1

    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Japanese"
    }

    chats.append(output_data)
    write_chat_data(unique_id, chats)

    total_token_count = sum(c['token_count'] for c in chats)

    return jsonify({
        "serial_number": serial_number,
        "translated_text": translation,
        "token_count": token_count,
        "total_token_count": total_token_count
    }), 200

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load smaller EN→HI model
model_name = "Helsinki-NLP/opus-mt-en-hi"

tokenizerhi = AutoTokenizer.from_pretrained(model_name)
modelhi = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def translatehi(text):
    try:
        if not text:
            return "No input text provided."

        inputs = tokenizerhi(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )

        with torch.no_grad():
            translated_tokens = modelhi.generate(
                **inputs,
                max_length=512
            )

        translated_text = tokenizerhi.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )

        return translated_text[0]

    except Exception as e:
        print("Translation error:", str(e))
        return "Translation failed."

@app.route('/translathi', methods=['POST'])
def translathi():

    data = request.get_json()
    unique_id = session.get('unique_id')
    tex = data.get('text')

    if not unique_id or not tex:
        return jsonify({'error': 'Missing data'}), 405

    translation = translatehi(tex)
    token_count = len(tex) * 3

    chats = read_chat_data(unique_id)
    serial_number = len(chats) + 1

    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Hindi"
    }

    chats.append(output_data)
    write_chat_data(unique_id, chats)

    total_token_count = sum(c['token_count'] for c in chats)

    return jsonify({
        "serial_number": serial_number,
        "translated_text": translation,
        "token_count": token_count,
        "total_token_count": total_token_count
    }), 201

@app.route('/speechjp', methods=['POST'])
def speechjp():

    data = request.get_json()
    unique_id = session.get('unique_id')
    serial_number = data.get('serial_number')

    if not unique_id or not serial_number:
        return jsonify({'error': 'Missing data'}), 406

    chats = read_chat_data(unique_id)

    entry = next(
        (c for c in chats if c["serial_number"] == serial_number),
        None
    )

    if not entry:
        return jsonify({"error": "Translation not found"}), 407

    text_to_speech_text = entry["translated_text"]

    timestamp = str(int(time.time()))
    audio_filename = f"static/{timestamp}.mp3"

    tts = gTTS(text=text_to_speech_text, lang="ja")
    tts.save(audio_filename)

    return jsonify(audio_url=f'/{audio_filename}'), 202

@app.route('/speechhi', methods=['POST'])
def speechhi():

    data = request.get_json()
    unique_id = session.get('unique_id')
    serial_number = data.get('serial_number')

    if not unique_id or not serial_number:
        return jsonify({'error': 'Missing data'}), 408

    chats = read_chat_data(unique_id)

    entry = next(
        (c for c in chats if c["serial_number"] == serial_number),
        None
    )

    if not entry:
        return jsonify({"error": "Translation not found"}), 409

    text_to_speech_text = entry["translated_text"]

    timestamp = str(int(time.time()))
    audio_filename = f"static/{timestamp}.mp3"

    tts = gTTS(text=text_to_speech_text, lang="hi")
    tts.save(audio_filename)

    return jsonify(audio_url=f'/{audio_filename}'), 203

ja_en_model_name = "Helsinki-NLP/opus-mt-ja-en"

tokenizer_ja_en = AutoTokenizer.from_pretrained(ja_en_model_name)
model_ja_en = AutoModelForSeq2SeqLM.from_pretrained(ja_en_model_name)

def translat_ja_en(text):
    try:
        if not text:
            return "No input text provided."

        inputs = tokenizer_ja_en(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )

        with torch.no_grad():
            translated_tokens = model_ja_en.generate(
                **inputs,
                max_length=512
            )

        translated_text = tokenizer_ja_en.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )

        return translated_text[0]

    except Exception as e:
        print("JA→EN Translation error:", str(e))
        return "Translation failed."
    
@app.route('/translate_ja_en', methods=['POST'])
def translate_ja_en():

    data = request.get_json()
    unique_id = session.get('unique_id')
    tex = data.get('text')

    if not unique_id or not tex:
        return jsonify({'error': 'Missing data'}), 412

    translation = translat_ja_en(tex)
    token_count = len(tex) * 3

    chats = read_chat_data(unique_id)
    serial_number = len(chats) + 1

    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Japanese → English"
    }

    chats.append(output_data)
    write_chat_data(unique_id, chats)

    total_token_count = sum(c['token_count'] for c in chats)

    return jsonify({
        "serial_number": serial_number,
        "translated_text": translation,
        "token_count": token_count,
        "total_token_count": total_token_count
    }), 200

hi_en_model_name = "Helsinki-NLP/opus-mt-hi-en"

tokenizer_hi_en = AutoTokenizer.from_pretrained(hi_en_model_name)
model_hi_en = AutoModelForSeq2SeqLM.from_pretrained(hi_en_model_name)

def translat_hi_en(text):
    try:
        if not text:
            return "No input text provided."

        inputs = tokenizer_hi_en(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )

        with torch.no_grad():
            translated_tokens = model_hi_en.generate(
                **inputs,
                max_length=512
            )

        translated_text = tokenizer_hi_en.batch_decode(
            translated_tokens,
            skip_special_tokens=True
        )

        return translated_text[0]

    except Exception as e:
        print("HI→EN Translation error:", str(e))
        return "Translation failed."
    
@app.route('/translate_hi_en', methods=['POST'])
def translate_hi_en():

    data = request.get_json()
    unique_id = session.get('unique_id')
    tex = data.get('text')

    if not unique_id or not tex:
        return jsonify({'error': 'Missing data'}), 413

    translation = translat_hi_en(tex)
    token_count = len(tex) * 3

    chats = read_chat_data(unique_id)
    serial_number = len(chats) + 1

    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Hindi → English"
    }

    chats.append(output_data)
    write_chat_data(unique_id, chats)

    total_token_count = sum(c['token_count'] for c in chats)

    return jsonify({
        "serial_number": serial_number,
        "translated_text": translation,
        "token_count": token_count,
        "total_token_count": total_token_count
    }), 200

@app.route('/output/<filename>')
def serve_audio(filename):
    path_to_file = f"static/{filename}"
    print(path_to_file)

    return send_file(
        path_to_file,
        mimetype="audio/mp3",
        as_attachment=True,
        attachment_filename=filename
    )

@app.route('/profile', methods=['GET'])
def profile():
    name = request.args.get('name')
    post = request.args.get('post')
    return render_template('profile.html', name=name, post=post)

@app.route('/get_pie_chart', methods=['POST'])
def get_pie_chart():

    data = request.get_json()
    unique_id = data.get('unique_id')

    if not unique_id:
        return jsonify({'error': 'Missing user id'}), 410

    chats = read_chat_data(unique_id)
    total_tokens_used = sum(c.get('token_count', 0) for c in chats)

    users = read_users()
    user_data = next(
        (u for u in users if u['unique_id'] == unique_id),
        None
    )

    if not user_data:
        return jsonify({'error': 'User not found'}), 411

    total_token_limit = user_data.get('tokens', 3000)

    pie_chart = generate_pie_chart(total_tokens_used, total_token_limit)
    pie_chart_base64 = base64.b64encode(pie_chart.getvalue()).decode('utf-8')

    return jsonify({
        'pie_chart': pie_chart_base64
    })

def generate_pie_chart(total_tokens_used, total_token_count):
    print(total_tokens_used, total_token_count)
    labels = ['Tokens Used', 'Remaining Tokens']
    sizes = [total_tokens_used, total_token_count - total_tokens_used]
    colors = ['lightblue', 'lightgreen']
    explode = (0.1, 0)

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140)
    ax.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return img

def clean_up():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    for file in os.listdir(static_dir):
        if file.endswith('.mp3'):
            try:
                os.remove(os.path.join(static_dir, file))
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000)
    finally:
        clean_up()