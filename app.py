from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from gtts import gTTS
import time
from pymongo import MongoClient
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = Flask(__name__)

client = MongoClient('mongodb+srv://shouryagarg2012:XGxOxzFRFHp87Kpe@cluster0.zyqzpr5.mongodb.net/')
db = client['user_data']
collection = db['user_data']


@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        entered_username = request.form['username']
        entered_password = request.form['password']

        # Query the MongoDB collection to find a matching user
        user_data = collection.find_one({
            'username': entered_username,
            'password': entered_password
        })

        if user_data:
            # Extract name and post from user_data
            name = user_data['name']
            post = user_data['post']
            collectionname = user_data['collectionname']

            return redirect(url_for('landing', name=name, post=post, collectionname=collectionname))

        return jsonify({'error': 'Invalid username or password'})

    return render_template('login.html')

@app.route('/landing')
def landing():
    name = request.args.get('name')
    post = request.args.get('post')
    collectionname = request.args.get('collectionname')

    serial_number = get_next_serial_number(collectionname)
    
    return render_template('landing.html', name=name, post=post, collectionname=collectionname, serial_number=serial_number)

@app.route('/Japanese')
def Japanese():
    name = request.args.get('name')
    post = request.args.get('post')
    collectionname = request.args.get('collectionname')
    
    return render_template('1jp.html', name=name, post=post, collectionname=collectionname)

@app.route('/Hindi')
def Hindi():
    name = request.args.get('name')
    post = request.args.get('post')
    collectionname = request.args.get('collectionname')

    return render_template('1hi.html', name=name, post=post, collectionname=collectionname)
     
@app.route('/signup1', methods=['POST'])
def update():

    # Extract user data from the form
    name = request.form['name']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    post = request.form['post']
    
    # Create a new collection for the user based on the username
    user_specific_collection_name = f"user_{username}"
    user_specific_collection = db[user_specific_collection_name]
    
        # Data to insert into the user_data collection
    user_data = {
        'name': name,
        'username': username,
        'email': email,
        'password': password,
        'post': post,
        'collectionname': user_specific_collection_name,
        'tokens': 3000
            }
    
    # Insert the new user data into the user_data collection
    collection.insert_one(user_data)
    
    # Optionally, you can insert initial data into the user's specific collection
    initial_data = {
        'name': name,
        'post': post,
        'email': email,
        'total': 3000
    }
    user_specific_collection.insert_one(initial_data)
    
    return redirect(url_for('login'))

@app.route('/signup')
def sign_up():
    return render_template('signup.html')

