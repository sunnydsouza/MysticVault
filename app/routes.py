import uuid
from flask import render_template, request, redirect, url_for, jsonify
from app.encryption import get_progress,encrypt_folder, decrypt_folder
from app import app
import threading

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