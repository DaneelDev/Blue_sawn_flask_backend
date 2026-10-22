import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def encrypt_text(text: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex) #converts hex key into bytes
    iv = os.urandom(12) #random initialisation vector
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()) #create encrypt obj with validation
    encryptor = cipher.encryptor() #configure the encrypt process
    ciphertext = encryptor.update(text.encode("utf-8")) + encryptor.finalize() #create an encrypted string in utf-8
    tag = encryptor.tag #need to decrypt the ciphertext
    blob = iv + tag + ciphertext
    return base64.b64encode(blob).decode("ascii") #encodes bin into base64 then decodes to ascii sctr

def decrypt_text(b64_data: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex)
    blob = base64.b64decode(b64_data)
    iv, tag, ciphertext = blob[:12], blob[12:28], blob[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode("utf-8")
