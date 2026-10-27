"""Осциллятор Неймарка: динамический хаос и корреляционная функция.

Запуск: python main.py [--lang en] [--fullscreen]
Параметры --screen/--frames/--screenshot нужны для автоматической проверки сборки.
"""
import argparse
import time

from ncorr.app import App


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=("ru", "en"), default="ru")
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--size", help="ШxВ, например 1600x900")
    ap.add_argument("--screen", choices=("menu", "motion", "demo", "theory", "authors"), default="menu")
    ap.add_argument("--mode", choices=("d", "c"))
    ap.add_argument("--preset", choices=("H", "E"))
    ap.add_argument("--build", action="store_true", help="сразу построить всю функцию")
    ap.add_argument("--steps", type=int, default=0, help="сразу выполнить столько шагов построения")
    ap.add_argument("--seconds", type=float, default=0.0, help="движение: сразу прокрутить столько секунд")
    ap.add_argument("--dev", action="store_true", help="сразу включить режим разработчика (F12)")
    ap.add_argument("--export", action="store_true",
                    help="версия разработчика: собрать обычную версию с текущим оформлением и выйти")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--screenshot")
    args = ap.parse_args()

    size = tuple(int(x) for x in args.size.lower().split("x")) if args.size else None
    app = App(size=size, fullscreen=args.fullscreen, lang=args.lang)
    if args.screen != "menu":
        app.show(args.screen)
    if args.screen == "demo":
        app.screens["demo"].test_setup(mode=args.mode, preset=args.preset, build=args.build, steps=args.steps)
    if args.screen == "motion":
        app.screens["motion"].test_setup(preset=args.preset, seconds=args.seconds)
    if args.export:
        if not app.dev:
            raise SystemExit("--export работает только в версии разработчика")
        app.dev.export()
        while app.dev.busy():
            app.dev.update()
            time.sleep(0.1)
        app.dev.update()
        print(app.dev.status)
        return
    if args.dev and app.dev:
        app.dev.toggle()
    app.run(frames=args.frames, screenshot=args.screenshot)


if __name__ == "__main__":
    main()
