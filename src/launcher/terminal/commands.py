"""The commands used by the Terminal."""
import os, machine

bcolors = {
    'DIM':'\033[35m',
    'MID':'\033[36m',
    'LIGHT': '\033[96m',
    'OKBLUE': '\033[94m',
    'OKGREEN': '\033[92m',
    'RED': '\033[91m',
    'BOLD': '\033[1m',
}

def ctext(text:str, color:str) -> str:
    """Apply a named color to the text."""
    return f"{bcolors[color]}{text}\033[0m"

def list_dir(*args) -> str:
    """List the given directory."""
    dirs = []
    files = []
    for name_type__ in os.ilistdir(*args):
        if name_type__[1] == 0x4000:
            dirs.append(name_type__[0])
        else:
            files.append(name_type__[0])

    # style output
    return f"{ctext('  '.join(dirs), 'OKBLUE')}\n{ctext('  '.join(files), 'OKGREEN')}"

def cat(*args) -> str:
    """Read text from one or more files."""
    txt = ""
    for arg in args:
        with open(arg) as f:
            txt += f.read()
    return txt

def touch(*args):
    """Create (or touch) the given files."""
    for arg in args:
        with open(arg, 'a') as f:
            f.write('')

def del_from_str(string:str, delstrings:str) -> str:
    """Remove multiple substrings from given string."""
    string = str(string)
    for s in delstrings:
        string = string.replace(s, '')
    return string

def _help(*args) -> str:
    """Get usage info."""
    global commands  # noqa: PLW0602
    global usr_commands  # noqa: PLW0602
    if "commands" in args:
        return (
            ctext("Commands:\n", 'DIM')
            + ctext(del_from_str(list(commands.keys()), ('[',']',"'")), 'OKBLUE')
            + (" " + ctext(del_from_str(usr_commands, ('{','}',"'")), 'OKGREEN') if usr_commands else '')
        )
    return (
        ctext("MicroHydra Terminal:\n", 'DIM')
        + ctext("Type a command, the name of a Python script, or Python code to execute.\n", 'LIGHT')
        + ctext("For a list of valid commands, type ", "DIM") + ctext("help commands", "OKBLUE")
    )

def get_commands(term) -> dict:
    """Get the terminal command functions."""
    global commands  # noqa: PLW0603
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
        "help": _help,
    }
    # add alternate aliases for commands
    commands.update({
        "chdir":commands['cd'],
        "exit":commands['reboot'],
    })
    return commands


def get_usr_commands() -> set:
    """Get a set of user-defined commands."""
    global usr_commands  # noqa: PLW0603
    usr_commands = set()
    if 'usr' in os.listdir('/'):
        for name in os.listdir('/usr'):
            if name.endswith('.py'):
                usr_commands.add(name[:-3])
    return usr_commands
