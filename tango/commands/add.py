import sys
import sqlite3
import webbrowser

from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget

from utils import debug_print, get_url_as_base64text, get_image_search_url, get_wiktionary_url

class TangoModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE contacts(
                id INTEGER PRIMARY KEY,
                created TEXT,
                headword TEXT,
                morphology TEXT,
                definition TEXT,
                example TEXT,
                image_url TEXT,
                image TEXT,
                notes TEXT)
        ''')
        self._db.commit()

        # Current contact when editing.
        self.current_id = None

    def add(self, tango):
        tango['created'] = 'asdf'
        tango['image_url'] = tango['image_url'].strip()
        if tango['image_url']:
            try:
                tango['image'] = get_url_as_base64text(tango['image_url'])
            except Exception as e:
                debug_print("Error: Could not download image: " + str(e))
        self._db.cursor().execute('''
            INSERT INTO contacts(created, headword, morphology, definition, example, image_url, image, notes)
            VALUES(:created, :headword, :morphology, :definition, :example, :image_url, :image, :notes)''',
                                  tango)
        self._db.commit()
        debug_print(tango)

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT headword, id from contacts").fetchall()

    def get_contact(self, contact_id):
        return self._db.cursor().execute(
            "SELECT * from contacts WHERE id=:id", {"id": contact_id}).fetchone()

    def get_current_contact(self):
        if self.current_id is None:
            return {"headword": "", "morphology": "", "definition": "", "example": "", "notes": "", "image_url": "", "image": ""}
        else:
            return self.get_contact(self.current_id)

    def update_current_contact(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            self._db.cursor().execute('''
                UPDATE contacts SET headword=:headword, morphology=:morphology, definition=:definition, example=:example, image_url=:image_url, notes=:notes
                WHERE id=:id''',
                                      details)
            self._db.commit()

    def delete_contact(self, contact_id):
        self._db.cursor().execute('''
            DELETE FROM contacts WHERE id=:id''', {"id": contact_id})
        self._db.commit()


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       title="Tango")
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            model.get_summary(),
            name="tango",
            on_change=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None

    def _reload_list(self, new_value=None):
        self._list_view.options = self._model.get_summary()
        self._list_view.value = new_value

    def _add(self):
        self._model.current_id = None
        raise NextScene("Edit Tango")

    def _edit(self):
        self.save()
        self._model.current_id = self.data["contacts"]
        raise NextScene("Edit Tango")

    def _delete(self):
        self.save()
        self._model.delete_contact(self.data["tango"])
        self._reload_list()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


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
                self._model.current_focus = name
            return on_focus

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)

        headword_widget = Text("Headword", "headword")
        headword_widget._on_focus=note_focus("headword")
        layout.add_widget(headword_widget)
        debug_print("hello?")
        for keyword in ['morphology', 'definition', 'example', 'image_url', 'notes']:
            widget = TextBox(3, keyword.title(), keyword, as_string=True)
            widget._on_focus=note_focus(keyword)
            layout.add_widget(widget)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(TangoView, self).reset()
        self.data = self._model.get_current_contact()

    def _ok(self):
        self.save()
        self._model.update_current_contact(self.data)
        raise NextScene("Main")

    @staticmethod
    def _cancel():
        raise NextScene("Main")

    @staticmethod
    def _back():
        # TODO
        pass

    @staticmethod
    def _next():
        # TODO
        pass

    @staticmethod
    def _exit():
        raise StopApplication("User terminated app")

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            # ctr-b for back
            if c == 2:
                self._back()
            # ctrl-n for next
            if c == 14:
                self._next()
            # Stop on ctrl+q, ctrl-x: TODO: something else is stealing the ctrl-q event
            elif c in (17, 24):
                self._exit()
            # ctrl-f opens a browser in some kind of search
            elif c == 6 and self.data['headword'].strip():
                debug_print(self._model.current_focus)
                if self._model.current_focus == 'example':
                    webbrowser.open(get_wiktionary_url(self._model.language, self.data["headword"]), new=2)
                elif self._model.current_focus == 'image_url':
                    webbrowser.open(get_image_search_url(self._model.language, self.data["headword"]), new=2)
            else:
                debug_print(c)
                debug_print(self._model.current_focus)
                debug_print("data:" + str(self.data))


        # Now pass on to lower levels for normal handling of the event.
        return super(TangoView, self).process_event(event)


def demo(screen, scene, contacts):
    scenes = [
        Scene([ListView(screen, contacts)], -1, name="Main"),
        Scene([TangoView(screen, contacts)], -1, name="Edit Tango")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene)

def main(language):
    contacts = TangoModel()
    contacts.language = language
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene, contacts])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene

if __name__ == '__main__':
    main('de')
