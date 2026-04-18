import pygame
import sys
import json
import os
import random
import math
import time

pygame.init()

# ── Constants ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1000, 700
FPS = 60
SAVE_FILE = "mind_maze_save.json"

# Palette
C_BG        = (8,   8,  20)
C_PANEL     = (15,  15,  35)
C_ACCENT    = (80, 200, 255)
C_ACCENT2   = (255, 100, 200)
C_GREEN     = (80, 255, 160)
C_GOLD      = (255, 210,  60)
C_TEXT      = (220, 230, 255)
C_MUTED     = (100, 110, 140)
C_WHITE     = (255, 255, 255)
C_DARK      = (5,    5,  15)
C_ERROR     = (255,  80,  80)
C_WALL      = (30,  40,  80)
C_PATH      = (20,  25,  50)
C_PLAYER    = (80, 200, 255)
C_EXIT      = (80, 255, 160)
C_KEY_BG    = (25,  30,  60)

# Fonts
pygame.font.init()
def load_font(size, bold=False):
    try:
        return pygame.font.SysFont("Consolas", size, bold=bold)
    except:
        return pygame.font.Font(None, size)

F_TITLE  = load_font(72, bold=True)
F_H1     = load_font(42, bold=True)
F_H2     = load_font(28, bold=True)
F_BODY   = load_font(22)
F_SMALL  = load_font(16)
F_TINY   = load_font(14)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Mind Maze")
clock = pygame.time.Clock()

# ── Particle System ───────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color=C_ACCENT):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.5, 1.5)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 5)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        alpha = self.life / self.max_life
        r, g, b = self.color
        col = (int(r * alpha), int(g * alpha), int(b * alpha))
        size = max(1, int(self.size * alpha))
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), size)

particles: list[Particle] = []

def spawn_particles(x, y, color=C_ACCENT, n=20):
    for _ in range(n):
        particles.append(Particle(x, y, color))

# ── Floating Stars Background ─────────────────────────────────────────────────
stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
          random.uniform(0.5, 2.0)) for _ in range(120)]

def draw_stars(t):
    for sx, sy, size in stars:
        alpha = int(100 + 80 * math.sin(t * 0.5 + sx))
        col = (alpha, alpha, min(255, alpha + 40))
        pygame.draw.circle(screen, col, (int(sx), int(sy)), max(1, int(size)))

# ── Helper draws ─────────────────────────────────────────────────────────────
def draw_text(surf, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)

def draw_glow_rect(surf, rect, color, radius=12, glow=True):
    if glow:
        glow_surf = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        r, g, b = color
        for i in range(8, 0, -2):
            pygame.draw.rect(glow_surf, (r, g, b, 15 * i),
                             (10 - i, 10 - i, rect.width + 2*i, rect.height + 2*i),
                             border_radius=radius + i)
        surf.blit(glow_surf, (rect.x - 10, rect.y - 10))
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_button(surf, rect, text, font, base_col, hover=False, active=False):
    col = tuple(min(255, c + 40) for c in base_col) if hover else base_col
    if active:
        col = C_GOLD
    draw_glow_rect(surf, rect, col, radius=10, glow=hover)
    pygame.draw.rect(surf, col, rect, border_radius=10)
    pygame.draw.rect(surf, tuple(min(255, c + 80) for c in col), rect, 2, border_radius=10)
    draw_text(surf, text, font, C_WHITE if not active else C_DARK,
              rect.centerx, rect.centery, center=True)

def draw_panel(surf, rect, alpha=200):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha))
    surf.blit(s, rect.topleft)
    pygame.draw.rect(surf, C_ACCENT, rect, 1, border_radius=14)

# ── Save / Load ───────────────────────────────────────────────────────────────
def save_game(level, puzzle_state=None):
    data = {"level": level, "puzzle_state": puzzle_state}
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return None

def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

# ═══════════════════════════════════════════════════════════════════════════════
#  PUZZLE DEFINITIONS  (10 levels, increasing difficulty)
# ═══════════════════════════════════════════════════════════════════════════════