def get_next_serial_number(collection):
    
    try:
        # Get the count of documents in the MongoDB collection
        data_count = collection.count_documents({})
        return data_count + 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    
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
    name = data.get('name')
    post = data.get('post')
    
    if not name or not post:
        return jsonify({'error': 'Name and post are required'}), 410
    
    
    # Retrieve user data to get collectionname
    user_data = db['user_data'].find_one({'name': name, 'post': post})
    if not user_data or 'collectionname' not in user_data:
        return jsonify({'error': 'User data not found or collection name missing'}), 404
    
    collectionname = user_data['collectionname']
    collection = db[collectionname]

    twt = request.get_json()
    tex = twt.get('text')
    print(tex)
    
    # Translate text using the Hugging Face model
    translation = translatejp(tex)
    
    # Tokenize the original text
    token_count = len(tex) * 3
    
    # Get the next serial number
    serial_number = get_next_serial_number(collection)
    
    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Japanese"
    }
    
    try:
        # Insert the new translation data into the MongoDB collection
        collection.insert_one(output_data)
        print("Translation data saved successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Calculate the total token count
    total_token_count = 0
    try:
        all_documents = collection.find({})
        for doc in all_documents:
            total_token_count += doc.get('token_count', 0)
    except Exception as e:
        print(f"An error occurred while calculating total token count: {e}")
    
    print(f"Current token count: {token_count}")
    print(f"Total token count: {total_token_count}")
    print(translation)

    return jsonify({"serial_number": serial_number, "translated_text": translation, "token_count": token_count, "total_token_count": total_token_count}), 200

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load NLLB model
tokenizerhi = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
modelhi = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")

import torch

def translatehi(text):
    try:
        if not text:
            return "No input text provided."

        tokenizerhi.src_lang = "eng_Latn"

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
                forced_bos_token_id=tokenizerhi.convert_tokens_to_ids("hin_Deva"),
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
    name = data.get('name')
    post = data.get('post')
    
    if not name or not post:
        return jsonify({'error': 'Name and post are required'}), 510
    
    # Retrieve user data to get collectionname
    user_data = db['user_data'].find_one({'name': name, 'post': post})
    if not user_data or 'collectionname' not in user_data:
        return jsonify({'error': 'User data not found or collection name missing'}), 504
    
    collectionname = user_data['collectionname']
    collection = db[collectionname]

    twt = request.get_json()
    tex = twt.get('text')
    
    # Translate text using the Hugging Face model
    translation = translatehi(tex)
    
    # Tokenize the original text
    token_count = len(tex) * 3
    
    # Get the next serial number
    serial_number = get_next_serial_number(collection)
    
    output_data = {
        "serial_number": serial_number,
        "original_text": tex,
        "translated_text": translation,
        "token_count": token_count,
        "language": "Hindi"
    }
    
    try:
        # Insert the new translation data into the MongoDB collection
        collection.insert_one(output_data)
        print("Translation data saved successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Calculate the total token count
    total_token_count = 0
    try:
        all_documents = collection.find({})
        for doc in all_documents:
            total_token_count += doc.get('token_count', 0)
    except Exception as e:
        print(f"An error occurred while calculating total token count: {e}")

    try:
        db['user_data'].update_one(
            {'name': name, 'post': post},
            {'$set': {'total_token_count': total_token_count}}
        )
        print("Total token count updated successfully.")
    except Exception as e:
        print(f"An error occurred while updating total token count: {e}")
    
    print(f"Current token count: {token_count}")
    print(f"Total token count: {total_token_count}")
    print(translation)

    return jsonify({"serial_number": serial_number, "translated_text": translation, "token_count": token_count, "total_token_count": total_token_count}), 200

@app.route('/speechjp', methods=['POST'])
def speechjp():

    data = request.get_json()
    name = data.get('name')
    post = data.get('post')
    serial_number = data.get('serial_number')

    if not name or not post or not serial_number:
        return jsonify({'error': 'Name, post, and serial number are required'}), 511

    # Retrieve the collectionname from the user_data collection
    user_data = db['user_data'].find_one({'name': name, 'post': post})
    if not user_data or 'collectionname' not in user_data:
        return jsonify({'error': 'User data not found or collection name missing'}), 514

    collectionname = user_data['collectionname']
    collection = db[collectionname]

    print(serial_number)

    # Find the entry with the specified serial number in MongoDB
    entry = collection.find_one({"serial_number": serial_number})
    if entry is None:
        return jsonify({"error": f"Translation with serial number {serial_number} not found"}), 704

    # Use the translated text for text-to-speech
    text_to_speech_text = entry["translated_text"]

    # Generate a unique filename using a timestamp
    timestamp = str(int(time.time()))
    audio_filename = f"static/{timestamp}.mp3"

    # Convert text to speech and save with the unique filename
    tts = gTTS(text=text_to_speech_text, lang="ja")
    tts.save(audio_filename)
    print("Audio filename:", audio_filename)

    # Create the audio URL with the unique filename
    audio_url = f'/{audio_filename}'

    return jsonify(audio_url=audio_url), 200

@app.route('/speechhi', methods=['POST'])
def speechhi():

    data = request.get_json()
    name = data.get('name')
    post = data.get('post')
    serial_number = data.get('serial_number')

    if not name or not post or not serial_number:
        return jsonify({'error': 'Name, post, and serial number are required'}), 411

    # Retrieve the collectionname from the user_data collection
    user_data = db['user_data'].find_one({'name': name, 'post': post})
    if not user_data or 'collectionname' not in user_data:
        return jsonify({'error': 'User data not found or collection name missing'}), 414

    collectionname = user_data['collectionname']
    collection = db[collectionname]

    print(serial_number)

    # Find the entry with the specified serial number in MongoDB
    entry = collection.find_one({"serial_number": serial_number})
    if entry is None:
        return jsonify({"error": f"Translation with serial number {serial_number} not found"}), 804

    # Use the translated text for text-to-speech
    text_to_speech_text = entry["translated_text"]

    # Generate a unique filename using a timestamp
    timestamp = str(int(time.time()))
    audio_filename = f"static/{timestamp}.mp3"

    # Convert text to speech and save with the unique filename
    tts = gTTS(text=text_to_speech_text, lang="hi")
    tts.save(audio_filename)
    print("Audio filename:", audio_filename)

    # Create the audio URL with the unique filename
    audio_url = f'/{audio_filename}'

    return jsonify(audio_url=audio_url), 200

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
    name = data.get('name')
    post = data.get('post')

    if not name or not post:
        return jsonify({'error': 'Name and post are required'}), 400

    # Retrieve user data
    user_data = db['user_data'].find_one({'name': name, 'post': post})
    if not user_data:
        return jsonify({'error': 'User not found'}), 404

    # Get the collection name from a specific field in user_data
    user_collection_name = user_data.get('collectionname')
    if not user_collection_name:
        return jsonify({'error': 'Collection name not found for this user'}), 402

    # Now get the collection
    user_collection = db[user_collection_name]

    # Calculate total tokens used from that collection
    total_tokens_used = sum(doc.get('token_count', 0) for doc in user_collection.find())

    # Generate the pie chart
    pie_chart = generate_pie_chart(total_tokens_used, user_data['tokens'])

    # Encode the pie chart image in base64
    pie_chart_base64 = base64.b64encode(pie_chart.getvalue()).decode('utf-8')

    return jsonify({
        'name': name,
        'post': post,
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
        app.run(host='0.0.0.0', port=5000)
    finally:
        clean_up()