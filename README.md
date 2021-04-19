# vispy_Text2D

This is a very simple implementation of text rendering using the map from bitmap method (texture mapping) and [vispy](https://github.com/vispy/vispy) acting as the bridge to OpenGL.

I looked around for specific python examples of this and couldn't find any, so made my own and am now sharing in the hopes that it's useful to anyone who's also looking for such an example.

# Tips

- You should have vispy and numpy installed in your Python environment before trying to run these scripts
- The bitmap font file (an example one is provided in this repo) should stay in the same directory as the scripts or, if running the scripts from another directory, the .bmp should be in the "working directory". Alternatively, you can change the path definition for the font_bmp variable inside ```__init__()``` method of Text2D class.
- If you want to experiment with other fonts, you can use [Codehead’s Bitmap Font Generator](http://www.codehead.co.uk/cbfg/) to generate the bitmap for you. Assumptions about the bitmap properties are provided in the Text2D class implementation comments.