# --- SLIDING TILE PUZZLE (levels 1-3) -----------------------------------------
class SlidingPuzzle:
    """Classic N-puzzle. Level controls grid size & shuffles."""
    def __init__(self, level):
        if level <= 1:
            self.size = 3
            shuffles = 20
        elif level <= 2:
            self.size = 3
            shuffles = 40
        else:
            self.size = 4
            shuffles = 60
        n = self.size
        self.tiles = list(range(1, n * n)) + [0]   # 0 = blank
        self.goal  = list(range(1, n * n)) + [0]
        self._shuffle(shuffles)
        self.moves = 0

    def _shuffle(self, n):
        blank = self.tiles.index(0)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for _ in range(n):
            r, c = divmod(blank, self.size)
            options = [(r+dr, c+dc) for dr, dc in dirs
                       if 0 <= r+dr < self.size and 0 <= c+dc < self.size]
            nr, nc = random.choice(options)
            nb = nr * self.size + nc
            self.tiles[blank], self.tiles[nb] = self.tiles[nb], self.tiles[blank]
            blank = nb

    def click(self, idx):
        blank = self.tiles.index(0)
        br, bc = divmod(blank, self.size)
        cr, cc = divmod(idx, self.size)
        if abs(br - cr) + abs(bc - cc) == 1:
            self.tiles[blank], self.tiles[idx] = self.tiles[idx], self.tiles[blank]
            self.moves += 1

    def solved(self):
        return self.tiles == self.goal

    def draw(self, surf, ox, oy, tile_size=100):
        n = self.size
        for i, val in enumerate(self.tiles):
            r, c = divmod(i, n)
            x = ox + c * (tile_size + 4)
            y = oy + r * (tile_size + 4)
            rect = pygame.Rect(x, y, tile_size, tile_size)
            if val == 0:
                pygame.draw.rect(surf, C_DARK, rect, border_radius=8)
                pygame.draw.rect(surf, C_WALL, rect, 2, border_radius=8)
            else:
                draw_glow_rect(surf, rect, C_KEY_BG, radius=8, glow=False)
                pygame.draw.rect(surf, C_ACCENT, rect, 2, border_radius=8)
                draw_text(surf, str(val), F_H1, C_ACCENT,
                          rect.centerx, rect.centery, center=True)

