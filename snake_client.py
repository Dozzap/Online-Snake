import socket
import pygame
import sys
import time


# Initialize Pygame
pygame.init()

# Game window dimensions
WIDTH, HEIGHT = 500, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Define colors for the snake and snacks
SNAKE_COLOR = (255, 0, 0)  # Red color for the snake
SNACK_COLOR = (0, 255, 0)  # Green color for the snacks
CELL_SIZE = 25  # Size of each cell in the grid
GRID_COLOR = (255, 255, 255)  # Color of the grid lines
# Server details
SERVER_IP = 'localhost'  # Replace with your server's IP
SERVER_PORT = 5555       # Replace with your server's port
BUFFER_SIZE = 500        # Size of the buffer for receiving data

# Connect to the server
def connect_to_server():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        return client_socket
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        sys.exit()

# Send command to the server
def send_command(client_socket, command):
    try:
        client_socket.send(command.encode())
    except socket.error as e:
        print(f"Error sending command: {e}")

# Receive game state from the server
def receive_game_state(client_socket):
    print("Attempting to receive game state")
    try:
        print("Receiving game state")
        game_state = client_socket.recv(BUFFER_SIZE).decode()
        print(game_state)
        return game_state
    except socket.error as e:
        print(f"Error receiving game state: {e}")
        return ""
    
# Parse the game state received from the server
def parse_game_state(game_state):
    try:
        snake_data, snack_data = game_state.split('|')
        snake_positions = [tuple(map(int, pos.strip('()').split(','))) for pos in snake_data.split('*') if pos]
        snack_positions = [tuple(map(int, pos.strip('()').split(','))) for pos in snack_data.split('**') if pos]
        return snake_positions, snack_positions
    except Exception as e:
        print(f"Error parsing game state: {e}")
        return [], []

# Draw the grid lines    
def draw_grid():
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

# Draw the snake and snacks
def draw_snake_and_snacks(screen, snake_positions, snack_positions):
    for pos in snake_positions:
        pygame.draw.rect(screen, SNAKE_COLOR, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for pos in snack_positions:
        pygame.draw.rect(screen, SNACK_COLOR, (pos[0] * CELL_SIZE, pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# Main function
def main():
    client_socket = connect_to_server()
    running = True
    while running:

        events = pygame.event.get()

        if events != []:
            
            event = events[0] 

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    send_command(client_socket, "up")
                elif event.key == pygame.K_DOWN:
                    send_command(client_socket, "down")
                elif event.key == pygame.K_LEFT:
                    send_command(client_socket, "left")
                elif event.key == pygame.K_RIGHT:
                    send_command(client_socket, "right")
                elif event.key == pygame.K_r:
                    send_command(client_socket, "reset")
                elif event.key == pygame.K_q:
                    send_command(client_socket, "quit")
                    running = False
                elif event.key == pygame.K_z:
                    send_command(client_socket, "z")
                elif event.key == pygame.K_x:
                    send_command(client_socket, "x")
                elif event.key == pygame.K_c:
                    send_command(client_socket, "c")
            else:
                send_command(client_socket, "get")
        else:
            send_command(client_socket, "get") 
        
        game_state = receive_game_state(client_socket)
        print(game_state)
        snake_positions, snack_positions = parse_game_state(game_state)

        # Clear the screen
        screen.fill((0, 0, 0))  
        draw_grid()
        draw_snake_and_snacks(screen,snake_positions, snack_positions)
        pygame.display.update()

        # Delay to control update frequency and reduce CPU usage
        time.sleep(0.2)

    client_socket.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

