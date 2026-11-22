"""Gera o ícone do app (um suricato de sentinela) em PNG, .icns (macOS) e .ico (Windows).

Uso: python icon/make_icon.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
S = 4  # desenha 4x maior e reduz, para bordas suaves
SIZE = 1024 * S

FUR = (196, 146, 92)
FUR_DARK = (150, 104, 60)
BELLY = (236, 206, 160)
PATCH = (58, 40, 30)
SAND = (233, 186, 112)
SAND_DARK = (214, 160, 86)


def box(cx, cy, w, h):
    """Retângulo (em coordenadas de 1024) centrado em (cx, cy), já escalado."""
    return (S * (cx - w / 2), S * (cy - h / 2), S * (cx + w / 2), S * (cy + h / 2))


def draw_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    margin, radius = 100 * S, 185 * S
    frame = (margin, margin, SIZE - margin, SIZE - margin)

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (frame[0], frame[1] + 14 * S, frame[2], frame[3] + 14 * S), radius, fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22 * S)))

    # Cena: céu em degradê, o suricato e uma duna na frente. Tudo recortado no formato do ícone.
    scene = Image.new("RGBA", (SIZE, SIZE))
    d = ImageDraw.Draw(scene)
    top, bottom = (110, 196, 240), (255, 214, 150)
    for y in range(SIZE):
        k = y / SIZE
        d.line((0, y, SIZE, y), fill=tuple(round(a + (b - a) * k) for a, b in zip(top, bottom)))

    # Corpo e barriga
    d.ellipse(box(512, 720, 330, 560), fill=FUR)
    d.ellipse(box(512, 750, 200, 440), fill=BELLY)
    # Patinhas dobradas no peito (pose de sentinela)
    for dx in (-62, 62):
        d.ellipse(box(512 + dx, 585, 92, 120), fill=FUR_DARK)
        d.ellipse(box(512 + dx, 630, 70, 54), fill=FUR)

    # Cabeça
    for dx in (-128, 128):  # orelhas
        d.ellipse(box(512 + dx, 300, 62, 74), fill=PATCH)
    d.ellipse(box(512, 350, 300, 270), fill=FUR)
    d.ellipse(box(512, 285, 120, 70), fill=FUR_DARK)  # topo da cabeça mais escuro
    d.ellipse(box(512, 425, 170, 120), fill=BELLY)  # focinho

    # Manchas escuras dos olhos e olhos grandes olhando para o lado (de olho nos PRs)
    for dx in (-72, 72):
        d.ellipse(box(512 + dx, 345, 112, 96), fill=PATCH)
        d.ellipse(box(512 + dx, 345, 66, 66), fill="white")
        d.ellipse(box(512 + dx + 14, 348, 34, 34), fill=(20, 14, 10))
        d.ellipse(box(512 + dx + 20, 340, 11, 11), fill="white")

    # Nariz e sorrisinho
    d.ellipse(box(512, 405, 52, 34), fill=PATCH)
    d.arc(box(492, 432, 40, 30), start=20, end=160, fill=PATCH, width=6 * S)
    d.arc(box(532, 432, 40, 30), start=20, end=160, fill=PATCH, width=6 * S)

    # Duna na frente, escondendo a base do corpo
    d.ellipse(box(330, 1010, 900, 300), fill=SAND_DARK)
    d.ellipse(box(700, 1000, 900, 280), fill=SAND)

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(frame, radius, fill=255)
    img.paste(scene, (0, 0), mask)
    return img.resize((1024, 1024), Image.LANCZOS)


def main():
    icon = draw_icon()
    icon.save(HERE / "icon.png")
    icon.save(HERE / "Meerkat.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    if sys.platform == "darwin":
        iconset = HERE / "Meerkat.iconset"
        iconset.mkdir(exist_ok=True)
        for size in (16, 32, 128, 256, 512):
            icon.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
            icon.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(HERE / "Meerkat.icns")], check=True)
        shutil.rmtree(iconset)


if __name__ == "__main__":
    main()
