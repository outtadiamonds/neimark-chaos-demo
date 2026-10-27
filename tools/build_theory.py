"""Собирает теорию из theory/*.typ: PDF для архива и PNG-страницы для экрана «Теория».

Нужен только при изменении текста: python tools/build_theory.py (требуется pip install typst).
"""
import os
import sys

import typst

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(lang):
    src = os.path.join(ROOT, "theory", f"theory_{lang}.typ")
    pdf = os.path.join(ROOT, "theory", f"theory_{lang}.pdf")
    typst.compile(src, output=pdf, root=ROOT, sys_inputs={"target": "pdf"})
    pages = typst.compile(src, format="png", ppi=200, root=ROOT, sys_inputs={"target": "png"})
    if isinstance(pages, bytes):
        pages = [pages]
    out_dir = os.path.join(ROOT, "assets", "theory", lang)
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        if name.endswith(".png"):
            os.remove(os.path.join(out_dir, name))
    for i, data in enumerate(pages, 1):
        with open(os.path.join(out_dir, f"page-{i:02d}.png"), "wb") as f:
            f.write(data)
    print(f"{lang}: {pdf}, {len(pages)} png")


if __name__ == "__main__":
    for lang in sys.argv[1:] or ("ru", "en"):
        build(lang)
