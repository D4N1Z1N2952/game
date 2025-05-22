import os, sys, time, tty, termios, json

# === Constants & Paths ===
WINDOW_WIDTH, WINDOW_HEIGHT = 24, 21
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERDATA_PATH = os.path.join(SCRIPT_DIR, "playerdata.json")
GAMEDATA_PATH = os.path.join(SCRIPT_DIR, "gamedata.json")
LANDSCAPE_PATH = os.path.join(SCRIPT_DIR, "lanscape.json")
ANSI = {
    "BLACK": "\033[30m", "RED": "\033[31m", "GREEN": "\033[32m", "YELLOW": "\033[33m",
    "BLUE": "\033[34m", "MAGENTA": "\033[35m", "CYAN": "\033[36m", "WHITE": "\033[37m",
    "LIGHTBLACK_EX": "\033[90m", "LIGHTRED_EX": "\033[91m", "LIGHTGREEN_EX": "\033[92m",
    "LIGHTYELLOW_EX": "\033[93m", "LIGHTBLUE_EX": "\033[94m", "LIGHTMAGENTA_EX": "\033[95m",
    "LIGHTCYAN_EX": "\033[96m", "LIGHTWHITE_EX": "\033[97m", "RESET": "\033[0m"
}
title = "█▄▄ █   █▀█ █▀▀ █▄▀ █▀▀ █▀█ █ █▀▄  █▀▀ █▀█ █▀█ █▀▀ █▀▀\n█▄█ █▄▄ █▄█ █▄▄ █ █ █▄█ █▀▄ █ █▄▀  █▀  █▄█ █▀▄ █▄█ ██▄"

# === Data Loading ===
def load_json(path, default=None):
    if os.path.exists(path):
        with open(path) as f: return json.load(f)
    print(f"Warning: {os.path.basename(path)} not found.")
    return default

landscape = load_json(LANDSCAPE_PATH, {"y": {}})
gamedata = load_json(GAMEDATA_PATH, {"blocks": {}})
playerdata = load_json(PLAYERDATA_PATH, {})
selected_y = 1

# Player state
last_x = playerdata.get('last_location', {}).get('x', 0)
last_y = playerdata.get('last_location', {}).get('y', 0)
inventory = [
    (item.get('id', 'none'), item.get('quantity', 0))
    for key, item in sorted(
        playerdata.get('inventory', {}).items(),
        key=lambda x: int(x[0][4:])
    )
] if playerdata else []
while len(inventory) < 10:
    inventory.append(('none', 0))
player_x, player_y = last_x, last_y
inventory_slot, block_place = 1, "up"

# === Utility Functions ===
def get_key():
    fd, old = sys.stdin.fileno(), termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def print_colored(symbol, color):
    print(ANSI.get(color, ANSI["RESET"]) + symbol + ANSI["RESET"], end="")

def get_block(x, y): return landscape.get("y", {}).get(str(y), {}).get(str(x), "none")
def set_block(x, y, block_id):
    landscape.setdefault("y", {}).setdefault(str(y), {})[str(x)] = block_id

def new_game():
    global landscape, inventory, player_x, player_y
    # Reset landscape: all "none"
    landscape = {"y": {str(y): {str(x): "none" for x in range(WINDOW_WIDTH)} for y in range(WINDOW_HEIGHT)}}
    # Reset inventory: all empty
    inventory = [("none", 0) for _ in range(10)]
    # Reset player position
    player_x, player_y = 0, 0
    # Save to files
    pdata = {
        "last_location": {"x": player_x, "y": player_y},
        "inventory": {f"item{i+1}": {"id": "none", "quantity": 0} for i in range(10)}
    }
    with open(PLAYERDATA_PATH, 'w') as f:
        json.dump(pdata, f, indent=4)
    with open(LANDSCAPE_PATH, 'w') as f:
        json.dump(landscape, f, indent=4)
    print("New game started. Inventory and landscape reset.")
    time.sleep(1)
