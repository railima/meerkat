"""Ícone da bandeja/barra de menu, desenhado em tempo de execução (com contador e alerta)."""

from PIL import Image, ImageDraw, ImageFont

FUR = (214, 160, 100, 255)
MUZZLE = (240, 212, 168, 255)
PATCH = (58, 40, 30, 255)
BADGE = (229, 72, 77, 255)
WARNING = (245, 180, 0, 255)


def _glyph(draw, size):
    """A carinha do suricato: orelhas e manchas escuras nos olhos (o que o reconhece mesmo pequeno)."""
    s = size / 64

    def box(cx, cy, w, h):
        return (s * (cx - w / 2), s * (cy - h / 2), s * (cx + w / 2), s * (cy + h / 2))

    for dx in (-19, 19):  # orelhas
        draw.ellipse(box(30 + dx, 14, 13, 15), fill=PATCH)
    draw.ellipse(box(30, 30, 52, 50), fill=FUR)  # cabeça
    draw.ellipse(box(30, 44, 28, 20), fill=MUZZLE)  # focinho
    for dx in (-11, 11):
        draw.ellipse(box(30 + dx, 28, 19, 17), fill=PATCH)  # mancha escura
        draw.ellipse(box(30 + dx + 1, 28, 10, 10), fill="white")  # olho
        draw.ellipse(box(30 + dx + 3, 28, 5, 5), fill=PATCH)  # pupila olhando de lado
    draw.ellipse(box(30, 39, 10, 7), fill=PATCH)  # nariz


def tray_icon(count, error, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _glyph(draw, size)
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
