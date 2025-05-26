# Online-Snake

A secure, multiplayer online Snake game built in Python, featuring real-time gameplay and encrypted client-server communication.

## Features

- **Multiplayer Support:** Play Snake with multiple players in real time.
- **Secure Networking:** Utilizes RSA and Fernet symmetric encryption to secure all communications between client and server.
- **Real-Time Gameplay:** Smooth, responsive controls using Pygame.
- **Chat System:** Send quick in-game chat messages via keyboard shortcuts.
- **Colorful Visuals:** Each player’s snake is assigned a unique color for easy distinction.
- **Reset & Quit Controls:** Players can reset their snake or leave the game at any time.
- **Snack Generation:** Snacks appear on the board for snakes to consume and grow.

## Architecture

- **Server (`snake_server.py`):**
  - Handles incoming client connections using sockets and threading.
  - Manages game state (`SnakeGame`), player snakes, and snack positions.
  - Broadcasts real-time game state to all connected clients.
  - Supports simple chat messages (predefined phrases).

- **Client (`snake_client.py`):**
  - Connects to the server, performs a secure key exchange, and handles encryption.
  - Renders the game board and snakes using Pygame.
  - Sends movement and chat commands to the server.
  - Receives and displays the current game state and chat messages.

- **Game Logic (`snake.py`):**
  - Implements the `SnakeGame`, `snake`, and `cube` classes.
  - Handles movement, collision, snack generation, and rendering.

- **Test (`test.py`):**
  - Provides a basic test for RSA encryption/decryption.

## Installation & Requirements

- Python 3.7+
- `pygame`
- `rsa`
- `cryptography`

Install required packages:
```bash
pip install pygame rsa cryptography

```

## Usage

### Start the Server

```bash
python snake_server.py
```

### Start One or More Clients

```bash
python snake_client.py
```

### Controls (Client)

- **Arrow keys:** Move snake
- **R:** Reset snake
- **Q:** Quit game
- **Z, X, C:** Send predefined chat messages

---

## Security

- **Hybrid Encryption:** The client and server perform an RSA key exchange, then use a Fernet (symmetric) key for fast, secure communication.
- **Encrypted Game State:** All messages (commands and game state) are encrypted during transmission.

---

## Customization

- Edit predefined chat messages or add new ones in both `snake_client.py` and `snake_server.py`.
- Modify game constants (board size, colors, etc.) at the top of the respective files.

---

## Project Structure

```
snake_server.py    # Server logic and networking
snake_client.py    # Client logic and interface
snake.py           # Game logic and classes
test.py            # Simple RSA encryption test
```


