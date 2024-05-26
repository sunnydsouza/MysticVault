import os
import re
import uuid
from flask import render_template, request, redirect, url_for, jsonify, send_from_directory, send_file, Response
from app.encryption import get_progress,encrypt_folder, decrypt_folder
from app import app
import threading
from werkzeug.utils import secure_filename
from PIL import Image
import subprocess
import mimetypes
from datetime import datetime
from base64 import urlsafe_b64encode, urlsafe_b64decode

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        folder_path = request.form['folder_path']
        password = request.form['password']
        action = request.form['action']

        # Ensure folder path and password are not empty
        if not folder_path or not password:
            return jsonify({'error': 'Folder path and password cannot be empty'}), 400

        task_id = str(uuid.uuid4())  # Generate a unique task ID using UUID

        # Start the encryption or decryption in a new thread
        if action == 'encrypt':
            thread = threading.Thread(target=encrypt_folder, args=(task_id, password, folder_path))
            thread.start()
        elif action == 'decrypt':
            thread = threading.Thread(target=decrypt_folder, args=(task_id, password, folder_path))
            thread.start()

        # Return the task_id to the client for progress tracking
        return jsonify({'task_id': task_id})
    else:
        # Render the initial HTML form for input
        return render_template('index.html')

@app.route('/progress/<task_id>')
def progress(task_id):
    # Endpoint to fetch progress for a given task_id
    progress = get_progress(task_id)
    return jsonify(progress)


# --------------------------------
THUMBNAIL_DIR = '/home/pi/IOTstack/MysticVault/thumbnails'  # Ensure this directory exists

@app.route('/gallery')
def gallery():
    dir = request.args.get('dir', '')  # Get directory from query or default to empty
    return render_template('gallery.html', dir=dir)

@app.route('/folders', methods=['GET'])
def folders():
    base_dir = request.args.get('dir', '/path/to/your/media/folder')  # default path if none provided
    tree = make_tree(base_dir)
    return jsonify(tree)


def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try:
        lst = os.listdir(path)
    except OSError:
        pass  # ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(fn))
            else:
                file_stat = os.stat(fn)
                last_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                file_size = file_stat.st_size
                encrypted_status, original_name, encrypted_file_name = get_encryption_details(name)
                tree['children'].append({
                    'name': original_name,
                    'last_modified': last_modified,
                    'encrypted_file_name': encrypted_file_name,
                    'file_size': file_size,
                    'status': encrypted_status
                })
    return tree

def get_encryption_details(file_name):
    if file_name.endswith('.sef'):
        original_name = unscramble_name(file_name)
        return 'encrypted', original_name, file_name
    else:
        encrypted_name = scramble_name(file_name)
        return 'decrypted', file_name, encrypted_name

def scramble_name(original_name: str) -> str:
    """ Scramble the filename for encryption """
    return urlsafe_b64encode(original_name.encode()).decode() + '.sef'

def unscramble_name(scrambled_name: str) -> str:
    """ Restore the original filename after decryption """
    return urlsafe_b64decode(scrambled_name.rsplit('.sef', 1)[0]).decode()

@app.route('/thumbnails', methods=['GET'])
def thumbnails():
    base_dir = request.args.get('dir')  # Get directory from query parameter
    if not base_dir:
        return jsonify({'error': 'Directory parameter is missing'}), 400

    # base_dir = secure_filename(base_dir)  # Secure the directory name to prevent path traversal
    print(base_dir)
    # full_path = os.path.join('/path/to/your/media/folder', base_dir)
    full_path =  base_dir

    if not os.path.exists(full_path):
        return jsonify({'error': 'Directory not found'}), 404

    files = []
    for filename in os.listdir(full_path):
        file_path = os.path.join(full_path, filename)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in ['.png', '.jpg', '.jpeg']:
                thumbnail_path = os.path.join(THUMBNAIL_DIR, filename)
                if not os.path.exists(thumbnail_path):
                    img = Image.open(file_path)
                    img.thumbnail((200, 200))
                    img.save(thumbnail_path, "JPEG")
                files.append({'name': filename, 'thumbnail': f'/thumbnail/{filename}'})
            elif file_ext in ['.mp4']:  # Extend this list with more video formats as needed
                thumbnail_path = os.path.join(THUMBNAIL_DIR, f'{filename}.jpg')
                if not os.path.exists(thumbnail_path):
                    command = f"ffmpeg -i {file_path} -ss 00:00:01.000 -vframes 1 {thumbnail_path}"
                    subprocess.run(command, shell=True)
                files.append({'name': filename, 'thumbnail': f'/thumbnail/{filename}.jpg'})
    
    return jsonify({'files': files})

@app.route('/thumbnail/<filename>')
def send_thumbnail(filename):
    return send_from_directory(THUMBNAIL_DIR, filename)




@app.route('/media')
def serve_media():
    media_dir = request.args.get('dir')
    file_name = request.args.get('file')
    if not media_dir or not file_name:
        return "Missing parameters", 400

    file_path = os.path.join(media_dir, file_name)
    if not os.path.exists(file_path):
        return "File not found", 404

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        return "Unsupported file type", 415

    range_header = request.headers.get('Range', None)
    print('Range header', range_header)
    
    if range_header:
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            file_size = os.path.getsize(file_path)
            
            if end:
                end = int(end)
            else:
                end = file_size - 1

            length = end - start + 1
            response_headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(length),
                'Content-Type': mime_type
            }

            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    while True:
                        chunk = f.read(1024 * 8)
                        if not chunk:
                            break
                        yield chunk

            return Response(generate(), 206, headers=response_headers)

    return send_file(file_path, mimetype=mime_type)

@app.route('/encrypt', methods=['POST'])
@app.route('/decrypt', methods=['POST'])
def handle_encryption_decryption():
    data = request.get_json()
    folder_path = data.get('folder_path')
    password = data.get('password')
    task_id = str(uuid.uuid4())

    if request.path == '/encrypt':
        print(f'Encrypting with args: {task_id}, {password}, {folder_path}')
        threading.Thread(target=encrypt_folder, args=(task_id, password, folder_path)).start()
    elif request.path == '/decrypt':
        print(f'Decrypting with args: {task_id}, {password}, {folder_path}')
        threading.Thread(target=decrypt_folder, args=(task_id, password, folder_path)).start()

    return jsonify({'task_id': task_id})

    