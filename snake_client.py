import socket
import pygame
import sys
import time
import rsa

# Initialize Pygame
pygame.init()

# Game window dimensions and other constants
WIDTH, HEIGHT = 500, 500
CELL_SIZE = 25
GRID_COLOR = (255, 255, 255)
SNAKE_COLOR = (255, 0, 0)
SNACK_COLOR = (0, 255, 0)
SERVER_IP = 'localhost'
SERVER_PORT = 5555
BUFFER_SIZE = 500

predefined_messages = {
    "Z": "Player says: Congratulations!",
    "X": "Player says: It works!",
    "C": "Player says: Ready?"
}

# Connect to the server and setup RSA
def connect_to_server():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))

        # Generate RSA key pair for the client
        client_public_key, client_private_key = rsa.newkeys(512)

        # Send the client's public key to the server
        sock.send(client_public_key.save_pkcs1(format='PEM'))

        # Receive the server's public key and load it
        server_public_key_data = sock.recv(2048)
        server_public_key = rsa.PublicKey.load_pkcs1(server_public_key_data, format='PEM')
        
        return sock, client_private_key, server_public_key
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit()

# Encrypt and send message to the server
def send_command(sock, message, server_public_key):
    try:
        encrypted_message = rsa.encrypt(message.encode(), server_public_key)
        sock.send(encrypted_message)
    except socket.error as e:
        print(f"Error sending command: {e}")

# Receive and decode game state from the server
def receive_game_state(sock):
    try:
        return sock.recv(BUFFER_SIZE).decode()
    except socket.error as e:
        print(f"Error receiving game state: {e}")
        return ""

# Parsing the game state received from the server
def parse_game_state(game_state):
    try:
        snake_data, snack_data = game_state.split('|')
        snake_positions = [tuple(map(int, pos.strip('()').split(','))) for pos in snake_data.split('*') if pos]
        snack_positions = [tuple(map(int, pos.strip('()').split(','))) for pos in snack_data.split('**') if pos]
        return snake_positions, snack_positions
    except Exception as e:

        print(f"Error parsing game state: {e}")
        return [], []

# Drawing functions
def draw_grid(screen):
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

def draw_snake_and_snacks(screen, snake_positions, snack_positions):
    for pos in snake_positions:
        pygame.draw.rect(screen, SNAKE_COLOR, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for pos in snack_positions:
        pygame.draw.rect(screen, SNACK_COLOR, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# Main function
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    client_socket, client_private_key, server_public_key = connect_to_server()
    
    running = True
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
                send_command(client_socket, "CONTROL:get",server_public_key)
        send_command(client_socket, button_pressed, server_public_key)

        game_state = receive_game_state(client_socket)
        snake_positions, snack_positions = parse_game_state(game_state)

        screen.fill((0, 0, 0))
        draw_grid(screen)
        draw_snake_and_snacks(screen, snake_positions, snack_positions)
        pygame.display.update()
        time.sleep(0.2)

    client_socket.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

