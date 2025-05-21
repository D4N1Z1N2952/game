import os
import sys
import time
import tty
import termios
import json

# ANSI color codes
ANSI = {
    "BLACK": "\033[30m", "RED": "\033[31m", "GREEN": "\033[32m",
    "YELLOW": "\033[33m", "BLUE": "\033[34m", "MAGENTA": "\033[35m",
    "CYAN": "\033[36m", "WHITE": "\033[37m", "LIGHTBLACK_EX": "\033[90m",
    "LIGHTRED_EX": "\033[91m", "LIGHTGREEN_EX": "\033[92m", "LIGHTYELLOW_EX": "\033[93m",
    "LIGHTBLUE_EX": "\033[94m", "LIGHTMAGENTA_EX": "\033[95m", "LIGHTCYAN_EX": "\033[96m",
    "LIGHTWHITE_EX": "\033[97m", "RESET": "\033[0m"
}

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 24, 21
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERDATA_PATH = os.path.join(SCRIPT_DIR, "playerdata.json")
GAMEDATA_PATH = os.path.join(SCRIPT_DIR, "gamedata.json")
LANDSCAPE_PATH = os.path.join(SCRIPT_DIR, "lanscape.json")

# Load landscape
if os.path.exists(LANDSCAPE_PATH):
    with open(LANDSCAPE_PATH, 'r') as f:
        landscape = json.load(f)
else:
    print("Warning: landscape.json not found.")

# Load player data
if os.path.exists(PLAYERDATA_PATH):
    with open(PLAYERDATA_PATH, 'r') as f:
        playerdata = json.load(f)
    last_x = playerdata.get('last_location', {}).get('x', 0)
    last_y = playerdata.get('last_location', {}).get('y', 0)
    inventory = [
        (item.get('id', 'none'), item.get('quantity', 0))
        for key, item in sorted(
            playerdata.get('inventory', {}).items(),
            key=lambda x: int(x[0][4:])  # Extract the number after 'item'
        )
    ]
    while len(inventory) < 10:
        inventory.append(('none', 0))
else:
    print("Warning: playerdata.json not found.")
    last_x, last_y = 0, 0

# Load game data
if os.path.exists(GAMEDATA_PATH):
    with open(GAMEDATA_PATH, 'r') as f:
        gamedata = json.load(f)
else:
    print("Warning: gamedata.json not found.")

player_x, player_y = last_x, last_y
inventory_slot = 1
block_place = "up"

# Utility functions
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def print_colored(symbol, color):
    print(ANSI.get(color, ANSI["RESET"]) + symbol + ANSI["RESET"], end="")

