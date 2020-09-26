import os
import random
import string

from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP

from app.config import config


def generate_filename(length):
    letters = string.ascii_letters
    return ''.join((random.choice(letters) for i in range(length))) + ".bin"

def encode_data(data, filename):
    data = data.encode("utf-8")
    with open(f'./encode/{filename}', 'wb') as file_out:
        recipient_key = RSA.import_key(generate_public_key())
        session_key = get_random_bytes(16)

        # Encrypt the session key with the public RSA key
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        enc_session_key = cipher_rsa.encrypt(session_key)

        # Encrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(data)
        for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext):
            file_out.write(x)
    
    f = open(f'./encode/{filename}', 'rb')
    encoded_data = f.read()
    f.close()
    os.remove(f'./encode/{filename}')

    return encoded_data


def decode_data(data, filename):
    filename_private_key = config["RSA"]["RSA_FILENAME_PRIVATE_KEY"]

    with open(f'./decode/{filename}', 'wb') as file_out:
        file_out.write(data)
    
    with open(f'./decode/{filename}', "rb") as file_in:
        private_key = RSA.import_key(open(filename_private_key).read())

        enc_session_key, nonce, tag, ciphertext = [ file_in.read(x) for x in (private_key.size_in_bytes(), 16, 16, -1) ]

        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)

        # Decrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)

    os.remove(f'./decode/{filename}')

    return data.decode("utf-8")



def generate_private_key_to_file():
    secret_code = config["FLASK_APP"]["FLASK_APP_SECRET_KEY"]
    filename_private_key = config["RSA"]["RSA_FILENAME_PRIVATE_KEY"]
    key = RSA.generate(1024)
    private_key = key.export_key()

    file_out = open(filename_private_key, "wb")
    file_out.write(private_key)
    file_out.close()


def generate_public_key():
    secret_code = config["FLASK_APP"]["FLASK_APP_SECRET_KEY"]
    filename_private_key = config["RSA"]["RSA_FILENAME_PRIVATE_KEY"]
    encoded_key = open(filename_private_key, 'rb').read()
    key = RSA.import_key(encoded_key, passphrase=secret_code)

    return key.publickey().export_key()