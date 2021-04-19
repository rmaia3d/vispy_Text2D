# text2d_demo.py
#
# An example of usage of the Text2D class, by emulating a terminal which 
# displays scrolling text data on the screen, OpenGL accelerated via vispy
#
# Author: Rodrigo R. M. B. Maia
# http://www.github.com/rmaia3d

import numpy as np
from vispy import gloo
from vispy import app

from text2d import Text2D


class Canvas(app.Canvas):

    def __init__(self):
        app.Canvas.__init__(self, size=(500, 500), keys='interactive')

        # Create the Text2D object
        self.text_obj = Text2D()
        self.text_obj.set_font_color((0.2, 0.2, 0.2, 1.0))

        # Initialize the window and font size
        self.s_wid = 500
        self.s_hgt = 500
        self.font_size = 16

        self.text_obj.set_font_size(self.font_size)

        # Initial screen coordinates
        self.cur_x = 10
        self.cur_y = self.s_hgt - 18

        self.lines_lst = []

        gloo.set_state(clear_color=(0.85, 0.85, 0.85, 1.0), blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

        self._timer = app.Timer('auto', connect=self.on_timer, start=True)

        self.show()

    def print_line(self, line_string):
        self.lines_lst.append(line_string)

        # If total lines above limit that fits in window height, roll the list
        max_lines = self.s_hgt // self.font_size
        if len(self.lines_lst) >= max_lines:
            self.lines_lst = self.lines_lst[1:]

        # Trigger a screen redraw
        self.update()

    def _print_buffer(self):
        # The actual drawing calls, first determining the screen coordinates
        start_y = self.s_hgt - self.font_size - 2
        for i, line in enumerate(self.lines_lst):
            c_y = start_y - (i * (self.font_size + 1))      # Starts from top down
            self.text_obj.print_text(line, self.cur_x, c_y)

    def clear_text(self):
        # Simply clear the text on screen
        self.lines_lst = []
        self.update()

    def adjust_buffer_size(self):
        # Adjust the number of lines that fit on window resize
        c_len = len(self.lines_lst)
        max_len = self.s_hgt // self.font_size

        diff = max_len - c_len

        if diff < 0:
            self.lines_lst = self.lines_lst[diff:]

    def on_resize(self, event):
        width, height = event.physical_size
        self.s_wid = width
        self.s_hgt = height
        gloo.set_viewport(0, 0, width, height)
        self.text_obj.update_screen_size(width, height)
        self.adjust_buffer_size()

    def on_key_press(self, event):
        # Press P to pause the text rolling
        if event.text == 'p' or event.text == 'P':
            if self._timer.running:
                self._timer.stop()
            else:
                self._timer.start()

    def on_draw(self, event):
        gloo.clear(color=True, depth=True)
        self._print_buffer()
        self.measure_fps()

    def on_mouse_move(self, event):
        # Nothing to do here
        pass

    def on_timer(self, event):
        # Generate some random numbers and print them
        a = np.random.randn()
        b = np.random.randn() * 10
        c = np.random.randn() * 5
        d = np.random.randn() * 20

        p_str = "a: " + str(a) + " - b: " + str(b) + \
            " c: " + str(c) + " d: " + str(d)

        self.print_line(p_str)


if __name__ == '__main__':
    c = Canvas()
    app.run()
