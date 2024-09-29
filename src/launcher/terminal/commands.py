import os, machine


def list_dir(*args):
    dirs = []
    files = []
    for name_type__ in os.ilistdir(*args):
        if name_type__[1] == 0x4000:
            dirs.append(name_type__[0])
        else:
            files.append(name_type__[0])
    
    # style output
    return f"\033[94m{'  '.join(dirs)}\n\033[92m{'  '.join(files)}\033[0m"

def cat(*args):
    txt = ""
    for arg in args:
        with open(arg) as f:
            txt += f.read()
    return txt

def touch(*args):
    for arg in args:
        with open(arg, 'a') as f:
            f.write('')

def get_commands(term):
    commands = {
        "ls": list_dir,
        "cat": cat,
        "cd": lambda arg: os.chdir(arg),
        "rm": lambda  arg: os.remove(arg),
        "touch": touch,
        "mv": lambda *args: os.rename(*args),
        "cwd": os.getcwd,
        "mkdir": lambda arg: os.mkdir(arg),
        "rmdir": lambda arg: os.rmdir(arg),
        "uname": lambda: os.uname().machine,
        "clear": term.clear,
        "reboot": lambda: (term.print("Goodbye!"), machine.reset()),
    }
    # add alternate aliases for commands
    commands.update({
        "chdir":commands['cd'],
        "exit":commands['reboot'],
    })
    return commands

