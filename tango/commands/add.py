import sys
import webbrowser

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Layout, Text, \
    Button, TextBox

from .. import utils
from ..model import get_model
from ..utils import debug_print


class TangoModel(object):
    def __init__(self, language, headword):
        self.language = language
        self.default_headword = headword
        self._model = get_model()
        # Current tango when editing.
        self.current_id = None

    def add(self, tango):
        tango['image_url'] = tango['image_url'].strip()
        if tango['image_url']:
            try:
                tango['image_base64'] = utils.get_url_as_base64text(tango['image_url'])
            except Exception as e:
                debug_print("Error: Could not download image: " + str(e))

        self.current_id = self._model.add_tango(self.language, tango)

    def get_current_contact(self):
        if self.current_id is None:
            headword = self.default_headword if self.default_headword else ""
            return {"headword": headword, "morphology": "", "definition": "", "example": "", "notes": "",
                    "image_url": "", "image_base64": ""}
        else:
            return self._model.get_tango(self.language, self.current_id)

    def update_current_contact(self, tango):
        if self.current_id is None:
            self.add(tango)
        else:
            self._model.update_tango()


class TangoView(Frame):
    def __init__(self, screen, model):
        super(TangoView, self).__init__(screen,
                                        screen.height * 2 // 3,
                                        screen.width * 2 // 3,
                                        hover_focus=True,
                                        title="Tango",
                                        reduce_cpu=True)
        # Save off the model that accesses the contacts database.
        self._model = model
        self._model.current_focus = ''

        def note_focus(name):
            def on_focus():
                # we do this so that headword can be accessed in process_event();
                # TODO: would be better if we could just query the headword widget's current value
                self.save()
                self._model.current_focus = name

            return on_focus

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)

        headword_widget = Text("Headword", "headword")
        headword_widget._on_focus = note_focus("headword")
        self.headword_widget = headword_widget
        layout.add_widget(headword_widget)
        for keyword in ['morphology', 'definition', 'example', 'image_url', 'notes']:
            widget = TextBox(3, keyword.title(), keyword, as_string=True)
            widget._on_focus = note_focus(keyword)
            layout.add_widget(widget)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Done", self._save_and_quit), 0)
        layout2.add_widget(Button("Next", self._save_and_next), 1)
        layout2.add_widget(Button("Cancel", self._quit), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(TangoView, self).reset()
        self.data = self._model.get_current_contact()

    def _save_and_quit(self):
        self.save()
        self._model.update_current_contact(self.data)
        raise StopApplication("User exited application")

    def _save_and_next(self):
        self.save()
        self._model.update_current_contact(self.data)
        self._model.default_headword = None
        self.reset()

    @staticmethod
    def _quit():
        raise StopApplication("User exited application")

    @staticmethod
    def _back():
        # TODO
        pass

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            # ctrl-n for next
            if c == 14:
                self._save_and_next()
            # ctrl-d for done
            if c == 4:
                self._save_and_quit()
            # Stop on ctrl+q, ctrl-x: TODO: something else is stealing the ctrl-q event
            elif c in (17, 24):
                self._quit()
            # ctrl-f opens a browser in some kind of search
            elif c == 6 and self.data['headword'].strip():
                if self._model.current_focus == 'definition':
                    webbrowser.open(utils.get_dictionary_url(self._model.language, self.data['headword']))
                if self._model.current_focus == 'example':
                    webbrowser.open(utils.get_wiktionary_url(self._model.language, self.data["headword"]), new=2)
                elif self._model.current_focus == 'image_url':
                    webbrowser.open(utils.get_image_search_url(self._model.language, self.data["headword"]), new=2)
                    # TODO: pressing down arrow should go to next widget if cursor is at end of line

        # Now pass on to lower levels for normal handling of the event.
        return super(TangoView, self).process_event(event)


def tui(language, headword):
    def player(screen, scene, tango_model, initial_data):
        scenes = [
            Scene([TangoView(screen, tango_model)], -1, name="Add Tango")
        ]
        screen.play(scenes, stop_on_resize=True, start_scene=scene)

    tango_model = TangoModel(language, headword)
    if not get_model().validate_language(language):
        return
    last_scene = None
    debug_print("wassup")
    while True:
        try:
            Screen.wrapper(player, catch_interrupt=True, arguments=[last_scene, tango_model, {"headword": headword}])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
