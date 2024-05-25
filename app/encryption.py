import os
import logging
from os import urandom
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import urlsafe_b64encode, urlsafe_b64decode
import threading
from glob import glob
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from datetime import datetime
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


def set_progress(task_id, overall_progress, total_files, current_file, current_file_progress, errors=None):
    with progress_lock:
        progress_dict[task_id] = {
            "overall_progress": overall_progress,
            "total_files": total_files,
            "current_file": current_file,
            "current_file_progress": current_file_progress,
            "errors": errors if errors else []
        }

def get_progress(task_id):
    with progress_lock:
        return progress_dict.get(task_id, {
            "overall_progress": 0,
            "total_files": 0,
            "current_file": None,
            "current_file_progress": 0,
            "errors": []
        })


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

     # Check and collect all files that are not already encrypted
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                files_to_process.extend([os.path.join(root, file) for file in files if not file.endswith('.sef')])
        elif os.path.isfile(path) and not path.endswith('.sef'):
            files_to_process.append(path)
        else:
            logging.error(f"Failed to find {path}: No such file or directory")
            set_progress(task_id, 0, 0, path, 0, [{"file": path, "error": "No such file or directory"}])
            return  # Optionally return after first failure or collect all failures



    total_files = len(files_to_process)
    processed_files = 0
    errors = []

    if total_files == 0:
        set_progress(task_id, 100, total_files, None, 100, errors)
        return
    
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    for file_path in files_to_process:
        try:
            encrypted_filename = scramble_name(os.path.basename(file_path))
            encrypted_file_path = os.path.join(os.path.dirname(file_path), encrypted_filename)
            file_size = os.path.getsize(file_path)
            processed_size = 0

            with open(file_path, 'rb') as infile, open(encrypted_file_path, 'wb') as outfile:
                cipher = Cipher(algorithms.AES(key), modes.CFB(os.urandom(16)), backend=default_backend())
                encryptor = cipher.encryptor()

                while True:
                    chunk = infile.read(10485760)  # Read in chunks of 10 MB
                    if not chunk:
                        break
                    outfile.write(encryptor.update(chunk))
                    processed_size += len(chunk)
                    current_file_progress = (processed_size / file_size) * 100
                    overall_progress = (processed_files / total_files) * 100 + (current_file_progress / total_files)
                    set_progress(task_id, overall_progress, total_files, file_path, current_file_progress, errors)

                outfile.write(encryptor.finalize())

            os.remove(file_path)
            processed_files += 1
        except Exception as e:
            logging.error(f"Failed to encrypt {file_path}: {str(e)}")
            errors.append({"file": file_path, "error": str(e)})
            set_progress(task_id, (processed_files / total_files) * 100, total_files, file_path, 100, errors)

    set_progress(task_id, 100, total_files, None, 100, errors)



def decrypt_folder(task_id, password, folder_path):
    paths = process_paths(folder_path)
    files_to_process = []

    # Check and collect all files to be decrypted
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                files_to_process.extend([os.path.join(root, file) for file in files if file.endswith('.sef')])
        elif os.path.isfile(path) and path.endswith('.sef'):
            files_to_process.append(path)
        else:
            logging.error(f"Failed to find {path}: No such file or directory")
            set_progress(task_id, 0, 0, path, 0, [{"file": path, "error": "No such file or directory"}])
            return  # Optionally return after first failure or collect all failures


    total_files = len(files_to_process)
    processed_files = 0
    errors = []

    if total_files == 0:
        set_progress(task_id, 100, total_files, None, 100, errors)
        return

    for file_path in files_to_process:
        try:
            file_size = os.path.getsize(file_path)
            processed_size = 0

            with open(file_path, 'rb') as infile:
                nonce, salt = infile.read(16), infile.read(16)
                key = derive_key(password, salt)

                cipher = Cipher(algorithms.AES(key), modes.CFB(nonce), backend=default_backend())
                decryptor = cipher.decryptor()

                decrypted_file_path = os.path.join(os.path.dirname(file_path), unscramble_name(os.path.basename(file_path)))
                with open(decrypted_file_path, 'wb') as outfile:
                    while True:
                        chunk = infile.read(1024 * 1024)  # Read in chunks of 1 MB
                        if not chunk:
                            break
                        outfile.write(decryptor.update(chunk))
                        processed_size += len(chunk)
                        current_file_progress = (processed_size / file_size) * 100
                        overall_progress = (processed_files / total_files) * 100 + (current_file_progress / total_files)
                        set_progress(task_id, overall_progress, total_files, file_path, current_file_progress, errors)
                    outfile.write(decryptor.finalize())

            os.remove(file_path)
            processed_files += 1
        except Exception as e:
            logging.error(f"Failed to decrypt {file_path}: {str(e)}")
            errors.append({"file": file_path, "error": str(e)})

    set_progress(task_id, 100, total_files, None, 100, errors)


