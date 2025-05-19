import time
import sys
import tty
import termios
import json
import os

# ANSI color codes
ANSI_COLORS ={
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "LIGHTBLACK_EX": "\033[90m",
    "LIGHTRED_EX": "\033[91m",
    "LIGHTGREEN_EX": "\033[92m",
    "LIGHTYELLOW_EX": "\033[93m",
    "LIGHTBLUE_EX": "\033[94m",
    "LIGHTMAGENTA_EX": "\033[95m",
    "LIGHTCYAN_EX": "\033[96m",
    "LIGHTWHITE_EX": "\033[97m",
    "RESET": "\033[0m"
}

#constants
WINDOW_WIDTH = 24
WINDOW_HEIGHT = 21
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERDATA_PATH = os.path.join(SCRIPT_DIR, "playerdata.json")
GAMEDATA_PATH = os.path.join(SCRIPT_DIR, "gamedata.json")

# Load player data
if os.path.exists(PLAYERDATA_PATH):
    with open(PLAYERDATA_PATH, 'r') as i:
        playerdata = json.load(i)
    last_x = playerdata.get('last_location', {}).get('x', 0)
    last_y = playerdata.get('last_location', {}).get('y', 0)
    inventory = []
    for key in sorted(playerdata.get('inventory', {})):
        item = playerdata['inventory'][key]
        inventory.append((item.get('id', 'none'), item.get('quantity', 0)))
    # Ensure inventory has 10 slots
    while len(inventory) < 10:
        inventory.append(('none', 0))
else:
    print("Warning: playerdata.json not found.")
    last_x = 0
    last_y = 0
    inventory = [('none', 0)] * 10

# Load game data
if os.path.exists(GAMEDATA_PATH):
    with open(GAMEDATA_PATH, 'r') as j:
        gamedata = json.load(j)
else:
    print("Warning: gamedata.json not found.")
    gamedata = {"blocks": {}}

player_x = last_x
player_y = last_y

######################################################################

def test_for_inventory_block(x, y, loop_turn):
    if y == loop_turn:
        block_id = inventory[x][0]
        if block_id == 'none':
            print(ANSI_COLORS["WHITE"] + "◾" + ANSI_COLORS["RESET"], end="")
        elif block_id in gamedata["blocks"]:
            color_str = gamedata["blocks"][block_id]["color"]
            print(color_str, end="")
        else:
            print(ANSI_COLORS["RED"] + "?" + ANSI_COLORS["RESET"], end="")  # Unknown block

def test_for_inventory_quantity(item):
    # Only print the quantity for the correct inventory slot
    qty = inventory[item][1]
    if qty > 9:
        print(str(qty), end="")
    else:
        print(str(qty) + " ", end="")

def test_for_inventory_slot(num, slot):
    if slot == num:
        print(ANSI_COLORS["WHITE"] + "◾" + ANSI_COLORS["RESET"], end="")
    else:
        print(ANSI_COLORS["YELLOW"] + "◾" + ANSI_COLORS["RESET"], end="")

def print_landscape(slot, place="up"):
    for y in range(WINDOW_HEIGHT):
        for x in range(WINDOW_WIDTH):
            # Inventory and UI columns
            if x == 21 and y in range(1, 21, 2):
                test_for_inventory_slot((y // 2) + 1, slot)
            elif x == 22 and y % 2 != 0:
                for idx, loop_y in enumerate(range(1, 20, 2)):
                    if y == loop_y:
                        test_for_inventory_block(idx, y, loop_y)
            elif x == 22 and y % 2 == 0 and y != 0:
                idx = (y // 2) - 1
                if 0 <= idx < len(inventory):
                    test_for_inventory_quantity(idx)
            elif x >= 21:
                print(ANSI_COLORS["YELLOW"] + "◾" + ANSI_COLORS["RESET"], end="")
            elif x == player_x and y == player_y:
                print(ANSI_COLORS["BLUE"] + "◾" + ANSI_COLORS["RESET"], end="")
            else:
                print(ANSI_COLORS["GREEN"] + "◾" + ANSI_COLORS["RESET"], end="")
        print()
    # Optionally print inventory for debugging
    # print(inventory)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

######################################################################
inventory_slot = 1
block_place = "up"
break_selected_block = False

while True:
    # Clear the screen
    print("\033[H\033[J", end="")

    # Print the game window
    print_landscape(inventory_slot)

    print(f"x: {player_x} y: {player_y} q: save and quit")

    # Detect key presses
    key = get_key()
    if key == "w" and player_y > 0:
        player_y -= 1
    elif key == "s" and player_y < WINDOW_HEIGHT - 1:
        player_y += 1
    elif key == "a" and player_x > 0:
        player_x -= 1
    elif key == "d" and player_x < WINDOW_WIDTH - 1:
        player_x += 1
    elif key == "q":
        try:
            if os.path.exists(PLAYERDATA_PATH):
                with open(PLAYERDATA_PATH, 'r') as j:
                    playerdata = json.load(j)
            else:
                playerdata = {"last_location": {}, "inventory": {}}
            playerdata['last_location']['x'] = player_x
            playerdata['last_location']['y'] = player_y
            with open(PLAYERDATA_PATH, 'w') as j:
                json.dump(playerdata, j, indent=4)
            print(f"Saving last location: x = {player_x}, y = {player_y}")
            time.sleep(1)
        except Exception as e:
            print(f"Error saving player location: {e}")
            time.sleep(2)
        print("last player location saved.")
        break
    elif key in "1234567890":
        inventory_slot = int(key) if key != "0" else 10
    elif key == "i":
        block_place = "up"
    elif key == "k":
        block_place = "down"
    elif key == "j":
        block_place = "left"
    elif key == "l":
        block_place = "right"
    elif key == " ":
        break_selected_block = True

    if player_x >= WINDOW_WIDTH - 3:
        player_x = WINDOW_WIDTH - 4
    # game speed
    time.sleep(0.1)
