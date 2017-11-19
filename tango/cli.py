#!/usr/bin/env python3

import click

from .commands.add import tui as tui_add
from .commands.study import tui as tui_study
from .commands.migrate import migrate as db_migrate

@click.group()
def main():
    pass

@main.command()
@click.argument('language')
@click.argument('headword')
def add(language, headword):
    tui_add(language, headword)

@main.command()
@click.argument('language', default='all')
def study(language):
    tui_study(language)

@main.command()
def migrate():
    db_migrate()

if __name__ == "__main__":
    main()
