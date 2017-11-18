#!/usr/bin/env python3

import click

from commands.add import tui as tui_add
from commands.study import tui as tui_study

@click.group()
def tango():
    pass

@tango.command()
@click.argument('language')
@click.argument('headword')
def add(language, headword):
    tui_add(language, headword)

@tango.command()
@click.argument('language', default='all')
def study(language):
    tui_study(language)

if __name__ == "__main__":
    tango()
