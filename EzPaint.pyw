# ui modules
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import hPyT
from pygame import mixer

# other modules
import os, json, ctypes
from PIL import Image

# internal modules
from internal.settings import *
from internal.paint_tools import *

mixer.init()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # setup
        self.settings_handler = SettingsHandler()
        self.asset_handler = AssetHandler()

        # appearance
        self.title('EzPaint')
        self.iconbitmap(os.path.join('Assets', 'Images', 'icon.ico'))
        appid = u'Rashdan.EzPaint'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
        ctk.set_appearance_mode(self.settings_handler['theme'])
        ctk.set_default_color_theme(os.path.join('Data','ezpaint_theme.json'))

        # geometry
        self.geometry(f'{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}')
        self.resizable(False,False)

        # hPyt
        hPyT.window_frame.center(self)
        hPyT.title_bar_color.set(self, TITLEBAR_COLOR)

        # widgets
        self.create_widgets()

        # shortcuts
        self.bind('<space>', lambda e: self.paint_panel.change_brush_color())
        self.bind('<Control-MouseWheel>', self.paint_panel.increment_brush_size)
        self.bind('<Shift-MouseWheel>', self.paint_panel.layer_spinbox.scroll)

        # exit protocol
        self.protocol('WM_DELETE_WINDOW', self.exit_app)

        # run
        self.mainloop()

    def create_widgets(self):
        # layout
        self.rowconfigure(0, weight = 4, uniform = 'self')
        self.rowconfigure(1, weight = 1, uniform = 'self')
        self.columnconfigure(0, weight = 1, uniform = 'self')

        # widgets
        self.paint_canvas = PaintCanvas(self, self.asset_handler)
        self.paint_panel = PaintPanel(self, self.asset_handler, self.paint_canvas)

    def exit_app(self):
        self.settings_handler.save_settings()
        self.destroy()


class SettingsHandler:
    def __init__(self):

        # attributes
        self.defaults_path = os.path.join('Data','defaults.json')
        self.settings_path = os.path.join('Data','settings.json')

        # init
        self.load_settings()

    def get_setting(self, setting_name):
        if setting_name not in self.settings:
            raise ValueError(f'Invalid setting name: {setting_name}')
            return

        return self.settings[setting_name]

    def change_setting(self, setting_name, setting_value):
        if setting_name not in self.settings:
            raise ValueError(f'Invalid setting name: {setting_name}')
            return
        
        self.settings[setting_name] = setting_value
        self.save_settings()

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as settings_file:
                self.settings = json.load(settings_file)
        else:
            with open(self.defaults_path, 'r') as defaults_file:
                self.settings = json.load(defaults_file)

    def save_settings(self):
        with open(self.settings_path, 'w') as settings_file:
            json.dump(self.settings, settings_file, indent = 1)

    def __getitem__(self, setting_name):
        return self.get_setting(setting_name)
    
    def __setitem__(self, setting_name, setting_value):
        self.change_setting(setting_name, setting_value)


class AssetHandler:
    def __init__(self):

        # attributes
        self.images_path = os.path.join('Assets','Images')
        self.sounds_path = os.path.join('Assets','Sounds')

        # assetes
        self.images = {}
        self.sounds = {}

        # init
        self.load_images()
        self.load_sounds()

    def load_images(self):
        pairs = {}
        for path, _, file_names in os.walk(self.images_path):
            for file_name in file_names:
                if '[dark]' in file_name or '[light]' in file_name:
                    pair_name = file_name.rpartition(' ')[0]
                    if pair_name not in pairs: 
                        if '[dark]' in file_name:
                            pairs[pair_name] = [None, os.path.join(path, file_name)]
                        else:
                            pairs[pair_name] = [os.path.join(path, file_name), None]
                    else:
                        if '[dark]' in file_name:
                            pairs[pair_name][1] = os.path.join(path, file_name)
                        else:
                            pairs[pair_name][0] = os.path.join(path, file_name)
                else:
                    image_name = file_name.rpartition('.')[0]
                    image = Image.open(os.path.join(path, file_name))
                    image = ctk.CTkImage(image)
                    self.images[image_name] = image

        for image_name, image_paths in pairs.items():
            image_light = Image.open(image_paths[0])
            image_dark = Image.open(image_paths[1])
            image = ctk.CTkImage(image_light, image_dark)
            self.images[image_name] = image

    def load_sounds(self):
        for path, _, file_names in os.walk(self.sounds_path):
            for file_name in file_names:
                sound_name = file_name.rpartition('.')[0]
                sound = mixer.Sound(os.path.join(path, file_name))
                self.sounds[sound_name] = sound


if __name__ == '__main__':
    App()