# --- SEQUENCE MEMORY PUZZLE (levels 4-5) --------------------------------------
class SequencePuzzle:
    """Simon Says - watch the pattern, repeat it."""
    def __init__(self, level):
        self.length    = 3 + level       # 7 for level 4, 8 for level 5
        self.colors    = [C_ACCENT, C_ACCENT2, C_GREEN, C_GOLD]
        self.labels    = ["A", "B", "C", "D"]
        self.sequence  = [random.randint(0, 3) for _ in range(self.length)]
        self.phase     = "show"           # show | input
        self.show_idx  = 0
        self.player_in = []
        self.timer     = 0
        self.show_duration = max(0.3, 0.8 - level * 0.05)
        self.flash_idx = -1

    def update(self, dt):
        if self.phase == "show":
            self.timer += dt
            if self.timer >= self.show_duration:
                self.timer = 0
                self.flash_idx = -1
                self.show_idx += 1
                if self.show_idx >= len(self.sequence):
                    self.phase = "input"
            else:
                self.flash_idx = self.sequence[self.show_idx] if self.timer < self.show_duration * 0.7 else -1

    def press(self, idx):
        if self.phase != "input":
            return "wait"
        self.player_in.append(idx)
        pos = len(self.player_in) - 1
        if self.player_in[pos] != self.sequence[pos]:
            return "wrong"
        if len(self.player_in) == len(self.sequence):
            return "correct"
        return "ok"

    def draw(self, surf, cx, cy):
        btn_size = 120
        gap = 20
        total_w = 4 * btn_size + 3 * gap
        sx = cx - total_w // 2
        sy = cy - btn_size // 2
        btns = []
        for i in range(4):
            rect = pygame.Rect(sx + i * (btn_size + gap), sy, btn_size, btn_size)
            btns.append(rect)
            active = self.flash_idx == i
            col = self.colors[i]
            if active:
                draw_glow_rect(surf, rect, col, radius=12)
            else:
                pygame.draw.rect(surf, tuple(c // 4 for c in col), rect, border_radius=12)
                pygame.draw.rect(surf, col, rect, 2, border_radius=12)
            draw_text(surf, self.labels[i], F_H2, col if not active else C_WHITE,
                      rect.centerx, rect.centery, center=True)
        return btns

    def solved(self):
        return len(self.player_in) == len(self.sequence) and self.player_in == self.sequence[:len(self.player_in)]

# --- MAZE NAVIGATION (levels 6-7) --------------------------------------------
class MazePuzzle:
    """Generate a random maze, navigate from start to exit."""
    def __init__(self, level):
        self.cols = 11 + (level - 6) * 4
        self.rows = 11 + (level - 6) * 4
        self.grid = self._gen_maze()
        self.player = [1, 1]
        self.exit   = [self.cols - 2, self.rows - 2]
        self.moves  = 0

    def _gen_maze(self):
        c, r = self.cols, self.rows
        grid = [[1] * c for _ in range(r)]
        visited = [[False] * c for _ in range(r)]

        def carve(x, y):
            visited[y][x] = True
            grid[y][x] = 0
            dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 < nx < c-1 and 0 < ny < r-1 and not visited[ny][nx]:
                    grid[y + dy//2][x + dx//2] = 0
                    carve(nx, ny)

        carve(1, 1)
        grid[r-2][c-2] = 0
        return grid

    def move(self, dx, dy):
        nx = self.player[0] + dx
        ny = self.player[1] + dy
        if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 0:
            self.player = [nx, ny]
            self.moves += 1

    def solved(self):
        return self.player == self.exit

    def draw(self, surf, ox, oy, cell):
        for ry in range(self.rows):
            for rx in range(self.cols):
                rect = pygame.Rect(ox + rx * cell, oy + ry * cell, cell, cell)
                if self.grid[ry][rx] == 1:
                    pygame.draw.rect(surf, C_WALL, rect)
                else:
                    pygame.draw.rect(surf, C_PATH, rect)

        # exit glow
        ex, ey = self.exit
        er = pygame.Rect(ox + ex * cell, oy + ey * cell, cell, cell)
        draw_glow_rect(surf, er, C_GREEN, radius=2)

        # player
        px, py = self.player
        pr = pygame.Rect(ox + px * cell + 2, oy + py * cell + 2, cell - 4, cell - 4)
        draw_glow_rect(surf, pr, C_PLAYER, radius=4)

# --- MATH CIPHER PUZZLE (levels 8-9) -----------------------------------------
class MathPuzzle:
    """Solve a series of equations. Each wrong answer costs a life."""
    def __init__(self, level):
        count = 4 + (level - 8) * 2     # 4 or 6 questions
        self.questions = []
        for _ in range(count):
            self.questions.append(self._gen_q(level))
        self.current = 0
        self.input_str = ""
        self.feedback  = ""
        self.fb_timer  = 0
        self.lives     = 3

    def _gen_q(self, level):
        ops = ["+", "-", "*"] if level >= 9 else ["+", "-"]
        op  = random.choice(ops)
        if op == "+":
            a, b = random.randint(10, 99), random.randint(10, 99)
            ans = a + b
        elif op == "-":
            a = random.randint(30, 99)
            b = random.randint(10, a)
            ans = a - b
        else:
            a, b = random.randint(2, 15), random.randint(2, 12)
            ans = a * b
        return (f"{a} {op} {b} = ?", ans)

    def submit(self):
        if not self.input_str:
            return "empty"
        try:
            ans = int(self.input_str)
        except:
            self.feedback = "Numbers only!"
            self.fb_timer = 2.0
            self.input_str = ""
            return "invalid"
        q_text, correct = self.questions[self.current]
        self.input_str = ""
        if ans == correct:
            self.current += 1
            if self.current >= len(self.questions):
                return "correct"
            self.feedback = "✓ Correct!"
            self.fb_timer = 1.0
            return "next"
        else:
            self.lives -= 1
            self.feedback = f"✗ Wrong! Answer: {correct}"
            self.fb_timer = 1.5
            if self.lives <= 0:
                return "dead"
            return "wrong"

    def solved(self):
        return self.current >= len(self.questions)

    def draw(self, surf, cx, cy):
        if self.current >= len(self.questions):
            return
        q_text, _ = self.questions[self.current]
        prog = f"Question {self.current + 1} / {len(self.questions)}"
        draw_text(surf, prog, F_BODY, C_MUTED, cx, cy - 120, center=True)
        draw_text(surf, q_text, F_H1, C_GOLD, cx, cy - 60, center=True)

        # input box
        box = pygame.Rect(cx - 150, cy, 300, 60)
        draw_panel(surf, box)
        display = self.input_str + ("_" if (time.time() % 1) < 0.6 else "")
        draw_text(surf, display, F_H1, C_WHITE, cx, cy + 30, center=True)

        # feedback
        if self.fb_timer > 0:
            ok = "✓" in self.feedback
            col = C_GREEN if ok else C_ERROR
            draw_text(surf, self.feedback, F_H2, col, cx, cy + 90, center=True)

        # lives
        for i in range(3):
            col = C_ACCENT2 if i < self.lives else C_MUTED
            draw_text(surf, "♥", F_H2, col, cx - 40 + i * 40, cy + 140, center=True)

# --- WORD DECODE PUZZLE (level 10) -------------------------------------------
class WordPuzzle:
    """Decode a Caesar-cipher word. Harder shift, longer words."""
    WORDS = ["ALGORITHM", "RECURSION", "ITERATION", "POLYMORPHISM",
             "ABSTRACTION", "INHERITANCE", "ENCRYPTION", "FIBONACCI",
             "CONCURRENCY", "COMPILATION"]

    def __init__(self, level):
        self.word  = random.choice(self.WORDS)
        self.shift = random.randint(3, 10)
        self.cipher = self._encode(self.word, self.shift)
        self.hint_used = False
        self.input_str = ""
        self.feedback  = ""
        self.fb_timer  = 0
        self.lives     = 4
        self.attempts  = 0

    def _encode(self, word, shift):
        return "".join(chr((ord(c) - ord("A") + shift) % 26 + ord("A")) for c in word)

    def submit(self):
        ans = self.input_str.strip().upper()
        self.input_str = ""
        self.attempts += 1
        if ans == self.word:
            return "correct"
        self.lives -= 1
        if self.lives <= 0:
            return "dead"
        self.feedback = f"✗ Not quite! {self.lives} tries left."
        self.fb_timer  = 2.0
        return "wrong"

    def hint(self):
        if not self.hint_used:
            self.hint_used = True
            return f"Shift = {self.shift} (each letter moved forward by {self.shift})"
        return "Hint already used."

    def solved(self):
        return self.input_str.strip().upper() == self.word  # checked via submit

    def draw(self, surf, cx, cy):
        draw_text(surf, "DECODE THE CIPHER WORD", F_H2, C_MUTED, cx, cy - 150, center=True)
        draw_text(surf, self.cipher, F_TITLE, C_ACCENT2, cx, cy - 80, center=True)

        hint_text = "Press [H] for a hint" if not self.hint_used else f"Hint: shift = {self.shift}"
        draw_text(surf, hint_text, F_BODY, C_GOLD, cx, cy - 10, center=True)

        box = pygame.Rect(cx - 200, cy + 30, 400, 60)
        draw_panel(surf, box)
        display = self.input_str.upper() + ("_" if (time.time() % 1) < 0.6 else "")
        draw_text(surf, display, F_H1, C_WHITE, cx, cy + 60, center=True)

        if self.fb_timer > 0:
            draw_text(surf, self.feedback, F_BODY, C_ERROR, cx, cy + 120, center=True)

        for i in range(4):
            col = C_ACCENT2 if i < self.lives else C_MUTED
            draw_text(surf, "♥", F_H2, col, cx - 60 + i * 40, cy + 165, center=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
LEVEL_INFO = {
    1:  ("Sliding Tiles",   "Arrange tiles in order. Click adjacent to blank.",  "sliding"),
    2:  ("Sliding Tiles II","Harder shuffle! Click tiles to slide them.",         "sliding"),
    3:  ("Sliding Tiles III","4×4 grid — the classic challenge!",                "sliding"),
    4:  ("Memory Sequence", "Watch the pattern. Repeat it perfectly.",            "sequence"),
    5:  ("Memory Sequence+","Longer pattern. Stay focused!",                      "sequence"),
    6:  ("Maze Escape",     "Navigate the maze. Use WASD or arrow keys.",         "maze"),
    7:  ("Deep Maze",       "Bigger maze, more choices. Find the exit!",          "maze"),
    8:  ("Math Cipher",     "Solve equations. 3 lives. Type and press ENTER.",    "math"),
    9:  ("Hard Math",       "Multiplication joins the mix. 3 lives!",             "math"),
    10: ("Word Decode",     "Decode the Caesar cipher. 4 lives. Press H for hint.","word"),
}

def build_puzzle(level):
    _, _, ptype = LEVEL_INFO[level]
    if ptype == "sliding":
        return SlidingPuzzle(level)
    elif ptype == "sequence":
        return SequencePuzzle(level)
    elif ptype == "maze":
        return MazePuzzle(level)
    elif ptype == "math":
        return MathPuzzle(level)
    elif ptype == "word":
        return WordPuzzle(level)


# ═══════════════════════════════════════════════════════════════════════════════
#  SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

class Screen:
    def handle(self, events, dt): pass
    def draw(self): pass


# ── Main Menu ─────────────────────────────────────────────────────────────────
class MainMenu(Screen):
    def __init__(self, has_save):
        self.has_save = has_save
        self.t = 0
        self.hovered = None

    def _buttons(self):
        btns = []
        if self.has_save:
            btns.append(("CONTINUE",   pygame.Rect(SCREEN_W//2 - 150, 320, 300, 54), "continue"))
        btns.append(("NEW GAME",   pygame.Rect(SCREEN_W//2 - 150, 390 if self.has_save else 330, 300, 54), "new"))
        btns.append(("EXIT",       pygame.Rect(SCREEN_W//2 - 150, 460 if self.has_save else 400, 300, 54), "exit"))
        return btns

    def handle(self, events, dt):
        self.t += dt
        mx, my = pygame.mouse.get_pos()
        self.hovered = None
        for _, rect, tag in self._buttons():
            if rect.collidepoint(mx, my):
                self.hovered = tag

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                for _, rect, tag in self._buttons():
                    if rect.collidepoint(mx, my):
                        return tag
        return None

    def draw(self):
        screen.fill(C_BG)
        draw_stars(self.t)

        # Animated title glow
        gv = int(128 + 80 * math.sin(self.t * 1.5))
        title_col = (80, gv, 255)
        # Shadow
        for dx, dy in [(3,3),(-1,1)]:
            img = F_TITLE.render("MIND MAZE", True, C_DARK)
            screen.blit(img, (SCREEN_W//2 - img.get_width()//2 + dx,
                               120 + dy))
        draw_text(screen, "MIND MAZE", F_TITLE, title_col, SCREEN_W//2, 120, center=True)
        draw_text(screen, "A Puzzle Adventure", F_BODY, C_MUTED, SCREEN_W//2, 195, center=True)

        # Level badges
        for i, (name, _, _) in enumerate(LEVEL_INFO.values()):
            ox = 50 + (i % 5) * 185
            oy = 230 + (i // 5) * 38
            r = pygame.Rect(ox, oy, 170, 28)
            pygame.draw.rect(screen, C_KEY_BG, r, border_radius=6)
            pygame.draw.rect(screen, C_WALL, r, 1, border_radius=6)
            draw_text(screen, f"Lv{i+1}: {name}", F_TINY, C_MUTED, r.centerx, r.centery, center=True)

        for label, rect, tag in self._buttons():
            draw_button(screen, rect, label, F_H2,
                        C_ACCENT if tag != "exit" else (60, 30, 60),
                        hover=self.hovered == tag)

        draw_text(screen, "© Tushar's Build",
                  F_TINY, C_MUTED, SCREEN_W//2, SCREEN_H - 24, center=True)

        for p in particles:
            p.draw(screen)


# ── Level Select (shown on New Game to confirm) ───────────────────────────────
class LevelSelectScreen(Screen):
    def __init__(self):
        self.t = 0
        self.hovered = None

    def _rects(self):
        rects = []
        cols, rows = 5, 2
        tw, th = 160, 80
        gx, gy = 20, 20
        sx = (SCREEN_W - (cols * tw + (cols-1)*gx)) // 2
        sy = 200
        for i in range(10):
            r = i // cols
            c = i % cols
            x = sx + c * (tw + gx)
            y = sy + r * (th + gy)
            rects.append(pygame.Rect(x, y, tw, th))
        return rects

    def handle(self, events, dt):
        self.t += dt
        mx, my = pygame.mouse.get_pos()
        self.hovered = None
        for i, rect in enumerate(self._rects()):
            if rect.collidepoint(mx, my):
                self.hovered = i + 1

        back_rect = pygame.Rect(40, SCREEN_H - 70, 130, 44)

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mx, my):
                    return ("back", None)
                for i, rect in enumerate(self._rects()):
                    if rect.collidepoint(mx, my):
                        return ("select", i + 1)
        return None

    def draw(self):
        screen.fill(C_BG)
        draw_stars(self.t)
        draw_text(screen, "SELECT STARTING LEVEL", F_H1, C_ACCENT, SCREEN_W//2, 100, center=True)
        draw_text(screen, "Level 1 recommended for new players", F_BODY, C_MUTED, SCREEN_W//2, 150, center=True)

        for i, rect in enumerate(self._rects()):
            lv = i + 1
            name, _, _ = LEVEL_INFO[lv]
            hover = self.hovered == lv
            col   = C_ACCENT if lv <= 3 else (C_ACCENT2 if lv <= 6 else C_GOLD)
            if hover:
                draw_glow_rect(screen, rect, col, radius=10)
            else:
                pygame.draw.rect(screen, C_KEY_BG, rect, border_radius=10)
                pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            draw_text(screen, f"Level {lv}", F_H2, col, rect.centerx, rect.y + 18, center=True)
            draw_text(screen, name, F_TINY, C_MUTED, rect.centerx, rect.y + 50, center=True)

        back = pygame.Rect(40, SCREEN_H - 70, 130, 44)
        draw_button(screen, back, "← BACK", F_BODY, (40, 20, 60), hover=back.collidepoint(*pygame.mouse.get_pos()))


# ── Game Screen ───────────────────────────────────────────────────────────────
class GameScreen(Screen):
    def __init__(self, start_level=1):
        self.level   = start_level
        self.puzzle  = build_puzzle(self.level)
        self.t       = 0
        self.feedback_msg   = ""
        self.feedback_timer = 0
        self.seq_btns = []
        self.dead     = False
        self.win_anim = 0

    def _next_level(self):
        if self.level >= 10:
            return "win"
        self.level  += 1
        self.puzzle  = build_puzzle(self.level)
        self.dead    = False
        save_game(self.level)
        return None

    def handle(self, events, dt):
        self.t += dt

        if self.feedback_timer > 0:
            self.feedback_timer -= dt

        # Update sequence puzzle animations
        _, _, ptype = LEVEL_INFO[self.level]
        if ptype == "sequence":
            self.puzzle.update(dt)
            if self.puzzle.fb_timer:
                self.puzzle.fb_timer = max(0, self.puzzle.fb_timer - dt)

        if ptype == "math":
            if self.puzzle.fb_timer > 0:
                self.puzzle.fb_timer -= dt

        if ptype == "word":
            if self.puzzle.fb_timer > 0:
                self.puzzle.fb_timer -= dt

        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(20, 20, 120, 38)

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    save_game(self.level)
                    return "menu"

                # Maze controls
                if ptype == "maze":
                    moves = {pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1),
                             pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0),
                             pygame.K_w: (0,-1), pygame.K_s: (0,1),
                             pygame.K_a: (-1,0), pygame.K_d: (1,0)}
                    if e.key in moves:
                        dx, dy = moves[e.key]
                        self.puzzle.move(dx, dy)
                        if self.puzzle.solved():
                            spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GREEN, 40)
                            res = self._next_level()
                            if res == "win":
                                return "win"

                # Math / Word text input
                if ptype in ("math", "word"):
                    if e.key == pygame.K_BACKSPACE:
                        self.puzzle.input_str = self.puzzle.input_str[:-1]
                    elif e.key == pygame.K_RETURN or e.key == pygame.K_KP_ENTER:
                        result = self.puzzle.submit()
                        if result == "correct":
                            spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GOLD, 50)
                            r = self._next_level()
                            if r == "win":
                                return "win"
                        elif result == "dead":
                            self.dead = True
                    elif ptype == "word" and e.key == pygame.K_h:
                        hint = self.puzzle.hint()
                        self.feedback_msg   = hint
                        self.feedback_timer = 3.0
                    else:
                        ch = e.unicode
                        if ptype == "math" and (ch.isdigit() or ch == "-"):
                            self.puzzle.input_str += ch
                        elif ptype == "word" and ch.isalpha():
                            self.puzzle.input_str += ch.upper()

            if e.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mx, my):
                    save_game(self.level)
                    return "menu"

                # Sliding puzzle
                if ptype == "sliding":
                    ts = 90 if self.puzzle.size == 3 else 70
                    n  = self.puzzle.size
                    total = n * (ts + 4)
                    ox = SCREEN_W // 2 - total // 2
                    oy = SCREEN_H // 2 - total // 2
                    for i in range(n * n):
                        r, c = divmod(i, n)
                        x = ox + c * (ts + 4)
                        y = oy + r * (ts + 4)
                        rect = pygame.Rect(x, y, ts, ts)
                        if rect.collidepoint(mx, my):
                            self.puzzle.click(i)
                            if self.puzzle.solved():
                                spawn_particles(SCREEN_W//2, SCREEN_H//2, C_ACCENT, 40)
                                res = self._next_level()
                                if res == "win":
                                    return "win"

                # Sequence
                if ptype == "sequence" and self.seq_btns:
                    for i, rect in enumerate(self.seq_btns):
                        if rect.collidepoint(mx, my):
                            result = self.puzzle.press(i)
                            if result == "wrong":
                                spawn_particles(mx, my, C_ERROR, 20)
                                # Reset puzzle
                                self.puzzle = SequencePuzzle(self.level)
                            elif result == "correct":
                                spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GREEN, 40)
                                res = self._next_level()
                                if res == "win":
                                    return "win"

                # Dead restart
                if self.dead:
                    restart_rect = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 60, 200, 50)
                    menu_rect    = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 125, 200, 50)
                    if restart_rect.collidepoint(mx, my):
                        self.puzzle = build_puzzle(self.level)
                        self.dead   = False
                    if menu_rect.collidepoint(mx, my):
                        save_game(self.level)
                        return "menu"

        return None

    def draw(self):
        screen.fill(C_BG)
        draw_stars(self.t)

        # Update particles
        dt = clock.get_time() / 1000
        for p in particles[:]:
            if not p.update(dt):
                particles.remove(p)
        for p in particles:
            p.draw(screen)

        # Header
        name, desc, ptype = LEVEL_INFO[self.level]
        draw_text(screen, f"LEVEL {self.level} — {name}", F_H2, C_ACCENT, SCREEN_W//2, 35, center=True)
        draw_text(screen, desc, F_BODY, C_MUTED, SCREEN_W//2, 68, center=True)

        # Level progress bar
        bar_w = 400
        bar_x = SCREEN_W//2 - bar_w//2
        pygame.draw.rect(screen, C_KEY_BG, (bar_x, 90, bar_w, 8), border_radius=4)
        prog = self.level / 10
        pygame.draw.rect(screen, C_ACCENT, (bar_x, 90, int(bar_w * prog), 8), border_radius=4)

        # Back button
        back = pygame.Rect(20, 20, 120, 38)
        draw_button(screen, back, "← MENU", F_SMALL, (40, 20, 60),
                    hover=back.collidepoint(*pygame.mouse.get_pos()))

        if self.dead:
            self._draw_dead()
            return

        # Puzzle area
        if ptype == "sliding":
            ts = 90 if self.puzzle.size == 3 else 68
            n  = self.puzzle.size
            total = n * (ts + 4)
            ox = SCREEN_W // 2 - total // 2
            oy = SCREEN_H // 2 - total // 2 + 20
            self.puzzle.draw(screen, ox, oy, tile_size=ts)
            draw_text(screen, f"Moves: {self.puzzle.moves}", F_BODY, C_MUTED,
                      SCREEN_W//2, oy + total + 20, center=True)

        elif ptype == "sequence":
            phase_text = "👁  Watch the sequence..." if self.puzzle.phase == "show" else "👆 Your turn! Repeat it."
            draw_text(screen, phase_text, F_H2, C_GOLD, SCREEN_W//2, 170, center=True)
            prog_text = f"Shown: {min(self.puzzle.show_idx, len(self.puzzle.sequence))} / {len(self.puzzle.sequence)}"
            if self.puzzle.phase == "input":
                prog_text = f"Input: {len(self.puzzle.player_in)} / {len(self.puzzle.sequence)}"
            draw_text(screen, prog_text, F_BODY, C_MUTED, SCREEN_W//2, 210, center=True)
            self.seq_btns = self.puzzle.draw(screen, SCREEN_W//2, SCREEN_H//2 + 40)

        elif ptype == "maze":
            cell = 30 if self.puzzle.cols <= 15 else 22
            total_w = self.puzzle.cols * cell
            total_h = self.puzzle.rows * cell
            ox = SCREEN_W // 2 - total_w // 2
            oy = SCREEN_H // 2 - total_h // 2 + 30
            self.puzzle.draw(screen, ox, oy, cell)
            draw_text(screen, "WASD / Arrow Keys to move", F_SMALL, C_MUTED,
                      SCREEN_W//2, oy + total_h + 14, center=True)

        elif ptype == "math":
            self.puzzle.draw(screen, SCREEN_W//2, SCREEN_H//2 - 40)

        elif ptype == "word":
            self.puzzle.draw(screen, SCREEN_W//2, SCREEN_H//2 - 60)

        # Feedback overlay
        if self.feedback_timer > 0:
            draw_text(screen, self.feedback_msg, F_BODY, C_GOLD,
                      SCREEN_W//2, SCREEN_H - 60, center=True)

        # ESC hint
        draw_text(screen, "ESC → Menu  (progress saved)", F_TINY, C_MUTED,
                  SCREEN_W - 20, SCREEN_H - 18, center=False)

    def _draw_dead(self):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))
        draw_text(screen, "OUT OF LIVES", F_H1, C_ERROR, SCREEN_W//2, SCREEN_H//2 - 60, center=True)
        draw_text(screen, "The puzzle resets.", F_BODY, C_MUTED, SCREEN_W//2, SCREEN_H//2 - 20, center=True)
        restart = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 60, 200, 50)
        menu    = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 125, 200, 50)
        mx, my  = pygame.mouse.get_pos()
        draw_button(screen, restart, "TRY AGAIN", F_H2, C_ACCENT, hover=restart.collidepoint(mx, my))
        draw_button(screen, menu,    "MAIN MENU", F_H2, (60,20,60), hover=menu.collidepoint(mx, my))


# ── Win Screen ────────────────────────────────────────────────────────────────
class WinScreen(Screen):
    def __init__(self):
        self.t = 0
        delete_save()

    def handle(self, events, dt):
        self.t += dt
        if self.t > 1.0:
            spawn_particles(random.randint(100, SCREEN_W-100),
                            random.randint(100, SCREEN_H//2),
                            random.choice([C_GOLD, C_ACCENT, C_GREEN, C_ACCENT2]), 5)
        mx, my = pygame.mouse.get_pos()
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                btn = pygame.Rect(SCREEN_W//2 - 150, SCREEN_H//2 + 100, 300, 54)
                if btn.collidepoint(mx, my):
                    particles.clear()
                    return "menu"
        return None

    def draw(self):
        screen.fill(C_BG)
        draw_stars(self.t)
        for p in particles:
            p.draw(screen)

        gv = int(200 + 55 * math.sin(self.t * 2))
        draw_text(screen, "🏆 MIND MAZE CONQUERED!", F_H1, (255, gv, 80),
                  SCREEN_W//2, SCREEN_H//2 - 120, center=True)
        draw_text(screen, "You solved all 10 levels!", F_H2, C_GREEN,
                  SCREEN_W//2, SCREEN_H//2 - 60, center=True)
        draw_text(screen, "Your mind is truly a maze master.", F_BODY, C_MUTED,
                  SCREEN_W//2, SCREEN_H//2, center=True)
        btn = pygame.Rect(SCREEN_W//2 - 150, SCREEN_H//2 + 100, 300, 54)
        mx, my = pygame.mouse.get_pos()
        draw_button(screen, btn, "BACK TO MENU", F_H2, C_ACCENT, hover=btn.collidepoint(mx, my))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    save = load_game()
    current = MainMenu(has_save=save is not None)

    while True:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        result = current.handle(events, dt)

        # State transitions
        if result == "continue" and save:
            current = GameScreen(start_level=save["level"])
            save = None

        elif result == "new":
            current = LevelSelectScreen()

        elif isinstance(result, tuple) and result[0] == "select":
            delete_save()
            current = GameScreen(start_level=result[1])

        elif isinstance(result, tuple) and result[0] == "back":
            save = load_game()
            current = MainMenu(has_save=save is not None)

        elif result == "menu":
            save = load_game()
            current = MainMenu(has_save=save is not None)

        elif result == "win":
            current = WinScreen()

        elif result == "exit":
            pygame.quit()
            sys.exit()

        current.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
