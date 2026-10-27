"""Цвета и размеры в духе демонстраций cmcstatphys: белый фон, чёрные линии, серые кнопки."""
BG = (255, 255, 255)
FG = (0, 0, 0)
MUTED = (115, 115, 115)
GRID = (228, 228, 228)
AXIS = (150, 150, 150)
PANEL = (248, 248, 248)
BORDER = (205, 205, 205)

BUTTON = (240, 240, 240)
BUTTON_HOVER = (226, 226, 226)
BUTTON_PRESSED = (210, 210, 210)
SELECTED = (30, 30, 30)
SELECTED_TEXT = (255, 255, 255)
DISABLED_TEXT = (170, 170, 170)

PROCESS = (20, 20, 20)
SHIFTED = (30, 95, 190)
POSITIVE = (40, 150, 85)
NEGATIVE = (205, 65, 55)
BAR = (95, 95, 95)
BAR_CURRENT = SHIFTED
THEORY = (225, 120, 0)
CURSOR = (150, 60, 200)
REGION = (232, 240, 250)
REGION_NORMAL = (246, 238, 220)
TWIN = (0, 150, 150)          # вторая, близкая траектория
TWIN_LIGHT = (150, 210, 210)


def unit(height):
    """Базовый размер шрифта/отступа, пропорциональный высоте окна."""
    return max(11, height // 52)


def num(x, digits=3):
    """Число с настоящим знаком минус."""
    s = f"{x:.{digits}f}"
    if s.startswith("-") and s.strip("-0.") != "":
        return "−" + s[1:]
    return s.lstrip("-")
