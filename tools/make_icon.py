"""Рисует иконку программы (столбики затухающей корреляционной функции) в build/icon.png и build/icon.ico."""
import io
import os
import struct

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def draw(size=256):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 255, 255), (8, 8, size - 16, size - 16), border_radius=44)
    pygame.draw.rect(s, (30, 30, 30), (8, 8, size - 16, size - 16), 6, border_radius=44)
    zero = size * 0.55
    pygame.draw.line(s, (150, 150, 150), (36, zero), (size - 36, zero), 4)
    values = [1.0, -0.81, 0.57, -0.38, 0.25, -0.16, 0.1]
    bw = (size - 80) / len(values)
    pts = []
    for i, v in enumerate(values):
        x = 40 + i * bw
        top = zero - v * size * 0.33
        color = (95, 95, 95) if i else (30, 95, 190)
        pygame.draw.rect(s, color, (x + bw * 0.18, min(top, zero), bw * 0.64, abs(zero - top)))
        pts.append((x + bw / 2, top))
    pygame.draw.lines(s, (225, 120, 0), False, pts, 7)
    return s


def main():
    out = os.path.join(ROOT, "build")
    os.makedirs(out, exist_ok=True)
    img = draw()
    pygame.image.save(img, os.path.join(out, "icon.png"))
    buf = io.BytesIO()
    pygame.image.save(img, buf, "png")
    png = buf.getvalue()
    # ICO с PNG внутри (поддерживается начиная с Windows Vista)
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 6 + 16)
    with open(os.path.join(out, "icon.ico"), "wb") as f:
        f.write(header + entry + png)
    print("build/icon.png, build/icon.ico")


if __name__ == "__main__":
    main()
