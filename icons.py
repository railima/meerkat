"""Ícone da bandeja/barra de menu, desenhado em tempo de execução (com contador e alerta)."""

from PIL import Image, ImageDraw, ImageFont

BRAND = (255, 122, 26, 255)
BADGE = (229, 72, 77, 255)
WARNING = (245, 180, 0, 255)


def _glyph(draw, size, color):
    """Um ponto com duas ondas: o sinal de alerta da sentinela."""
    s = size / 64
    draw.ellipse((10 * s, 26 * s, 24 * s, 40 * s), fill=color)
    for r in (18, 30):
        box = (17 * s - r * s, 33 * s - r * s, 17 * s + r * s, 33 * s + r * s)
        draw.arc(box, start=-50, end=50, fill=color, width=round(6 * s))


def tray_icon(count, error, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _glyph(draw, size, BRAND)
    if error:
        draw.ellipse((size * 0.55, size * 0.55, size, size), fill=WARNING)
        draw.text((size * 0.775, size * 0.76), "!", fill="black", anchor="mm",
                  font=ImageFont.load_default(size=size * 0.36))
    elif count:
        label = str(count) if count < 100 else "99+"
        draw.ellipse((size * 0.45, size * 0.45, size, size), fill=BADGE)
        draw.text((size * 0.725, size * 0.71), label, fill="white", anchor="mm",
                  font=ImageFont.load_default(size=size * (0.36 if len(label) < 3 else 0.26)))
    return img
