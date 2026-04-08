mode_hex = False

def int_to_hex():
    global mode_hex
    
    try:
        user_input = input("Enter an integer (c to change mode): ")
        
        if user_input == "c":
            mode_hex = not mode_hex
            print("changed mode")
            return
        
        
        hex_value = hex(int(user_input))
        print(f"Hexadecimal: {hex_value}")
    except ValueError:
        print("Please enter a valid integer.")


def hex_to_int():
    global mode_hex
    
    try:
        user_input = input("Enter an hex (c to change mode): ")
        
        if user_input == "c":
            mode_hex = not mode_hex
            print("changed mode")
            return
        
        int_value = float.fromhex(user_input)
        print(f"int: {int_value}")
    except ValueError:
        print("Please enter a valid integer.")


if __name__ == "__main__":
    while True:
        if mode_hex:
            hex_to_int()
        else:
            int_to_hex()
32