# Drawing functions
def draw_inventory_slot(y, slot):
    print_colored("◾", "WHITE" if (y // 2) + 1 == slot else "YELLOW")

def draw_inventory_block(x, y, row_y):
    if y == row_y:
        block_id = inventory[x][0]
        if block_id == "none":
            print_colored("◾", "WHITE")
        elif block_id in gamedata["blocks"]:
            print(gamedata["blocks"][block_id]["color"], end="")
        else:
            print_colored("?", "RED")

def draw_inventory_quantity(y):
    idx = (y // 2) - 1
    if 0 <= idx < len(inventory):
        print(str(inventory[idx][1]).ljust(2), end="")

def draw_landscape_block(x, y):
    block_id = landscape.get("y", {}).get(str(y), {}).get(str(x), "none")
    if block_id == "none":
        print_colored("◾", "GREEN")
    elif block_id in gamedata["blocks"]:
        print(gamedata["blocks"][block_id]["color"], end="")
    else:
        print_colored("?", "RED")

def print_landscape(slot, place="up"):
    show_x, show_y = player_x, player_y
    if place == "up" and player_y > 0:
        show_y -= 1
    elif place == "down" and player_y < WINDOW_HEIGHT - 1:
        show_y += 1
    elif place == "left" and player_x > 0:
        show_x -= 1
    elif place == "right" and player_x < WINDOW_WIDTH - 1:
        show_x += 1

    for y in range(WINDOW_HEIGHT):
        for x in range(WINDOW_WIDTH):
            if x == 21 and y in range(1, 21, 2):
                draw_inventory_slot(y, slot)
            elif x == 22 and y % 2 != 0:
                draw_inventory_block((y - 1) // 2, y, y)
            elif x == 22 and y % 2 == 0 and y != 0:
                draw_inventory_quantity(y)
            elif x == player_x and y == player_y:
                print_colored("◾", "BLUE")
            elif x == show_x and y == show_y:
                print_colored("◾", "WHITE")
            elif x >= 21:
                print_colored("◾", "YELLOW")
            else:
                draw_landscape_block(x, y)
        print()

# Block interaction
def place_block():
    global landscape, inventory
    dx, dy = player_x, player_y
    if block_place == "up" and dy > 0:
        dy -= 1
    elif block_place == "down" and dy < WINDOW_HEIGHT - 1:
        dy += 1
    elif block_place == "left" and dx > 0:
        dx -= 1
    elif block_place == "right" and dx < WINDOW_WIDTH - 1:
        dx += 1

    # Get the block from the selected inventory slot (inventory_slot is 1-based)
    slot_idx = inventory_slot - 1
    block_id, quantity = inventory[slot_idx]

    # Only place if there is a block and quantity > 0
    if block_id != "none" and quantity > 0:
        if "y" not in landscape:
            landscape["y"] = {}
        if str(dy) not in landscape["y"]:
            landscape["y"][str(dy)] = {}
        landscape["y"][str(dy)][str(dx)] = block_id
        # Decrease quantity in inventory
        inventory[slot_idx] = (block_id, quantity - 1)

def break_block():
    global landscape, inventory
    dx, dy = player_x, player_y
    if block_place == "up" and dy > 0:
        dy -= 1
    elif block_place == "down" and dy < WINDOW_HEIGHT - 1:
        dy += 1
    elif block_place == "left" and dx > 0:
        dx -= 1
    elif block_place == "right" and dx < WINDOW_WIDTH - 1:
        dx += 1

    block_id = landscape.get("y", {}).get(str(dy), {}).get(str(dx))
    if block_id not in (None, "none"):
        # Add the block to inventory
        for i, (inv_id, qty) in enumerate(inventory):
            if inv_id == block_id:
                inventory[i] = (inv_id, qty + 1)
                break
        else:
            # If not found, add to first empty slot
            for i, (inv_id, qty) in enumerate(inventory):
                if inv_id == "none":
                    inventory[i] = (block_id, 1)
                    break
        # Remove the block from the landscape
        landscape["y"][str(dy)][str(dx)] = "none"

# Game loop
move_actions = {
    "w": lambda x, y: (x, y - 1) if y > 0 else (x, y),
    "s": lambda x, y: (x, y + 1) if y < WINDOW_HEIGHT - 1 else (x, y),
    "a": lambda x, y: (x - 1, y) if x > 0 else (x, y),
    "d": lambda x, y: (x + 1, y) if x < WINDOW_WIDTH - 1 else (x, y),
}
block_places = {"i": "up", "k": "down", "j": "left", "l": "right"}

while True:
    print("\033[H\033[J", end="")  # Clear screen
    print_landscape(inventory_slot, block_place)
    print(f"x: {player_x} y: {player_y} q: save and quit")

    key = get_key()

    if key in move_actions:
        # Calculate the intended new position
        new_x, new_y = move_actions[key](player_x, player_y)
        # Check for collision with "rock"
        block_id = landscape.get("y", {}).get(str(new_y), {}).get(str(new_x), "none")
        if block_id != "rock":
            player_x, player_y = new_x, new_y
        # else: do not move if there is a rock
    elif key == "q":
        try:
            playerdata = {
                "last_location": {"x": player_x, "y": player_y},
                "inventory": {
                    f"item{i+1}": {"id": inventory[i][0], "quantity": inventory[i][1]}
                    for i in range(len(inventory))
                }
            }
            with open(PLAYERDATA_PATH, 'w') as f:
                json.dump(playerdata, f, indent=4)
            with open(LANDSCAPE_PATH, 'w') as f:
                json.dump(landscape, f, indent=4)
            print("Game saved.")
            time.sleep(1)
        except Exception as e:
            print(f"Error saving game: {e}")
            time.sleep(2)
        break
    elif key in "1234567890":
        inventory_slot = int(key) if key != "0" else 10
    elif key in block_places:
        block_place = block_places[key]
    elif key == "z":
        place_block()
    elif key == "x":
        break_block()

    if player_x >= WINDOW_WIDTH - 3:
        player_x = WINDOW_WIDTH - 4

    time.sleep(0.1)