# === Drawing Functions ===
def draw_inventory_slot(y, slot):
    print_colored("◾", "WHITE" if (y // 2) + 1 == slot else "YELLOW")

def draw_inventory_block(x, y):
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
    block_id = get_block(x, y)
    if block_id == "none":
        print_colored("◾", "MAGENTA")
    elif block_id in gamedata["blocks"]:
        print(gamedata["blocks"][block_id]["color"], end="")
    else:
        print_colored("?", "RED")

def print_landscape(slot, place="up"):
    show_x, show_y = player_x, player_y
    if place == "up" and player_y > 0: show_y -= 1
    elif place == "down" and player_y < WINDOW_HEIGHT - 1: show_y += 1
    elif place == "left" and player_x > 0: show_x -= 1
    elif place == "right" and player_x < WINDOW_WIDTH - 1: show_x += 1

    for y in range(WINDOW_HEIGHT):
        for x in range(WINDOW_WIDTH):
            if x == 21 and y in range(1, 21, 2):
                draw_inventory_slot(y, slot)
            elif x == 22 and y % 2 != 0:
                draw_inventory_block((y - 1) // 2, y)
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

# === Block Interaction ===
def place_block():
    global inventory
    dx, dy = player_x, player_y
    if block_place == "up" and dy > 0: dy -= 1
    elif block_place == "down" and dy < WINDOW_HEIGHT - 1: dy += 1
    elif block_place == "left" and dx > 0: dx -= 1
    elif block_place == "right" and dx < WINDOW_WIDTH - 1: dx += 1
    slot_idx = inventory_slot - 1
    block_id, quantity = inventory[slot_idx]
    if block_id != "none" and quantity > 0 and get_block(dx, dy) == "none":
        set_block(dx, dy, block_id)
        inventory[slot_idx] = (block_id, quantity - 1)

def break_block():
    global inventory
    dx, dy = player_x, player_y
    if block_place == "up" and dy > 0: dy -= 1
    elif block_place == "down" and dy < WINDOW_HEIGHT - 1: dy += 1
    elif block_place == "left" and dx > 0: dx -= 1
    elif block_place == "right" and dx < WINDOW_WIDTH - 1: dx += 1
    block_id = get_block(dx, dy)
    if block_id not in (None, "none"):
        for i, (inv_id, qty) in enumerate(inventory):
            if inv_id == block_id:
                inventory[i] = (inv_id, qty + 1)
                break
        else:
            for i, (inv_id, qty) in enumerate(inventory):
                if inv_id == "none":
                    inventory[i] = (block_id, 1)
                    break
        set_block(dx, dy, "none")

# === Game Loop & Menu ===
move_actions = {
    "w": lambda x, y: (x, y - 1) if y > 0 else (x, y),
    "s": lambda x, y: (x, y + 1) if y < WINDOW_HEIGHT - 1 else (x, y),
    "a": lambda x, y: (x - 1, y) if x > 0 else (x, y),
    "d": lambda x, y: (x + 1, y) if x < WINDOW_WIDTH - 1 else (x, y),
}
block_places = {"i": "up", "k": "down", "j": "left", "l": "right"}

def intro(title):
    global selected_y
    while True:
        print("\033[H\033[J\n")
        print(title.center(60))
        print("\n" * 2)
        print(" " * 20 + ("[ Continue ]" if selected_y == 1 else "  Continue  ").center(20))
        print("\n" * 2)
        print(" " * 20 + ("[ New Game ]" if selected_y == 2 else "  New Game  ").center(20))
        print("\n" * 2)
        print(" " * 20 + ("[ Options ]" if selected_y == 3 else "  Options   ").center(20))
        print("\n" * 2)
        print(" " * 20 + ("[ Quit ]" if selected_y == 4 else "   Quit     ").center(20))
        print("\n" * 2)
        key = get_key()
        if key == "w":
            selected_y = 4 if selected_y == 1 else selected_y - 1
        elif key == "s":
            selected_y = 1 if selected_y == 4 else selected_y + 1
        elif key in ("\n", "\r"):
            return selected_y
        time.sleep(0.1)

selected_y = 1  # Make sure this is set before calling intro
n = intro(title)
if n == 1:
    print("Loading last save..."); time.sleep(1)
elif n == 2:
    print("Starting new game..."); time.sleep(1)
    new_game()
elif n == 3:
    print("Options menu (not implemented yet)."); time.sleep(1)
    # Implement your options menu here
    n = 1
    n = intro(title)
elif n == 4:
    print("Exiting game..."); time.sleep(1); sys.exit(0)

while True:
    print("\033[H\033[J", end="")
    print_landscape(inventory_slot, block_place)
    print(f"x: {player_x} y: {player_y} q: save and quit")
    key = get_key()
    if key in move_actions:
        nx, ny = move_actions[key](player_x, player_y)
        if get_block(nx, ny) not in ("rock", "grass"):
            player_x, player_y = nx, ny
    elif key == "q":
        try:
            pdata = {
                "last_location": {"x": player_x, "y": player_y},
                "inventory": {f"item{i+1}": {"id": inventory[i][0], "quantity": inventory[i][1]} for i in range(len(inventory))}
            }
            with open(PLAYERDATA_PATH, 'w') as f: json.dump(pdata, f, indent=4)
            with open(LANDSCAPE_PATH, 'w') as f: json.dump(landscape, f, indent=4)
            print("Game saved."); time.sleep(1)
        except Exception as e:
            print(f"Error saving game: {e}"); time.sleep(2)
        break
    elif key in "1234567890":
        inventory_slot = int(key) if key != "0" else 10
    elif key in block_places:
        block_place = block_places[key]
    elif key == "z":
        place_block()
    elif key == "x":
        break_block()
    if player_x >= WINDOW_WIDTH - 3: player_x = WINDOW_WIDTH - 4
    time.sleep(0.1)