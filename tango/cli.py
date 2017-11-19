#!/usr/bin/env python3

import click

from .commands.add import tui as tui_add
from .commands.study import tui as tui_study

@click.group()
def main():
    pass

@main.command()
@click.argument('language')
@click.argument('headword', default=None)
def add(language, headword):
    tui_add(language, headword)

@main.command()
@click.argument('language', default='all')
def study(language):
    tui_study(language)

if __name__ == "__main__":
    main()
