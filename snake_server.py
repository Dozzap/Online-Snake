import socket
from _thread import *
import numpy as np
import rsa
from snake import SnakeGame
import uuid
import time 


# server = "10.11.250.207"
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0 
rows = 20 

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
# s.settimeout(0.5)
print("Waiting for a connection, Server Started")


game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()


# Generate RSA key pair for the server
(server_public_key, server_private_key) = rsa.newkeys(512)

# Dictionary to store each client's public key
client_public_keys = {}

def decrypt_message(encrypted_message, server_private_key):
    try:
        return rsa.decrypt(encrypted_message, server_private_key).decode()
    except Exception as e:
        print("Decryption failed:", e)
        return None

def encrypt_message(message, client_public_key):
    return rsa.encrypt(message.encode(), client_public_key)

def game_thread() : 
    global game, moves_queue, game_state 
    while True :
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval : 
            time.sleep(0.1) 



rgb_colors = {
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "yellow" : (255, 255, 0),
    "orange" : (255, 165, 0),
} 
rgb_colors_list = list(rgb_colors.values())

def client_thread(unique_id,conn, addr):
    try:
        # Send the server's public key to the client
        conn.send(server_public_key.save_pkcs1(format='PEM'))

        # Receive the client's public key
        client_public_key_data = conn.recv(2048)
        if not client_public_key_data:
            raise ValueError("Failed to receive client's public key")

        client_public_key = rsa.PublicKey.load_pkcs1(client_public_key_data, 'PEM')
        client_public_keys[addr] = client_public_key

        while True:
            encrypted_data = conn.recv(1024)
            if not encrypted_data:
                print(f"Connection closed by client: {addr}")
                break
            print(f"encrypted_data: {encrypted_data}")
            decrypted_data = decrypt_message(encrypted_data, server_private_key)
            print(f"Received message from client: {decrypted_data}")
            
            if decrypted_data is None:
                print(f"Failed to decrypt message from client: {decrypted_data}")
                continue


            data_HEADER, data_CONTENT = decrypted_data.split(":")

            if data_HEADER == "CONTROL":
                # Handle control commands like up, down, left, right, reset, quit, get
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
                else:
                    print(f"Invalid control command from client: {addr}")

            elif data_HEADER == "CHAT":
                pass
                # # Handle chat messages
                # if data_CONTENT in predefined_messages:
                #     print(predefined_messages[data_CONTENT])
                #     # Here, you can broadcast this message to other clients if needed
                # else:
                #     print(f"Invalid chat command from client: {addr}")

            # Send the game state (unencrypted)
            conn.send(game_state.encode())

            # Optionally, send encrypted responses to certain messages here
            # Example: encrypted_response = encrypt_message("Response", client_public_key)
            # conn.send(encrypted_response)

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        game.remove_player(unique_id)
        conn.close()
        print(f"Connection closed for client: {addr}")

def main():
    global game

    start_new_thread(game_thread, ())  # Start the game thread

    while True:
        conn, addr = s.accept()  # Accept new connections within the loop
        print("Connected to:", addr)

        unique_id = str(uuid.uuid4())
        color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
        game.add_player(unique_id, color=color)

        # Start a new client thread for each connection
        start_new_thread(client_thread, (unique_id, conn, addr))

    # Close the server socket if you ever break out of the loop (optional)
    s.close()

if __name__ == "__main__":
    main()