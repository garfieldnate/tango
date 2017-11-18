import click

import commands.add as tui_add

@click.group()
def tango():
    pass

@tango.command()
@click.argument('language')
@click.argument('headword')
def add(language, headword):
    tui_add.tui(language, headword)

if __name__ == "__main__":
    tango()
