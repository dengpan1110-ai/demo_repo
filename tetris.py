"""简易俄罗斯方块 — 使用 pygame"""

import random
import sys

import pygame

# ---------- 配置 ----------
CELL = 30
COLS, ROWS = 10, 20
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
SIDEBAR = 160
WIDTH, HEIGHT = BOARD_W + SIDEBAR, BOARD_H
FPS = 60

BLACK = (18, 18, 24)
GRID = (40, 40, 52)
WHITE = (230, 230, 235)
GRAY = (140, 140, 155)

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# 每种方块的旋转形态（相对坐标）
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}


class Piece:
    def __init__(self, kind=None):
        self.kind = kind or random.choice(list(SHAPES))
        self.rot = 0
        self.x = COLS // 2 - 2
        self.y = 0

    @property
    def cells(self):
        return SHAPES[self.kind][self.rot % len(SHAPES[self.kind])]

    def positions(self, dx=0, dy=0, rot=None):
        r = self.rot if rot is None else rot
        shape = SHAPES[self.kind][r % len(SHAPES[self.kind])]
        return [(self.x + cx + dx, self.y + cy + dy) for cx, cy in shape]


class Game:
    def __init__(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False
        self.piece = Piece()
        self.next_piece = Piece()
        self.fall_ms = 800
        self._timer = 0

    def valid(self, positions):
        for x, y in positions:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def lock(self):
        for x, y in self.piece.positions():
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.piece.kind
        cleared = self.clear_lines()
        if cleared:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(cleared, cleared * 200) * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.fall_ms = max(100, 800 - (self.level - 1) * 70)
        self.piece = self.next_piece
        self.next_piece = Piece()
        if not self.valid(self.piece.positions()):
            self.game_over = True

    def clear_lines(self):
        new_board = [row for row in self.board if any(c is None for c in row)]
        cleared = ROWS - len(new_board)
        while len(new_board) < ROWS:
            new_board.insert(0, [None] * COLS)
        self.board = new_board
        return cleared

    def move(self, dx, dy):
        if self.valid(self.piece.positions(dx, dy)):
            self.piece.x += dx
            self.piece.y += dy
            return True
        return False

    def rotate(self):
        nxt = self.piece.rot + 1
        # 简易墙踢：原地、左、右
        for kick in (0, -1, 1, -2, 2):
            if self.valid(self.piece.positions(kick, 0, rot=nxt)):
                self.piece.x += kick
                self.piece.rot = nxt
                return

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.lock()

    def soft_drop(self):
        if self.move(0, 1):
            self.score += 1
        else:
            self.lock()

    def update(self, dt):
        if self.game_over or self.paused:
            return
        self._timer += dt
        if self._timer >= self.fall_ms:
            self._timer = 0
            if not self.move(0, 1):
                self.lock()

    def reset(self):
        self.__init__()


def draw_cell(surf, x, y, color, ox=0, oy=0):
    rect = pygame.Rect(ox + x * CELL, oy + y * CELL, CELL, CELL)
    pygame.draw.rect(surf, color, rect.inflate(-2, -2), border_radius=3)
    highlight = tuple(min(255, c + 40) for c in color)
    pygame.draw.rect(surf, highlight, rect.inflate(-2, -2), width=1, border_radius=3)


def draw_board(surf, game, font, small):
    surf.fill(BLACK)
    # 网格
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(
                surf, GRID, (c * CELL, r * CELL, CELL, CELL), 1
            )
            kind = game.board[r][c]
            if kind:
                draw_cell(surf, c, r, COLORS[kind])

    # 当前方块
    if not game.game_over:
        for x, y in game.piece.positions():
            if y >= 0:
                draw_cell(surf, x, y, COLORS[game.piece.kind])

    # 侧栏
    sx = BOARD_W + 12
    pygame.draw.line(surf, GRID, (BOARD_W, 0), (BOARD_W, HEIGHT), 2)

    lines = [
        f"分数  {game.score}",
        f"消除  {game.lines}",
        f"等级  {game.level}",
    ]
    y = 20
    for text in lines:
        surf.blit(font.render(text, True, WHITE), (sx, y))
        y += 32

    surf.blit(small.render("下一个", True, GRAY), (sx, 130))
    for cx, cy in game.next_piece.cells:
        draw_cell(surf, cx, cy, COLORS[game.next_piece.kind], ox=sx - 10, oy=150)

    help_lines = [
        "← → 移动",
        "↑ 旋转",
        "↓ 软降",
        "空格 硬降",
        "P 暂停",
        "R 重开",
    ]
    y = HEIGHT - 160
    for text in help_lines:
        surf.blit(small.render(text, True, GRAY), (sx, y))
        y += 22

    if game.paused:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))
        t = font.render("暂停", True, WHITE)
        surf.blit(t, t.get_rect(center=(BOARD_W // 2, BOARD_H // 2)))

    if game.game_over:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        t1 = font.render("游戏结束", True, WHITE)
        t2 = small.render("按 R 重新开始", True, GRAY)
        surf.blit(t1, t1.get_rect(center=(BOARD_W // 2, BOARD_H // 2 - 12)))
        surf.blit(t2, t2.get_rect(center=(BOARD_W // 2, BOARD_H // 2 + 18)))


def main():
    pygame.init()
    pygame.display.set_caption("俄罗斯方块")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 22)
    small = pygame.font.SysFont("pingfangsc,hiraginosansgb,arial", 16)

    game = Game()
    move_delay = 0
    soft_delay = 0

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif not game.game_over and not game.paused:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                        move_delay = 160
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                        move_delay = 160
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()
                    elif event.key == pygame.K_DOWN:
                        game.soft_drop()
                        soft_delay = 80

        keys = pygame.key.get_pressed()
        if not game.game_over and not game.paused:
            move_delay -= dt
            soft_delay -= dt
            if move_delay <= 0:
                if keys[pygame.K_LEFT]:
                    game.move(-1, 0)
                    move_delay = 70
                elif keys[pygame.K_RIGHT]:
                    game.move(1, 0)
                    move_delay = 70
            if soft_delay <= 0 and keys[pygame.K_DOWN]:
                game.soft_drop()
                soft_delay = 50

        game.update(dt)
        draw_board(screen, game, font, small)
        pygame.display.flip()


if __name__ == "__main__":
    main()
