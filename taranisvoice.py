import aifc
import atexit
import audioop
import configparser
import tkinter
import wave
from array import array
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from time import time, sleep
from tkinter import ttk, filedialog

import appdirs
import pyttsx3


class UtterAudioThread(Thread):
    def __init__(self, phrase='', voice_id=None, progress=None, buttons=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = pyttsx3.init()
        self.voice_id = voice_id
        self.engine.setProperty('voice', self.voice_id)
        self.phrase = phrase
        self.progress = progress
        self.buttons = buttons
        self.engine.connect('started-utterance', self.on_utter_start)
        self.engine.connect('started-word', self.on_utter_word)
        self.engine.connect('finished-utterance', self.on_utter_end)
        self.daemon = True
        for button in self.buttons:
            button.state(['disabled'])
        self.start()

    def on_utter_start(self, name):
        print(f'starting {name}')
        if self.progress:
            self.progress['maximum'] = 110
            self.progress['value'] = 10

    def on_utter_word(self, name, location, length):
        print(f'utter {name} {location}/{length}/{len(self.phrase)} {self.phrase[location:location+length]}')
        if self.progress:
            self.progress['value'] = 10 + 100 * (location / len(self.phrase))

    def on_utter_end(self, name, completed):
        print(f'uttered {name} {completed}')
        self.progress['value'] = 110
        self.engine.endLoop()

    def run(self):
        self.engine.say(self.phrase)
        self.engine.startLoop(False)
        # engine.iterate() must be called inside externalLoop()
        self.loop()
        if self.progress:
            sleep(0.25)
            self.progress['value'] = 0
        for button in self.buttons:
            button.state(['!disabled'])
        print('utter thread done.')

    def loop(self):
        while True:
            try:
                self.engine.iterate()
                sleep(0.01)
            except RuntimeError:
                break
            except TypeError:
                break
        print('exiting loop...')


class MacUtterSaveThread(Thread):
    def __init__(self, phrase='', voice_id=None, filename=None, samplerate=16000, progress=None, buttons=None, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = pyttsx3.init()
        self.voice_id = voice_id
        self.engine.setProperty('voice', self.voice_id)
        self.phrase = phrase
        self.voice_id = voice_id
        self.fn = str(filename)
        self.samplerate = samplerate
        self.progress = progress
        self.buttons = buttons
        self.engine.connect('started-utterance', self.on_utter_start)
        self.engine.connect('started-word', self.on_utter_word)
        self.engine.connect('finished-utterance', self.on_utter_end)
        self.daemon = True
        for button in self.buttons:
            button.state(['disabled'])
        self.start()

    def on_utter_start(self, name):
        print(f'starting {name}')
        if self.progress:
            self.progress['maximum'] = 110
            self.progress['value'] = 10

    def on_utter_word(self, name, location, length):
        print(f'utter {name} {location}/{length}/{len(self.phrase)} {self.phrase[location:location+length]}')
        if self.progress:
            self.progress['value'] = 10 + 100 * (location / len(self.phrase))

    def on_utter_end(self, name, completed):
        print(f'uttered {name} {completed}')
        self.progress['value'] = 110
        self.engine.endLoop()

    def run(self):
        with TemporaryDirectory() as td:
            tf = str(Path(td, str(time()) + ".aiff"))
            print(f'putting in {tf}...')
            self.engine = pyttsx3.init()
            self.engine.setProperty('voice', self.voice_id)
            self.engine.save_to_file(self.phrase, tf)
            self.engine.startLoop(False)
            # engine.iterate() must be called inside externalLoop()
            self.loop()
            print('uttered.')
            with aifc.open(tf, 'rb') as a:
                print('reading aiff')
                with wave.open(self.fn, 'wb') as w:
                    w.setframerate(int(self.samplerate))
                    w.setnchannels(a.getnchannels())
                    w.setsampwidth(a.getsampwidth())
                    print('reading frames...')
                    pcm = array('H', a.readframes(a.getnframes()))
                    print('swapping bytes...')
                    pcm.byteswap()
                    print('converting to frames..')
                    frames = pcm.tobytes()
                    print('converting frames...')
                    cvframes = audioop.ratecv(frames,
                                              a.getsampwidth(),
                                              a.getnchannels(),
                                              a.getframerate(),
                                              w.getframerate(),
                                              None,
                                              )[0]
                    print(f"writing wav {self.fn}...")
                    w.writeframes(cvframes)
            print('done writing wav.')
        if self.progress:
            sleep(0.25)
            self.progress['value'] = 0
        for button in self.buttons:
            button.state(['!disabled'])
        print('utter thread done.')

    def loop(self):
        while True:
            try:
                self.engine.iterate()
                sleep(0.01)
            except RuntimeError:
                break
            except TypeError:
                break
        print('exiting loop...')


class HankTalk(ttk.Frame):
    """The adders gui and functions."""

    def __init__(self, parent, config, *args, **kwargs):
        self.config = config
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        print('init speech')
        self.engine = pyttsx3.init()
        print('get voices')
        self.voices = self.engine.getProperty('voices')
        print('init gui')
        self.init_gui()
        self._target_dir = None
        self.target_dir = Path(self.config['DEFAULT']['save_dir'])
        self._filename = None
        self.filename = 'pullup.wav'

    @property
    def target_dir(self):
        return str(self._target_dir)

    @target_dir.setter
    def target_dir(self, value):
        if self.ent_dir.get() != value:
            self.ent_dir.delete(0, len(self.ent_dir.get()))
            self.ent_dir.insert(0, value)
        self.config['DEFAULT']['save_dir'] = self.ent_dir.get()
        self._target_dir = Path(value)

    @property
    def filename(self):
        if self._filename != self.ent_filename.get():
            self._filename = self.ent_filename.get()
        return self._filename

    @filename.setter
    def filename(self, value):
        if self.ent_filename.get() != value:
            self.ent_filename.delete(0, len(self.ent_filename.get()))
            self.ent_filename.insert(0, value)
        self._filename = value

    def dia_dirsel(self):
        self.target_dir = filedialog.askdirectory(
            initialdir=str(self.target_dir),
            title="Select Destination"
        )

    @property
    def voice_id(self):
        return self.tree_voice.item(self.tree_voice.focus()).get('values', ['', '', None])[3]

    @voice_id.setter
    def voice_id(self, value):
        self.config['DEFAULT']['voice'] = self.voice_id

    def utter(self):
        self.target_dir = self.ent_dir.get()
        print('getting voice')
        utter_thread = UtterAudioThread(phrase=self.ent_phrase.get(),
                                        voice_id=self.voice_id,
                                        progress=self.status_progress,
                                        buttons=(self.export_button, self.utter_button))
        print('uttered')

    def export(self):
        self.target_dir = self.ent_dir.get()
        print('saving utterance')
        utter_thread = MacUtterSaveThread(phrase=self.ent_phrase.get(),
                                          voice_id=self.voice_id,
                                          filename=Path(self.target_dir, self.filename),
                                          samplerate=config['DEFAULT']['sample_rate'],
                                          progress=self.status_progress,
                                          buttons=(self.export_button, self.utter_button))

    def on_voice_select(self, event):
        self.voice_id = event.widget.item(event.widget.focus()).get('values', ['', '', None])[3]

    def init_gui(self):
        """Builds GUI."""
        print('init gui root')
        self.root.title('Taranis Voice')
        self.root.option_add('*tearOff', 'FALSE')

        print('init gui grid')
        self.grid(column=0, row=0, sticky='nsew')

        print('init gui menu')
        self.menubar = tkinter.Menu(self.root)

        self.menu_file = tkinter.Menu(self.menubar)
        self.menu_file.add_command(label='Export', command=self.export)
        self.menu_edit = tkinter.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        self.root.config(menu=self.menubar)

        self.lbl_phrase = ttk.Label(self, text='Phrase')
        self.ent_phrase = ttk.Entry(self)
        self.lbl_voice_select = ttk.Label(self, text='Voice')
        self.tree_voice = ttk.Treeview(self,
                                       columns=('Premium', 'Gender', 'Language', 'vid'),
                                       displaycolumns=('Premium', 'Gender', 'Language'),
                                       selectmode='browse',
                                       show='tree',
                                       )
        self.tree_voice.bind('<<TreeviewSelect>>', self.on_voice_select)

        self.lbl_dir = ttk.Label(self, text='Directory')
        self.ent_dir = ttk.Entry(self)
        self.btn_dir_dialog = ttk.Button(self, text="...", command=self.dia_dirsel)

        self.lbl_filename = ttk.Label(self, text='Filename')
        self.ent_filename = ttk.Entry(self)

        self.export_button = ttk.Button(self, text='Export to WAV', command=self.export)
        self.utter_button = ttk.Button(self, text='Speak', command=self.utter)

        self.status_frame = ttk.LabelFrame(self, text='Status', height=100)
        self.status_progress = ttk.Progressbar(self.status_frame, length=200, mode='determinate')

        row = 0
        self.lbl_phrase.grid(row=row, column=0, sticky='w')
        self.ent_phrase.grid(row=row, column=1, columnspan=3, sticky='ew')
        row += 1
        self.lbl_voice_select.grid(row=row, column=0, sticky='w')
        self.tree_voice.grid(row=row, column=1, columnspan=3, sticky='ew')
        row += 1
        self.lbl_dir.grid(row=row, column=0, sticky='w')
        self.ent_dir.grid(row=row, column=1, columnspan=2, sticky='ew')
        self.btn_dir_dialog.grid(row=row, column=3, sticky='w')
        row += 1
        self.lbl_filename.grid(row=row, column=0, sticky='w')
        self.ent_filename.grid(row=row, column=1, columnspan=3, sticky='ew')
        row += 1
        self.export_button.grid(row=row, column=0, columnspan=2, sticky='ew')
        self.utter_button.grid(row=row, column=2, columnspan=2, sticky='ew')
        row += 1
        self.status_frame.grid(row=row, column=0, columnspan=4, sticky='nesw')
        row = 0
        # row += 1
        self.status_progress.grid(row=row, column=0, sticky='ew')

        print('init inputs')
        self.ent_phrase.insert(0, 'Pull up')

        print('init inputs voices')
        self.tree_voice.column('Premium', width=32)
        self.tree_voice.column('Gender', width=32)
        self.tree_voice.column('Language', width=60)
        self.tree_voice.column('vid', width=0)

        print('init inputs voices data')
        for i, v in enumerate(self.voices):
            vv = self.tree_voice.insert('', 'end', text=v.name, values=(
                '⭐' if 'premium' in v.id else '',
                'F' if 'Female' in v.gender else 'M' if 'Male' in v.gender else '',
                v.languages[0],
                v.id,
            ))
            if v.id == self.config['DEFAULT']['voice']:
                self.tree_voice.selection_set(vv)
                self.tree_voice.focus(vv)
                self.tree_voice.move(vv, '', 0)

        print('configure grid')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.status_frame.columnconfigure(0, weight=1)
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)


def config_filename():
    return Path(appdirs.user_config_dir(appname='taranisvoice'), 'main.ini')


def load_config():
    cf = config_filename()
    config = configparser.ConfigParser()
    if cf.exists():
        print('reading config..')
        config.read(cf)
    else:
        print('defaulting config..')
        config['DEFAULT'] = {
            'save_dir'   : str(Path(Path.home(), 'Desktop')),
            'voice'      : '',
            'sample_rate': 16000,
        }
        save_config(config)
    return config


def save_config(config):
    print('saving config...')
    cf = config_filename()
    if not cf.parent.exists():
        cf.parent.mkdir(parents=True)
    with open(cf, 'w') as fp:
        config.write(fp)


if __name__ == '__main__':
    def on_quit():
        save_config(config)


    config = load_config()
    root = tkinter.Tk()
    HankTalk(root, config=config)
    print('start loop...')

    atexit.register(on_quit)
    root.mainloop()
    print('quit.')
