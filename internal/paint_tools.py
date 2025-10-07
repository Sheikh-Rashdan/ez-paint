# ui modules
import customtkinter as ctk
import hPyT
import CTkColorPicker
from CTkToolTip import CTkToolTip
from CTkSpinbox import CTkSpinbox

# other modules
import math, os
from PIL import ImageGrab

# internal modules
from internal.settings import *

class PaintCanvas(ctk.CTkCanvas):
    def __init__(self, parent, asset_handler):
        super().__init__(parent, background = CANVAS_BG, cursor = 'tcross')
        self.parent = parent
        self.asset_handler = asset_handler

        # attributes
        self.old_pos = None
        self.layers = [{}]
        self.active_layer = 0
        self.brush_size = DEFAULT_BRUSH_SIZE
        self.brush_color = DEFAULT_BRUSH_COLOR
        self.drawing = False
        self.erasing = False

        # events
        self.bind('<Motion>', self.handle_motion)
        self.bind('<Button-1>', lambda e: setattr(self, 'drawing', True))
        self.bind('<ButtonRelease-1>', lambda e: setattr(self, 'drawing', False))
        self.bind('<Button-3>', lambda e: setattr(self, 'erasing', True))
        self.bind('<ButtonRelease-3>', lambda e: setattr(self, 'erasing', False))

        # layout
        self.grid(row = 0, column = 0, sticky = 'news')

    def handle_motion(self, event):
        if self.old_pos:
            if self.drawing:
                coords = (*self.old_pos, event.x, event.y)
                self.add_to_layer(coords)
                if self.active_layer == self.get_topmost_layer_index():
                    self.create_line(*coords, width = self.brush_size, fill = self.brush_color, capstyle = 'round', tags = f'layer{self.active_layer}')
                else:
                    self.create_line(*coords, width = self.brush_size, fill = self.brush_color, capstyle = 'round', tags = f'layer{self.active_layer}')
                    self.raise_layers()
            elif self.erasing:
                overlaps = self.find_overlapping(event.x-2,event.y-2,event.x+2,event.y+2)
                for object in overlaps:
                    if f'layer{self.active_layer}' in self.gettags(object):
                        self.delete(object)
                    
        self.old_pos = event.x, event.y

    def get_topmost_layer_index(self):
        return len(self.layers)-1

    def add_to_layer(self, coords):
        if self.active_layer <= self.get_topmost_layer_index():
            if (self.brush_size,self.brush_color) not in self.layers[self.active_layer]:
                self.layers[self.active_layer][(self.brush_size,self.brush_color)] = [(coords)]
            else:
                self.layers[self.active_layer][(self.brush_size,self.brush_color)] += [(coords,)]
        else:
            self.layers.append({})
            self.add_to_layer(coords)

    def raise_layers(self):
        for layer_no in range(self.active_layer+1, self.get_topmost_layer_index()+1):
            self.tag_raise(f'layer{layer_no}')

    def clear_layer(self, layer_no = None, playsound = True):
        if layer_no is None: layer_no = self.active_layer
        self.delete(f'layer{layer_no}')
        self.layers[layer_no] = {}
        if playsound:
            self.asset_handler.sounds['clear_layer'].play()

    def clear_all_layers(self):
        for layer_no in range(0,self.get_topmost_layer_index()+1):
            self.clear_layer(layer_no, playsound = False)
        self.asset_handler.sounds['clear_layer'].play()

    def save_image(self):
        filename_dialog = ctk.CTkInputDialog(title = 'Saving File', text = 'ENTER FILENAME:')
        filename_dialog.after(200, lambda: filename_dialog.iconbitmap(os.path.join('Assets', 'Images', 'icon.ico')))
        hPyT.title_bar_color.set(filename_dialog, TITLEBAR_COLOR)
        hPyT.window_frame.center(filename_dialog)

        if (filename:=filename_dialog.get_input()):
            x1 = self.parent.winfo_rootx() + self.winfo_x()
            y1 = self.parent.winfo_rooty() + self.winfo_y()
            x2 = x1+self.winfo_width()
            y2 = y1+self.winfo_height()
            self.old_pos = None
            self.after(250, lambda: ImageGrab.grab((x1,y1,x2,y2)).save(os.path.join('Saves', f'{filename}.png')))
            self.asset_handler.sounds['save_image'].play()

    def highlight_layer(self, layer_no = None):
        if layer_no is None: layer_no = self.active_layer
        items = self.find_withtag(f'layer{layer_no}')
        for item in items:
            self.itemconfigure(item, stipple = 'gray25')
            self.after(100, lambda item=item: self.itemconfigure(item, stipple = ''))

