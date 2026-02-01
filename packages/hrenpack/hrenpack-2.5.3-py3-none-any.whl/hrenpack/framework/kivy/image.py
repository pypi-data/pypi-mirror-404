from kivy.uix.image import Image as KivyImage
from kivy.graphics.svg import Svg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from hrenpack.cmd import get_path_without_extension


class Image(KivyImage):
    def path(self):
        return self.source


class SVGImage(Image):
    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        drawing = svg2rlg(path)
        png_path = get_path_without_extension(path) + '.png'
        renderPM.drawToFile(drawing, png_path, 'PNG')
        self.source = png_path

if __name__ == '__main__':
    print(SVGImage('../../../icons/update.svg').path())
