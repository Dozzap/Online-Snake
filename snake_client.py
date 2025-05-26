import socket
import pygame
import sys
import time
import rsa
import json
from cryptography.fernet import Fernet
import traceback
# Initialize Pygame
pygame.init()

# Game window dimensions and other constants
WIDTH, HEIGHT = 500, 500
CELL_SIZE = 25
GRID_COLOR = (255, 255, 255)
SNACK_COLOR = (0, 255, 0)
SERVER_IP = 'localhost'
SERVER_PORT = 5555
BUFFER_SIZE = 4096

predefined_messages = {
    "Z": "Congratulations!",
    "X": "It works!",
    "C": "Ready?"
}

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

def connect_to_server():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))

        # RSA Key Exchange
        client_public_key, client_private_key = rsa.newkeys(2048)
        sock.send(client_public_key.save_pkcs1(format='PEM'))
        server_public_key_data = sock.recv(2048)
        server_public_key = rsa.PublicKey.load_pkcs1(server_public_key_data, format='PEM')

        # Fernet Key Exchange (hybrid)
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        encrypted_fernet_key = rsa.encrypt(fernet_key, server_public_key)
        sock.send(encrypted_fernet_key)

        return sock, fernet
    except socket.error as e:
        print(f"Decryption/parse error: {e}")
        traceback.print_exc()
        sys.exit()

def send_command(sock, message, fernet):
    msg_json = json.dumps({"command": message})
    encrypted_message = fernet.encrypt(msg_json.encode())
    send_with_length(sock, encrypted_message)

def receive_game_state(sock, fernet):
    try:
        encrypted_response = recv_with_length(sock)
        response_str = fernet.decrypt(encrypted_response).decode()
        response = json.loads(response_str)
        return response
    except Exception as e:
        print(f"Error receiving game state: {e}")
        return None

def draw_grid(screen):
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

def parse_game_state(response):
    try:
        snakes = response["snakes"]
        snacks = response["snacks"]
        message = response.get("chat_message")
        return snakes, snacks, message
    except Exception as e:
        print(f"Decryption/parse error: {e}")
        traceback.print_exc()
        return [], [], None

def draw_snake_and_snacks(screen, snakes, snacks):
    for snake in snakes:
        color = tuple(snake["color"])
        positions = snake["positions"]
        # Draw the head differently (e.g., white border or different color)
        if positions:
            head = positions[0]
            # Draw head with a border (white)
            pygame.draw.rect(screen, (255, 255, 255), (head[0] * CELL_SIZE, head[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, color, (head[0] * CELL_SIZE + 3, head[1] * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6))
            # Optionally, draw "eyes":
            centre_x = head[0] * CELL_SIZE + CELL_SIZE // 2
            centre_y = head[1] * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(screen, (0, 0, 0), (centre_x - 4, centre_y - 4), 2)
            pygame.draw.circle(screen, (0, 0, 0), (centre_x + 4, centre_y - 4), 2)
        # Draw the rest of the snake body
        for pos in positions[1:]:
            pygame.draw.rect(screen, color, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for pos in snacks:
        pygame.draw.rect(screen, SNACK_COLOR, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    client_socket, fernet = connect_to_server()
    running = True
    snakes, snacks, message = [], [], None
    last_seen_message = None  # track last chat message

    while running:
        button_pressed = ""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    button_pressed = "CONTROL:up"
                elif event.key == pygame.K_DOWN:
                    button_pressed = "CONTROL:down"
                elif event.key == pygame.K_LEFT:
                    button_pressed = "CONTROL:left"
                elif event.key == pygame.K_RIGHT:
                    button_pressed = "CONTROL:right"
                elif event.key == pygame.K_r:
                    button_pressed = "CONTROL:reset"
                elif event.key == pygame.K_q:
                    button_pressed = "CONTROL:quit"
                    running = False
                elif event.key == pygame.K_z:
                    button_pressed = "CHAT:Z"
                elif event.key == pygame.K_x:
                    button_pressed  = "CHAT:X"
                elif event.key == pygame.K_c:
                    button_pressed = "CHAT:C"
        if len(button_pressed) == 0:
            button_pressed = "CONTROL:get"
        send_command(client_socket, button_pressed, fernet)

        response = receive_game_state(client_socket, fernet)
        if response:
            try:
                snakes, snacks, message = parse_game_state(response)
            except Exception as e:
                print(f"Decryption/parse error: {e}")
                traceback.print_exc()
                snakes, snacks, message = [], [], None
        else:
            continue

        if message and message != last_seen_message:
            print(f"{message}")
            last_seen_message = message

        screen.fill((0, 0, 0))
        draw_grid(screen)
        draw_snake_and_snacks(screen, snakes, snacks)
        pygame.display.update()
        time.sleep(0.2)

    client_socket.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()