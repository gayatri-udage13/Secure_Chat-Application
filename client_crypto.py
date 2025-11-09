from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

class CryptoManager:
    def __init__(self):
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()
        self.peer_public_key = None

    def get_public_key(self):
        return self.public_key.export_key().decode('utf-8')

    def set_peer_public_key(self, public_key_str):
        try:
            self.peer_public_key = RSA.import_key(public_key_str)
        except Exception as e:
            print("Error importing peer key:", e)

    def encrypt_message(self, message):
        if self.peer_public_key is None:
            raise ValueError("Peer public key not set yet.")
        cipher = PKCS1_OAEP.new(self.peer_public_key)
        encrypted = cipher.encrypt(message.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_message(self, encrypted_message_b64):
        try:
            encrypted_message = base64.b64decode(encrypted_message_b64)
            cipher = PKCS1_OAEP.new(self.private_key)
            decrypted = cipher.decrypt(encrypted_message).decode('utf-8')
            return decrypted
        except Exception as e:
            print("Decryption error:", e)
            return ""
