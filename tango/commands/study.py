#!/usr/bin/env python3

import json
from os import listdir
from os.path import isfile, join
from pathlib import Path
import sys

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label

from .. import utils
from ..utils import debug_print

class ViewState():
    def __init__(self, entries):
        self.entries = entries
        self.tango_index = 0

    def current_tango(self):
        return self.entries[self.tango_index]

    def next_tango(self):
        if len(self.entries) == self.tango_index - 1:
            raise StopApplication("Reached end of tango")
        self.tango_index += 1

    def previous_tango(self):
        if self.tango_index == 0:
            return
        self.tango_index -= 1

class FrontView(Frame):
    def __init__(self, screen, entries, view_state):
        super(FrontView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Tango",
                                          reduce_cpu=True)
        self.disabled = True
        self.entries = entries
        self.view_state = view_state
        self.data = view_state.current_tango()

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)

        # TODO: uneditable Text widget
        widget = Text("Headword", "headword")
        layout.add_widget(widget)

        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Back", self._back), 0)
        layout2.add_widget(Button("Next", self._next), 1)
        layout2.add_widget(Button("Flip", self._flip), 2)
        layout2.add_widget(Button("Exit", self._exit), 3)
        self.fix()

    @staticmethod
    def _exit():
        raise StopApplication("User terminated app")

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(FrontView, self).reset()
        self.data = self.view_state.current_tango()

    def _next(self):
        self.view_state.next_tango()
        raise NextScene("FrontView")

    def _back(self):
        self.view_state.previous_tango()
        raise NextScene("FrontView")

    def _flip(self):
        debug_print("Flipping to back")
        raise NextScene("BackView")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            # ctr-b for back
            if c == 2:
                self._back()
            # ctrl-f for flip
            elif c == 6:
                self._flip()
            # ctrl-n for next
            elif c == 14:
                self._next()
            # raise ValueError(c)
            # Stop on ctrl+q, ctrl-x: TODO: something else is stealing the ctrl-q event
            elif c in (17, 24):
                self._exit()

        # Now pass on to lower levels for normal handling of the event.
        return super(FrontView, self).process_event(event)

class BackView(Frame):
    def __init__(self, screen, entries, view_state):
        super(BackView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=True,
                                          title="Tango",
                                          reduce_cpu=True)
        self.disabled = True
        self.entries = entries
        self.view_state = view_state
        self.data = view_state.current_tango()

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        for keyword in ['headword', 'morphology', 'definition', 'example', 'notes']:
            if keyword == 'headword':
                # TODO: uneditable Text widget
                widget = Text(keyword.title(), keyword)
                layout.add_widget(widget)
            else:
                # TODO: uneditable TextBox widget
                widget = TextBox(3, keyword.title(), keyword, as_string=True)
                layout.add_widget(widget)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Back", self._back), 0)
        layout2.add_widget(Button("Next", self._next), 1)
        layout2.add_widget(Button("Flip", self._flip), 2)
        layout2.add_widget(Button("Exit", self._exit), 3)
        self.fix()

    @staticmethod
    def _exit():
        raise StopApplication("User terminated app")

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(BackView, self).reset()
        self.data = self.view_state.current_tango()

    def _next(self):
        self.view_state.next_tango()
        raise NextScene("FrontView")

    def _back(self):
        self.view_state.previous_tango()
        raise NextScene("FrontView")

    def _flip(self):
        debug_print("Flipping to back")
        raise NextScene("FrontView")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            # ctr-b for back
            if c == 2:
                self._back()
            # ctrl-f for flip
            elif c == 6:
                self._flip()
            # ctrl-n for next
            elif c == 14:
                self._next()
            # raise ValueError(c)
            # Stop on ctrl+q, ctrl-x: TODO: something else is stealing the ctrl-q event
            elif c in (17, 24):
                self._exit()

        # Now pass on to lower levels for normal handling of the event.
        return super(BackView, self).process_event(event)

def tui(lang):
    """Review the tango for the selected language. If 'all' (default), review all tango for all languages.
    Shortcuts: ctrl-f=forward, ctrl-b=backward, ctrl-x=quit."""
    if lang == 'all':
        languages = utils.get_all_languages()
    else:
        languages = [lang]

    db = utils.get_db()

    entries = []
    for language in languages:
        entries.extend(db.cursor().execute(f"SELECT * FROM {language};").fetchall())

    # index- the index of the tango currently shown
    view_state = ViewState(entries)
    def show_cards(screen, start_scene):
        scenes = [
            Scene([FrontView(screen, entries, view_state)], -1, name="FrontView"),
            Scene([BackView(screen, entries, view_state)], -1, name="BackView")
        ]
        screen.play(scenes, stop_on_resize=True, start_scene=start_scene)

    current_scene = None
    while True:
        try:
            Screen.wrapper(show_cards, catch_interrupt=True, arguments=[current_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            current_scene = e.scene