class PaintPanel(ctk.CTkFrame):
    def __init__(self, parent, asset_handler, paint_canvas: PaintCanvas):
        super().__init__(parent, corner_radius = 1000)
        self.asset_handler = asset_handler
        self.paint_canvas = paint_canvas

        # widgets
        self.create_widgets()

        # layout
        self.grid(row = 1, column = 0, sticky = 'news', padx = 15, pady = 15)

    def create_widgets(self):
        # brush tools
        self.brush_display_canvas = BrushDisplayCanvas(self, self.paint_canvas)
        self.brush_size_slider = ctk.CTkSlider(self, height = 25, corner_radius = 30,
                                               from_ = 1, to = 50, number_of_steps = 49, command = self.change_brush_size)
        self.brush_size_slider.pack(side = 'left', padx = 10)
        self.brush_size_slider.set(DEFAULT_BRUSH_SIZE)
        self.brush_size_slider.bind('<Button-1>', lambda e: self.asset_handler.sounds['change_brush_size'].play())
        create_tooltip(self.brush_size_slider, 'Brush Size')

        # seperator
        ctk.CTkFrame(self, corner_radius = 0, width = 2, fg_color = LGRAY).pack(side = 'left', fill = 'y', padx = 2, pady = 10)

        # layer tools
        self.layer_label = ctk.CTkLabel(self, text = 'LAYER:')
        self.layer_label.pack(side = 'left', padx = 10)
        self.layer_spinbox = CTkSpinbox(self, fg_color = FRAME_BG, border_width = 0, button_color = THEME_FILL, button_hover_color = THEME_HIGHLIGHT, button_border_width = 4,
                                        button_border_color = THEME_BORDER, height = 48, width = 126, button_corner_radius = 50,
                                        start_value = 1, min_value = 1, max_value = 10, scroll_value = 1, font = (FONT, 18, 'bold'), command = self.select_layer)
        self.layer_spinbox.pack(side = 'left', padx = 10)
        self.layer_spinbox.configure(cursor = 'sb_v_double_arrow')
        create_tooltip(self.layer_spinbox.decrement, 'Previous Layer')
        create_tooltip(self.layer_spinbox.increment, 'Next Layer')

        # seperator
        ctk.CTkFrame(self, corner_radius = 0, width = 2, fg_color = LGRAY).pack(side = 'left', fill = 'y', padx = 2, pady = 10)

        self.clear_layer_button = ctk.CTkButton(self, text = '', image = self.asset_handler.images['clear_layer'], command = self.paint_canvas.clear_layer,
                                                width = 40, height = 40)
        self.clear_layer_button.pack(side = 'left', padx = 10)
        create_tooltip(self.clear_layer_button, 'Clear Current Layer')

        self.clear_all_button = ctk.CTkButton(self, text = '', image = self.asset_handler.images['clear_all'], command = self.paint_canvas.clear_all_layers,
                                              width = 40, height = 40)
        self.clear_all_button.pack(side = 'left', padx = 10)
        create_tooltip(self.clear_all_button, 'Clear All Layers')

        self.save_button = ctk.CTkButton(self, text = '', image = self.asset_handler.images['save_image'], command = self.paint_canvas.save_image,
                                         width = 40, height = 40)
        self.save_button.pack(side = 'left', padx = 10)
        create_tooltip(self.save_button, 'Save Painting')

    def change_brush_color(self):
        self.asset_handler.sounds['change_brush_color'].play()
        colorpicker = CTkColorPicker.AskColor(title = 'Color Picker', initial_color = self.paint_canvas.brush_color, text = 'SELECT')
        colorpicker.after(200, lambda: colorpicker.iconbitmap(os.path.join('Assets', 'Images', 'icon.ico')))
        hPyT.window_frame.center(colorpicker)
        hPyT.title_bar_color.set(colorpicker, TITLEBAR_COLOR)
        new_color = colorpicker.get()
        if new_color:
            self.paint_canvas.brush_color = new_color
            self.brush_display_canvas.draw_display()
            self.paint_canvas.old_pos = None

    def change_brush_size(self, value):
        self.paint_canvas.brush_size = min(max(int(value),BRUSH_SIZE_LIMITS[0]),BRUSH_SIZE_LIMITS[1])
        self.brush_size_slider.set(value)
        self.brush_display_canvas.draw_display()

    def increment_brush_size(self, event):
        dirn = 1 if event.delta>0 else -1
        self.change_brush_size(self.paint_canvas.brush_size + dirn)

    def select_layer(self, layer_no):
        self.paint_canvas.active_layer = layer_no-1
        self.asset_handler.sounds['select_layer'].play()
        self.paint_canvas.highlight_layer()

class BrushDisplayCanvas(ctk.CTkCanvas):
    def __init__(self, parent: PaintPanel, paint_canvas: PaintCanvas):
        super().__init__(parent, highlightthickness = 0, background = FRAME_BG,
                         width = BRUSH_SIZE_LIMITS[1]+10, height = BRUSH_SIZE_LIMITS[1]+10,
                         cursor = 'hand2')
        self.paint_panel = parent
        self.paint_canvas = paint_canvas

        # attributes
        self.center = ((BRUSH_SIZE_LIMITS[1]+10)//2,)*2

        # draw
        self.draw_display()

        # event bindings
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)

        # layout
        self.pack(side = 'left', padx = 10)

    def on_enter(self, _event):
        radius = math.ceil(self.paint_canvas.brush_size//2) + 4
        self.create_oval(get_circle_coords(self.center, radius), width = 2, outline = WHITE if self.paint_canvas.brush_color != WHITE else THEME_HIGHLIGHT)

    def on_leave(self, _event):
        self.draw_display()

    def on_click(self, _event):
        self.paint_panel.change_brush_color()

    def draw_display(self):
        # clear canvas
        self.delete('all')

        # draw display
        radius = math.ceil(self.paint_canvas.brush_size/2)
        self.create_oval(get_circle_coords(self.center, radius), fill = self.paint_canvas.brush_color,
                                   outline = self.paint_canvas.brush_color, width = 0)
        

def get_circle_coords(center, radius):
    x1 = center[0] - radius
    y1 = center[1] - radius
    x2 = center[0] + radius
    y2 = center[1] + radius
    return (x1,y1,x2,y2)

def create_tooltip(widget, message):
    return CTkToolTip(widget, message = message, delay = 0, font = (FONT, 16, 'bold'), border_width = 2, alpha = 0.85)
