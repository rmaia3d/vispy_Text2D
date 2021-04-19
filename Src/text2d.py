# text2d.py
#
# Implements the Text2D class, a very simple implementation which maps 
# glyphs from a bitmap file to actual text rendering on the screen using vispy
#
# Author: Rodrigo R. M. B. Maia
# http://www.github.com/rmaia3d

import struct

from vispy import gloo
# from vispy import app
import numpy as np


class Text2D:
    # Class that encapsulates all related methods to printing 2D text
    # to the screen using the texture mapping scheme
    # Assumes a 16rows by 16columns bitmap file containing the character glyphs
    # starting from char code 32 (ascii table).
    # For now, only constant spacing fonts supported, assumed to use half of each
    # alloted glyph square for width (e.g., if each glyph is 32x32px in a 512x512px
    # bitmap, glyph width is assumed to be 16px)
    T2DV_SHADER = """
    #version 120
    attribute vec2 a_position;
    attribute vec2 a_texcoord;
    uniform vec2 a_screensize;
    varying vec2 v_texcoord;

    void main (void)
    {
        // Normalize the position coords (which are passed in 
        // bottom left total px values) to [-1:1]
        vec2 n_pos = (a_position - (a_screensize / 2.)) / (a_screensize / 2.);
        gl_Position = vec4(n_pos, 0.0, 1.0);
        v_texcoord = a_texcoord;
    }
    """

    T2DF_SHADER = """
    #version 120
    uniform sampler2D u_tex1;
    uniform vec4 text_color;
    varying vec2 v_texcoord;

    void main()
    {
        // Sample the alpha channel from the texture R component
        // (Since glyphs are assumed to be RGB=(FF, FF, FF), just the R component is ok)
        // This is needed to ensure the texture background color becomes transparent
        vec4 sampled = vec4(1.0, 1.0, 1.0, texture2D(u_tex1, v_texcoord).r);
        // Apply the passed text_color parameter
        gl_FragColor = text_color * sampled;
    }
    """

    def __init__(self):
        self.font_img = None
        self.font_bmp_path = "Monospace821BT.bmp"
        self.font_color = (1.0, 1.0, 1.0, 1.0)
        self.font_size_px = 12

        self.f_mrg = 0      # Lateral space between glyphs, default 0px abs
        self.scr_w = 500
        self.scr_h = 500

        self.import_font_bmp()

        self.text2d_shader = gloo.Program(self.T2DV_SHADER, self.T2DF_SHADER)
        self.text2d_shader['text_color'] = self.font_color
        self.text2d_shader['u_tex1'] = gloo.Texture2D(
            self.font_img, interpolation="linear")

        # Initialize to some dummy data
        self.text2d_shader['a_position'] = np.array(
            [[-1, -1], [+1, -1], [-1, +1], [+1, +1]]).astype(np.float32)
        self.text2d_shader['a_texcoord'] = np.array(
            [[0, 0], [1.0, 0.0], [0, 1.0], [1.0, 1.0]]).astype(np.float32)

    def set_font_bmp_path(self, new_path):
        self.font_bmp_path = new_path
        self.import_font_bmp()
        self.text2d_shader['u_tex1'] = gloo.Texture2D(
            self.font_img, interpolation="linear")

    def set_font_color(self, new_color):
        # new_color should be a normalized [0:1] (r, g, b, a) tuple
        self.font_color = new_color
        self.text2d_shader['text_color'] = self.font_color

    def set_font_size(self, new_size):
        # Font size (height) in absolute pixels
        self.font_size_px = new_size

    def update_screen_size(self, new_width, new_height):
        # Absolute pixel screen (framebuffer) size
        # Reference to generate the normalized coordinates in the vertex shader
        self.scr_w = new_width
        self.scr_h = new_height
        self.text2d_shader['a_screensize'] = (self.scr_w, self.scr_h)

    def print_text(self, string, abs_pos_x, abs_pos_y):
        # pos_x and pos_y should be absolute pixel coordinates of left
        # bottom part of text rectangle starting from bottom left of the screen
        verts, uvs = self.get_text_vertex_uv(string, abs_pos_x, abs_pos_y)

        # Bind the data to the buffers
        self.text2d_shader['a_position'] = gloo.VertexBuffer(
            np.array(verts).astype(np.float32))

        self.text2d_shader['a_texcoord'] = gloo.VertexBuffer(
            np.array(uvs).astype(np.float32))

        self.text2d_shader.draw('triangles')

    def get_text_extents(self, text_string):
        # Using the currently set font size (height), the lateral spacing
        # and assuming fonts are constant width = half height, returns
        # the total absolute pixel dimensions of the passed string if printed
        # - Note that the font height parameter realates to the maximum height
        # a font with top and lower decorations will have, so simpler (no decorations)
        # and lowercase characters can have smaller heights than specified
        hgt = self.font_size_px
        wid = len(text_string) * ((hgt / 2) + self.f_mrg)

        return wid, hgt

    def import_font_bmp(self):
        # Reads the font bmp file, getting the attributes from the header fields
        # and saves the bits themselves into a numpy array
        infile = open(self.font_bmp_path, "rb")
        contents = bytearray(infile.read())
        infile.close()

        # Get filesize - offset 2
        data = [contents[2], contents[3], contents[4], contents[5]]
        fsize = struct.unpack("I", bytearray(data))

        # Start of data - offset 10 (usually = 54)
        sdata = contents[10]

        # File width (pixels) - offset 18
        f_wid = [contents[18], contents[19], contents[20], contents[21]]
        f_wid = struct.unpack("I", bytearray(f_wid))

        # File height (pixels) - offset 22
        f_hgt = [contents[22], contents[23], contents[24], contents[25]]
        f_hgt = struct.unpack("I", bytearray(f_hgt))

        # Bits per pixel - ofsset 28
        bpp = contents[28]
        bytes_px = bpp // 8

        # Start at the offset and go to the end of the file
        pix_lst = []
        for i in range(sdata, fsize[0], 3):
            r = contents[i]
            g = contents[i + 1]
            b = contents[i + 2]
            pix_lst.append((r, g, b))

        # Convert to W x H numpy array of bytes_px item tuples (RGB)
        im = np.array(pix_lst)
        im = im.reshape((f_wid[0], f_hgt[0], bytes_px)).astype(np.float32)

        # Store the final bits array
        self.font_img = im

    def get_text_vertex_uv(self, string, pos_x, pos_y):
        # Position should be passed in absolute pixels starting from bottom left
        # Assuming fixed width font, width = height / 2
        # In 512x512 bitmap, each character square in texture is 32x32px,
        # with the font being 16px wide and 32px tall originally
        f_w = self.font_size_px / 2
        verts = []
        uvs = []
        for i, c in enumerate(string):
            # Character quad vertices
            up_left = (pos_x + (i * f_w), pos_y + self.font_size_px)
            up_right = (pos_x + (i * f_w) + f_w + self.f_mrg,
                        pos_y + self.font_size_px)
            down_right = (up_right[0], pos_y)
            down_left = (up_left[0], pos_y)

            # Character texture coordinates
            # Font bitmap has been generated starting at character 32 (ascii)
            # 16 rows x 16 columns
            ascii_code = ord(c)
            row = (ascii_code - 32) // 16  # Integer division
            col = ascii_code % 16
            uv_y = row
            uv_x = col
            # Normalize to [0:1] range, divide by 16 because 16x16 rows x columns
            uv_x /= 16.
            uv_y /= 16.

            # Build the uv vertices
            # (mapping to the the actual squares)
            # Column 0 is top and UV is bottom left
            uv_up_left = (uv_x, 0.995 - uv_y)
            uv_up_right = (uv_x + 0.5 / 16., 0.995 - uv_y)
            uv_down_right = (uv_up_right[0], 0.995 - (uv_y + 0.995 / 16.))
            uv_down_left = (uv_x, uv_down_right[1])

            # Add the quad vertices (forming 2 triangles)
            verts.append(up_left)
            verts.append(down_left)
            verts.append(up_right)

            verts.append(down_right)
            verts.append(up_right)
            verts.append(down_left)

            # Add the corresponding UV vertices (same order)
            uvs.append(uv_up_left)
            uvs.append(uv_down_left)
            uvs.append(uv_up_right)

            uvs.append(uv_down_right)
            uvs.append(uv_up_right)
            uvs.append(uv_down_left)
        return verts, uvs
