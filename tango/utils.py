from pathlib import Path
f = open(Path.home() / "dic_lookups/debug.log", 'w+')

def debug_print(message):
    print(message, file=f, flush=True)
