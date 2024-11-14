terminate_flag = False

def get_terminate_flag():
    return terminate_flag

def set_terminate_flag(value: bool):
    global terminate_flag
    terminate_flag = value