import clipboard


class ClipBoardError(Exception):
    pass


def get_clipboard_image():
    from PIL import ImageGrab

    im = ImageGrab.grabclipboard()
    if im is not None:
        return im
    else:
        raise ClipBoardError("Буфер обмена пуст или не является изображением")


def copy_text(text: str) -> None:
    clipboard.copy(text)


def insert_text() -> str:
    return clipboard.paste()


def clipboard_is_image() -> bool:
    from PIL import ImageGrab
    im = ImageGrab.grabclipboard()
    return im is not None


def clipboard_image_error() -> None:
    if not clipboard_is_image():
        raise ClipBoardError("Буфер обмена пуст или не является изображением")


if __name__ == '__main__':
    clipboard_image_error()
