import socket
from _thread import *
import numpy as np
import rsa
from snake import SnakeGame
import uuid
import time
import json
from cryptography.fernet import Fernet
import traceback

server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

rows = 20
predefined_messages = {
    "Z": "Congratulations!",
    "X": "It works!",
    "C": "Ready?"
}

try:
    s.bind((server, port))
except socket.error as e:
    print(f"Socket bind error: {e}")

s.listen(2)
print("Waiting for a connection, Server Started")

game = SnakeGame(rows)
interval = 0.2
moves_queue = set()

(server_public_key, server_private_key) = rsa.newkeys(2048)

rgb_colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
}
rgb_colors_list = list(rgb_colors.values())

# For chat broadcast
last_chat_message = None
last_chat_message_time = 0

def send_with_length(sock, data):
    length = len(data)
    sock.sendall(length.to_bytes(4, byteorder='big') + data)

def recv_with_length(sock):
    length_bytes = b''
    while len(length_bytes) < 4:
        more = sock.recv(4 - len(length_bytes))
        if not more:
            raise ConnectionError("Socket closed before length received")
        length_bytes += more
    length = int.from_bytes(length_bytes, byteorder='big')
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise ConnectionError("Socket closed before full message received")
        data += more
    return data

def game_thread():
    global game, moves_queue
    while True:
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        while time.time() - last_move_timestamp < interval:
            time.sleep(0.01)

def client_thread(unique_id, conn, addr):
    global last_chat_message, last_chat_message_time
    try:
        conn.send(server_public_key.save_pkcs1(format='PEM'))
        client_public_key_data = conn.recv(2048)
        client_public_key = rsa.PublicKey.load_pkcs1(client_public_key_data, 'PEM')
        encrypted_fernet_key = conn.recv(512)
        fernet_key = rsa.decrypt(encrypted_fernet_key, server_private_key)
        fernet = Fernet(fernet_key)

        while True:
            try:
                encrypted_data = recv_with_length(conn)
            except Exception as e:
                print(f"Connection closed by client: {addr} ({e})")
                break

            try:
                decrypted_data = fernet.decrypt(encrypted_data).decode()
                client_msg = json.loads(decrypted_data)
                command = client_msg["command"]
            except Exception as e:
                print(f"Decryption/parse error: {e}")
                traceback.print_exc()
                break

            # Chat broadcast: update shared message if chat received
            if ":" in command:
                data_HEADER, data_CONTENT = command.split(":", 1)
                if data_HEADER == "CONTROL":
                    if data_CONTENT == "get":
                        pass
                    elif data_CONTENT == "quit":
                        game.remove_player(unique_id)
                        conn.close()
                        break
                    elif data_CONTENT == "reset":
                        game.reset_player(unique_id)
                    elif data_CONTENT in ["up", "down", "left", "right"]:
                        moves_queue.add((unique_id, data_CONTENT))
                elif data_HEADER == "CHAT":
                    if data_CONTENT in predefined_messages:
                        last_chat_message = f"Chat from {addr}: {predefined_messages[data_CONTENT]}"
                        last_chat_message_time = time.time()

            # Only show chat message if it is recent (last 5 seconds)
            chat_message = None
            if last_chat_message and time.time() - last_chat_message_time < 5:
                chat_message = last_chat_message
            else:
                chat_message = None

            snakes = []
            for player_id, player in game.players.items():
                snake_info = {
                    "positions": [cube.pos for cube in player.body],
                    "color": player.color
                }
                snakes.append(snake_info)

            response = {
                "snakes": snakes,
                "snacks": [snack.pos for snack in game.snacks],
                "chat_message": chat_message
            }
            response_str = json.dumps(response)
            encrypted_response = fernet.encrypt(response_str.encode())
            send_with_length(conn, encrypted_response)
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        traceback.print_exc()
    finally:
        try:
            game.remove_player(unique_id)
        except Exception:
            pass
        conn.close()
        print(f"Connection closed for client: {addr}")

def main():
    global game
    start_new_thread(game_thread, ())
    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)
        unique_id = str(uuid.uuid4())
        color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
        game.add_player(unique_id, color=color)
        start_new_thread(client_thread, (unique_id, conn, addr))

if __name__ == "__main__":
    main()