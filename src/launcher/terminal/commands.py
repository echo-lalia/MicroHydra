import os


def list_dir(args):
    dirs = []
    files = []
    for name_type__ in os.ilistdir(*args):
        if name_type__[1] == 0x4000:
            dirs.append(name_type__[0])
        else:
            files.append(name_type__[0])
    
    # style output
    return f"\033[94m{'  '.join(dirs)}\n\033[92m{'  '.join(files)}\033[0m"

def cat(args):
    with open(*args) as f:
        txt = f.read()
    return txt

def get_commands(term):
    commands = {
        "ls": lambda args: term.print(list_dir(args)),
        "cat": lambda args: term.print(cat(args)),
        "cd": lambda args: os.chdir(*args),
    }
    # add alternate aliases for commands
    commands.update({
        "chdir":commands['cd'],
    })
    return commands 
# elif args[0] == 'rm':
#     for i in args[1:]:
#         os.remove(i)
# elif args[0] == 'touch':
#     for i in args[1:]:
#         with open(i, 'w') as f:
#             f.write(i)
# elif args[0] == 'mv':
#     os.rename(args[1],args[2])
# elif args[0] == 'cwd':
#     term.print(os.getcwd())
# elif args[0] == 'mkdir':
#     for i in args[1:]:
#         os.mkdir(i)
# elif args[0] == 'rmdir':
#     for i in args[1:]:
#         os.rmdir(i)
# elif args[0] == 'uname':
#     term.print(os.uname().machine)
# elif args[0] == 'clear':
#     scr_clear()
# elif args[0] == 'reboot' or args[0] == 'exit':
#     machine.reset()

