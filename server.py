import socket
import threading

clients = []
public_keys = {}

def handle_client(client_socket, addr):
    print(f"[+] {addr} connected.")
    try:
        # Receive the client's public key
        data = client_socket.recv(8192).decode('utf-8')
        if data.startswith("PUBLIC_KEY::"):
            public_key = data.split("::", 1)[1]
            public_keys[client_socket] = public_key
            print(f"[+] Received public key from {addr}")
        else:
            print(f"[-] Invalid key format from {addr}")
            client_socket.close()
            return

        # Wait until both clients are connected
        while len(public_keys) < 2:
            pass

        # Find the peer socket
        peer_socket = None
        for c in public_keys:
            if c != client_socket:
                peer_socket = c
                break

        # Exchange public keys
        if peer_socket:
            peer_key = public_keys[peer_socket]
            client_socket.sendall(f"PUBLIC_KEY::{peer_key}".encode('utf-8'))
            print(f"[+] Sent peer key to {addr}")

        # Relay encrypted messages
        while True:
            msg = client_socket.recv(8192)
            if not msg:
                break
            if peer_socket:
                try:
                    peer_socket.sendall(msg)
                except Exception as e:
                    print(f"[-] Failed to send to peer: {e}")
                    break

    except Exception as e:
        print(f"[-] Error with {addr}: {e}")

    finally:
        print(f"[-] {addr} disconnected.")
        if client_socket in public_keys:
            del public_keys[client_socket]
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5000))
    server.listen(2)
    print("[*] Server listening on port 5000")

    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()


if __name__ == "__main__":
    start_server()
