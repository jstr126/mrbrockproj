"""Write a printable US-letter checkerboard with exactly 0.25" squares.

    python make_board.py            -> board.pdf / board.png

Print at 100% / "actual size" (NOT "fit to page"), then check with a ruler
that 4 squares = 1 inch.
"""
import numpy as np
from PIL import Image

DPI = 300
SQUARE_PX = DPI // 4                     # 0.25 inch
PAGE_W, PAGE_H = int(8.5 * DPI), 11 * DPI
COLS, ROWS = 30, 40                      # 7.5" x 10" of squares

board = ((np.add.outer(np.arange(ROWS), np.arange(COLS)) % 2) * 255).astype(np.uint8)
board = np.kron(board, np.ones((SQUARE_PX, SQUARE_PX), np.uint8))
page = np.full((PAGE_H, PAGE_W), 255, np.uint8)
y0, x0 = (PAGE_H - board.shape[0]) // 2, (PAGE_W - board.shape[1]) // 2
page[y0:y0 + board.shape[0], x0:x0 + board.shape[1]] = board

img = Image.fromarray(page)
img.save("board.pdf", resolution=DPI)
img.save("board.png", dpi=(DPI, DPI))
print("wrote board.pdf and board.png — print at 100% scale, 4 squares should measure 1 inch")
