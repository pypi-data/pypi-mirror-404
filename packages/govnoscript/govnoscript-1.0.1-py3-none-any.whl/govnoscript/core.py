def run(filename: str):
    """
    Read .govno file and run it
    :param filename: .govno-file
    :raise IOError: Got not .govno-file
    """
    if not filename.endswith(".govno"):
        raise IOError(f"File {filename} must end with .govno")

    with open(filename, "r") as file:
        lines = file.read().split("\n")

    interpret(lines)

def interpret(lines: list):
    """
    Run interpretation of govno-lines
    :param lines: Lines of govno-script
    """
    import pyautogui as gui
    import keyboard as kb
    import time

    for line in lines:
        line0 = line.split()

        if line in ["", " ", "\n"]:
            continue
        if line0[0].startswith("#"):
            continue

        if line0[0] == "MOVETO" and len(line0) == 4:
            gui.moveTo(int(line0[1]), int(line0[2]), float(line0[3]))
        elif line0[0] == "CLICK" and len(line0) == 2:
            if line0[1] == "LEFT":
                gui.click()
            elif line0[1] == "RIGHT":
                gui.rightClick()
            elif line0[1] == "MIDDLE":
                gui.middleClick()
            else:
                print(f"Unknown mouse button [{line0[1]}]")
        elif line0[0] == "WAIT" and len(line0) == 2:
            time.sleep(float(line0[1]))
        elif line0[0] == "WRITE" and len(line0) >= 3:
            text = " ".join(line0[2:])
            kb.write(text, float(line0[1]))
        elif line0[0] == "WRITE_BY_KEYBOARD" and len(line0) >= 3:
            text = " ".join(line0[2:]).lower()
            for char in text:
                time.sleep(float(line0[1]))
                kb.press(char)
                time.sleep(0.05)
                kb.release(char)
        else:
            print(f"Unknown command [{line}]")
