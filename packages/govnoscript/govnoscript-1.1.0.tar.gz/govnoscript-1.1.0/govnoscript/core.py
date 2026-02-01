def run(filename: str, script_vars:dict=None):
    """
    Read .govno file and run it
    :param filename: .govno-file
    :param script_vars: .govno-file variables
    :raise IOError: Got not .govno-file
    """
    if not filename.endswith(".govno"):
        raise IOError(f"File {filename} must end with .govno")

    with open(filename, "r") as file:
        lines = file.read().split("\n")

    interpret(lines, script_vars)

def interpret(lines: list, script_vars:dict=None):
    """
    Run interpretation of govno-lines
    :param lines: Lines of govno-script
    :param script_vars: .govno-file variables
    """
    import pyautogui as gui
    import keyboard as kb
    import time

    for line in lines:
        if script_vars is not None:
            for var in script_vars.keys():
                line = line.replace(f"%{var}%", script_vars[var])

        line0 = line.split()

        if line in ["", " ", "\n"]:
            continue
        if line0[0].startswith("#"):
            continue

        match line0[0].lower():
            case "moveto":
                if len(line0) != 4:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                gui.moveTo(int(line0[1]), int(line0[2]), float(line0[3].replace(",", ".")))
                gui.click()
            case "click":
                if len(line0) != 2:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                match line0[1].lower():
                    case "left":
                        gui.leftClick()
                    case "right":
                        gui.rightClick()
                    case "middle":
                        gui.middleClick()
                    case _:
                        print(f"Unknown mouse button [{line0[1]}]")
            case "wait":
                if len(line0) != 2:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                time.sleep(float(line0[1]))
            case "write":
                if len(line0) < 3:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                text = " ".join(line0[2:])
                kb.write(text, float(line0[1].replace(",", ".")))
            case "write_by_keyboard":
                if len(line0) < 3:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                text = " ".join(line0[2:]).lower()
                for char in text:
                    time.sleep(float(line0[1].replace(",", ".")))
                    kb.press(char)
                    time.sleep(0.05)
                    kb.release(char)
            case "press":
                if len(line0) != 2:
                    print(f"Syntax error in line [{lines.index(line)+1}]")
                    continue
                kb.press(line0[1])
            case "release":
                if len(line0) != 2:
                    print(f"Syntax error in line [{lines.index(line) + 1}]")
                    continue
                kb.release(line0[1])
            case _:
                print(f"Unknown command [{line}]")
