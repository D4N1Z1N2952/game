import time
import sys
import tty
import termios
import json
import os
from colorama import init, Fore, Back, Style

init()

# Foreground colors
# Fore.BLACK
# Fore.RED
# Fore.GREEN
# Fore.YELLOW
# Fore.BLUE
# Fore.MAGENTA
# Fore.CYAN
# Fore.WHITE
# Fore.LIGHTBLACK_EX
# Fore.LIGHTRED_EX
# Fore.LIGHTGREEN_EX
# Fore.LIGHTYELLOW_EX
# Fore.LIGHTBLUE_EX
# Fore.LIGHTMAGENTA_EX
# Fore.LIGHTCYAN_EX
# Fore.LIGHTWHITE_EX

# Background colors
# Back.BLACK
# Back.RED
# Back.GREEN
# Back.YELLOW
# Back.BLUE
# Back.MAGENTA
# Back.CYAN
# Back.WHITE
# Back.LIGHTBLACK_EX
# Back.LIGHTRED_EX
# Back.LIGHTGREEN_EX
# Back.LIGHTYELLOW_EX
# Back.LIGHTBLUE_EX
# Back.LIGHTMAGENTA_EX
# Back.LIGHTCYAN_EX
# Back.LIGHTWHITE_EX

# Styles
# Style.DIM
# Style.NORMAL
# Style.BRIGHT
# Style.RESET_ALL

# Example usage:
# print(Fore.RED + "Red text" + Style.RESET_ALL)
# print(Back.GREEN + "Green background" + Style.RESET_ALL)
# print(Style.BRIGHT + "Bright text" + Style.RESET_ALL)

#constants
WINDOW_WIDTH = 24
WINDOW_HEIGHT = 21
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERDATA_PATH = os.path.join(SCRIPT_DIR, "playerdata.json")
GAMEDATA_PATH = os.path.join(SCRIPT_DIR, "gamedata.json")

if os.path.exists(PLAYERDATA_PATH):
    with open(PLAYERDATA_PATH, 'r') as i:
        playerdata = json.load(i)
    last_x = playerdata['last_location']['x']
    last_y = playerdata['last_location']['y']
    # Build inventory list: [(id, quantity), ...]
    inventory = []
    for key in playerdata['inventory']:
        item = playerdata['inventory'][key]
        inventory.append((item['id'], item['quantity']))
else:
    print("Warning: playerdata.json not found.")
    last_x = 0
    last_y = 0

if os.path.exists(GAMEDATA_PATH):
    with open(GAMEDATA_PATH, 'r') as j:
        gamedata = json.load(j)
else:
    print("Warning: gamedata.json not found.")

player_x = last_x
player_y = last_y

######################################################################

def test_for_inventory_block(x, y, loop_turn):
    if y == loop_turn:
        block_id = inventory[x][0]
        if block_id == 'none':
            print(Fore.WHITE + "◾" + Style.RESET_ALL, end="")
        elif block_id in gamedata["blocks"]:
            # Remove double quotes from the color string if present
            color_str = gamedata["blocks"][block_id]["color"]
            color_str = color_str.replace('"', '')
            # Evaluate the color string to get the actual colorama code
            try:
                color = eval(color_str)
                print(color, end="")
            except Exception:
                print(Fore.RED + "?" + Style.RESET_ALL, end="")
        else:
            print(Fore.RED + "?" + Style.RESET_ALL, end="")  # Unknown block

def test_for_inventory_quantity(item):
    # Only print the quantity for the correct inventory slot
    if inventory[item][1] > 10:
        dez = (inventory[item][1] // 10) % 10
        print(dez, end="")
        print(inventory[item][1] - dez * 10, end="")
    else:
        print(str(inventory[item][1]) + " ", end="")

def print_landscape():
    for y in range(WINDOW_HEIGHT):
        for x in range(WINDOW_WIDTH):
            if x == 22 and y % 2 != 0:
                test_for_inventory_block(0, y, 1)
                test_for_inventory_block(1, y, 3)
                test_for_inventory_block(2, y, 5)
                test_for_inventory_block(3, y, 7)
                test_for_inventory_block(4, y, 9)
                test_for_inventory_block(5, y, 11)
                test_for_inventory_block(6, y, 13)
                test_for_inventory_block(7, y, 15)
                test_for_inventory_block(8, y, 17)
                test_for_inventory_block(9, y, 19)             
            elif x == 22 and y % 2 == 0 and y != 0:
                # Only print the quantity for the corresponding inventory slot
                if y == 2:
                    test_for_inventory_quantity(0)
                elif y == 4:
                    test_for_inventory_quantity(1)
                elif y == 6:
                    test_for_inventory_quantity(2)
                elif y == 8:
                    test_for_inventory_quantity(3)
                elif y == 10:
                    test_for_inventory_quantity(4)
                elif y == 12:
                    test_for_inventory_quantity(5)
                elif y == 14:
                    test_for_inventory_quantity(6)
                elif y == 16:
                    test_for_inventory_quantity(7)
                elif y == 18:
                    test_for_inventory_quantity(8)
                elif y == 20:
                    test_for_inventory_quantity(9)
            elif x >= 21:
                print(Fore.YELLOW + "◾" + Style.RESET_ALL, end="")
            elif x == player_x and y == player_y:
                print(Fore.BLUE + "◾" + Style.RESET_ALL, end="")
            else:
                print(Fore.GREEN + "◾" + Style.RESET_ALL, end="")
        print()
    print(inventory)

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

while True:
    # Clear the screen
    print("\033[H\033[J", end="")

    # Print the game window
    print_landscape()

    print("x: " + str(player_x) + " y: " + str(player_y) + " q: save and quit")

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

    if player_x >= 20:
        player_x = 20
    #game speed
    time.sleep(0.1)