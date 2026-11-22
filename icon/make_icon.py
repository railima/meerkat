"""Gera o ícone do app em PNG, .icns (macOS) e .ico (Windows). Uso: python icon/make_icon.py"""

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
S = 4
SIZE = 1024 * S


def draw_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    margin, radius = 100 * S, 185 * S
    box = (margin, margin, SIZE - margin, SIZE - margin)

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((box[0], box[1] + 14 * S, box[2], box[3] + 14 * S), radius,
                                             fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22 * S)))

    top, bottom = (255, 150, 40), (240, 70, 110)
    gradient = Image.new("RGBA", (SIZE, SIZE))
    gd = ImageDraw.Draw(gradient)
    for y in range(box[1], box[3]):
        k = (y - box[1]) / (box[3] - box[1])
        gd.line((0, y, SIZE, y), fill=tuple(round(a + (b - a) * k) for a, b in zip(top, bottom)))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius, fill=255)
    img.paste(gradient, (0, 0), mask)

    d = ImageDraw.Draw(img)
    cx, cy = 360 * S, 512 * S
    d.ellipse((cx - 70 * S, cy - 70 * S, cx + 70 * S, cy + 70 * S), fill="white")
    for r in (190, 320):
        d.arc((cx - r * S, cy - r * S, cx + r * S, cy + r * S), start=-48, end=48, fill="white", width=58 * S)
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
