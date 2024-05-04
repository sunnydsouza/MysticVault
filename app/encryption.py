import os
import logging
from os import urandom
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import urlsafe_b64encode, urlsafe_b64decode
import threading
from glob import glob
# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def derive_key(password: str, salt: bytes) -> bytes:
    """ Derive a secure key from the password using Scrypt """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key

def scramble_name(original_name: str) -> str:
    """ Scramble the filename for encryption """
    return urlsafe_b64encode(original_name.encode()).decode() + '.sef'

def unscramble_name(scrambled_name: str) -> str:
    """ Restore the original filename after decryption """
    return urlsafe_b64decode(scrambled_name.rsplit('.sef', 1)[0]).decode()


# Global dictionary to store progress and a lock to manage concurrent access
progress_dict = {}
progress_lock = threading.Lock()

def set_progress(task_id, progress,total_files, errors=None):
    with progress_lock:
        progress_dict[task_id] = {"progress": progress, "total_files": total_files, "errors": errors if errors else []}

def get_progress(task_id):
    with progress_lock:
        return progress_dict.get(task_id, {"progress": 0, "total_files": 0, "errors": []})

def process_paths(input_path):
    """Process input to handle multiple paths or wildcards."""
    paths = []
    # Split input by ';' to handle multiple paths
    for part in input_path.split(';'):
        if '*' in part or '?' in part:  # Handle wildcard entries
            paths.extend(glob(part))
        else:
            if os.path.exists(part):
                paths.append(part)
    return paths
    

def encrypt_folder(task_id, password, folder_path):
    paths = process_paths(folder_path)
    files_to_process = []

    # Collect all files that are not already encrypted
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                files_to_process.extend([os.path.join(root, file) for file in files if not file.endswith('.sef')])
        elif os.path.isfile(path) and not path.endswith('.sef'):
            files_to_process.append(path)

    total_files = len(files_to_process)
    processed_files = 0
    errors = []

    if total_files == 0:
        set_progress(task_id, 100, 0, errors)  # Mark as complete if no files to process
        return
    
    salt = urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    # Encrypt each file
    for file_path in files_to_process:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            nonce = urandom(12)
            encrypted_data = aesgcm.encrypt(nonce, data, None)
            encrypted_filename = scramble_name(os.path.basename(file_path))
            encrypted_file_path = os.path.join(os.path.dirname(file_path), encrypted_filename)
            with open(encrypted_file_path, 'wb') as f:
                f.write(nonce + salt + encrypted_data)
                logging.debug(f"Encrypted {file_path} to {encrypted_filename}")
            os.remove(file_path)
            processed_files += 1
        except Exception as e:
            logging.error(f"Failed to encrypt {file_path}: {str(e)}")
            errors.append({"file": file_path, "error": str(e)})

        progress = round((processed_files / total_files) * 100)
        set_progress(task_id, progress, total_files, errors)

    set_progress(task_id, 100, total_files, errors)  # Final update to mark completion

def decrypt_folder(task_id, password, folder_path):
    paths = process_paths(folder_path)
    files_to_process = []

    # Collect files to process, including files from directories and directly specified files
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                files_to_process.extend([os.path.join(root, file) for file in files if file.endswith('.sef')])
        elif os.path.isfile(path) and path.endswith('.sef'):
            files_to_process.append(path)

    total_files = len(files_to_process)
    processed_files = 0
    errors = []

    if total_files == 0:
        set_progress(task_id, 100, 0, errors)  # Mark as complete if no files to process
        return
    
    for file_path in files_to_process:
        try:
            with open(file_path, 'rb') as f:
                file_contents = f.read()
            nonce, salt, encrypted_data = file_contents[:12], file_contents[12:28], file_contents[28:]
            key = derive_key(password, salt)
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
            original_filename = unscramble_name(os.path.basename(file_path))
            original_file_path = os.path.join(os.path.dirname(file_path), original_filename)
            with open(original_file_path, 'wb') as f:
                f.write(decrypted_data)
                logging.debug(f"Decrypted {file_path} to {original_filename}")
            os.remove(file_path)
            processed_files += 1
        except Exception as e:
            logging.error(f"Failed to decrypt {file_path}: {str(e)}")
            errors.append({"file": file_path, "error": str(e)})
        progress = round((processed_files / total_files) * 100)
        set_progress(task_id, progress, total_files, errors)

    set_progress(task_id, 100, total_files, errors)  # Final update to mark completion
