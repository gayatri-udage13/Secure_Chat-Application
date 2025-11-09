import socket
import threading
import time
from PyQt5.QtWidgets import QApplication
from client_crypto import CryptoManager
from PyQt5.QtCore import pyqtSignal
from client_gui import ChatClientGUI

class ChatClient:
    def __init__(self, gui):
        self.gui = gui
        self.socket = None
        self.crypto = CryptoManager()
        self.connected = False

        # Connect GUI signals
        self.gui.connectButton.clicked.connect(self.connect_to_server)
        self.gui.disconnectButton.clicked.connect(self.disconnect)
        self.gui.sendButton.clicked.connect(self.send_message)

    def connect_to_server(self):
        host = self.gui.serverIpInput.text()
        port = int(self.gui.serverPortInput.text())
        self.gui.update_connection_status("Connecting")

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.gui.update_connection_status("Connected")
            self.gui.append_message("Connected to server...\nWaiting for your friend's connection...")

            # Send our public key to server
            pub_key_msg = f"PUBLIC_KEY::{self.crypto.get_public_key()}"
            self.socket.sendall(pub_key_msg.encode('utf-8'))

            # Start thread to listen for messages
            threading.Thread(target=self.listen_for_messages, daemon=True).start()

            # Wait for peer public key
            self.wait_for_peer_key(timeout=15)

        except Exception as e:
            self.gui.append_message(f"Connection failed: {e}")
            self.gui.update_connection_status("Disconnected")

    def wait_for_peer_key(self, timeout=15):
        start = time.time()
        while self.crypto.peer_public_key is None:
            if time.time() - start > timeout:
                self.gui.append_message("Public key exchange timed out.\nDisconnecting...")
                self.disconnect()
                return
            time.sleep(0.5)
        self.gui.append_message("Public key exchange successful. You can now chat securely.\n")

    def listen_for_messages(self):
        while self.connected:
            try:
                msg = self.socket.recv(8192).decode('utf-8')
                if not msg:
                    time.sleep(0.1)
                    continue  # Don't break — wait for data

                if msg.startswith("PUBLIC_KEY::"):
                    peer_key = msg.split("::", 1)[1]
                    if not self.crypto.peer_public_key:
                        self.crypto.set_peer_public_key(peer_key)
                        print("[+] Peer public key received.")
                else:
                    decrypted = self.crypto.decrypt_message(msg)
                    if decrypted:
                        self.gui.message_received.emit("Friend: " + decrypted)

            except Exception as e:
                print("Error in listening thread:", e)
                break

        self.gui.append_message("Connection closed.")
        self.gui.update_connection_status("Disconnected")

    def send_message(self):
        if not self.connected:
            self.gui.append_message("Not connected to server.")
            return
        message = self.gui.messageInput.text().strip()
        if not message:
            return
        try:
            encrypted = self.crypto.encrypt_message(message)
            self.socket.sendall(encrypted.encode('utf-8'))
            self.gui.append_message("You: " + message)
            self.gui.messageInput.clear()
        except Exception as e:
            self.gui.append_message(f"Error sending message: {e}")

    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.gui.update_connection_status("Disconnected")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    gui = ChatClientGUI()
    client = ChatClient(gui)
    gui.show()
    sys.exit(app.exec_())
