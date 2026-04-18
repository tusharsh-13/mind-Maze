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
        self.x = x; self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.5, 1.5)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 5)

    def update(self, dt):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.05; self.life -= dt
        return self.life > 0

    def draw(self, surf):
        alpha = self.life / self.max_life
        r, g, b = self.color
        col = (int(r * alpha), int(g * alpha), int(b * alpha))
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)),
                           max(1, int(self.size * alpha)))

particles: list[Particle] = []

def spawn_particles(x, y, color=C_ACCENT, n=20):
    for _ in range(n):
        particles.append(Particle(x, y, color))

# ── Stars Background ──────────────────────────────────────────────────────────
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
        gs = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        r, g, b = color
        for i in range(8, 0, -2):
            pygame.draw.rect(gs, (r, g, b, 15 * i),
                             (10-i, 10-i, rect.width+2*i, rect.height+2*i),
                             border_radius=radius + i)
        surf.blit(gs, (rect.x - 10, rect.y - 10))
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_button(surf, rect, text, font, base_col, hover=False, active=False):
    col = tuple(min(255, c + 40) for c in base_col) if hover else base_col
    if active: col = C_GOLD
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
def save_game(level):
    with open(SAVE_FILE, "w") as f:
        json.dump({"level": level}, f)

def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return None

def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


# =============================================================================
#  PUZZLE CLASSES
# =============================================================================

# ── Sliding Tile (levels 1-3) ─────────────────────────────────────────────────
class SlidingPuzzle:
    def __init__(self, level):
        if level <= 1:   self.size, shuffles = 3, 20
        elif level <= 2: self.size, shuffles = 3, 40
        else:            self.size, shuffles = 4, 60
        n = self.size
        self.tiles = list(range(1, n * n)) + [0]
        self.goal  = list(range(1, n * n)) + [0]
        self._shuffle(shuffles)
        self.moves = 0

    def _shuffle(self, n):
        blank = self.tiles.index(0)
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        for _ in range(n):
            r, c = divmod(blank, self.size)
            opts = [(r+dr, c+dc) for dr,dc in dirs
                    if 0 <= r+dr < self.size and 0 <= c+dc < self.size]
            nr, nc = random.choice(opts)
            nb = nr * self.size + nc
            self.tiles[blank], self.tiles[nb] = self.tiles[nb], self.tiles[blank]
            blank = nb

    def click(self, idx):
        blank = self.tiles.index(0)
        br, bc = divmod(blank, self.size)
        cr, cc = divmod(idx, self.size)
        if abs(br-cr) + abs(bc-cc) == 1:
            self.tiles[blank], self.tiles[idx] = self.tiles[idx], self.tiles[blank]
            self.moves += 1

    def solved(self): return self.tiles == self.goal

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


# ── Math Puzzle (levels 4-5) — level 5 has hard multi-step word problems ──────
class MathPuzzle:
    def __init__(self, level):
        self.level = level
        count = 4 if level == 4 else 5
        self.questions = [self._gen_q(level) for _ in range(count)]
        self.current   = 0
        self.input_str = ""
        self.feedback  = ""
        self.fb_timer  = 0
        self.lives     = 3

    def _gen_q(self, level):
        if level == 4:
            ops = ["+", "-", "*"]
            op  = random.choice(ops)
            if op == "+":
                a, b = random.randint(10, 99), random.randint(10, 99)
                return (f"{a} + {b} = ?", a + b)
            elif op == "-":
                a = random.randint(30, 99); b = random.randint(10, a)
                return (f"{a} - {b} = ?", a - b)
            else:
                a, b = random.randint(2, 15), random.randint(2, 12)
                return (f"{a} x {b} = ?", a * b)
        else:
            # Hard multi-step word problems
            t = random.randint(1, 8)
            if t == 1:
                s1 = random.choice([60,70,80,90])
                s2 = random.choice([50,55,65,75])
                h  = random.choice([2,3,4])
                ans = (s1+s2)*h
                q = (f"Two trains depart simultaneously in opposite directions.\n"
                     f"Train A: {s1} km/h  |  Train B: {s2} km/h\n"
                     f"Distance between them after {h} hours? (km)")
            elif t == 2:
                p = random.choice([1000,2000,5000])
                r = random.choice([5,10,20])
                y = random.choice([2,3])
                ans = p + p*r*y//100
                q = (f"Principal: Rs.{p}  Rate: {r}% per year (simple interest)\n"
                     f"What is the total amount after {y} years?")
            elif t == 3:
                age_a = random.randint(10,30)
                diff  = random.randint(3,15)
                yrs   = random.randint(3,10)
                ans   = (age_a + yrs) + (age_a + diff + yrs)
                q = (f"A is {age_a} yrs old. B is {diff} years older than A.\n"
                     f"What is the SUM of their ages after {yrs} years?")
            elif t == 4:
                w  = random.choice([4,5,6,8])
                d  = random.choice([10,12,15,20])
                nw = random.choice([2,3,4])
                ans = (w*d) // (w+nw)
                q = (f"{w} workers finish a project in {d} days.\n"
                     f"{nw} additional workers join from day 1.\n"
                     f"In how many days is the project finished now?")
            elif t == 5:
                l1 = random.choice([10,15,20])
                p1 = random.choice([20,25,30])
                l2 = random.choice([10,15,20])
                p2 = random.choice([40,50,60])
                ans = l1*p1//100 + l2*p2//100
                q = (f"Mixture A: {l1}L  ({p1}% milk)\n"
                     f"Mixture B: {l2}L  ({p2}% milk)\n"
                     f"Total milk in litres when combined?")
            elif t == 6:
                cp   = random.choice([200,300,400,500])
                perc = random.choice([10,15,20,25])
                ans  = cp + cp*perc//100
                q = (f"Cost Price: Rs.{cp}\n"
                     f"Shopkeeper sells at {perc}% profit.\n"
                     f"What is the Selling Price? (Rs.)")
            elif t == 7:
                first = random.choice([1,2,3,4,5])
                diff  = random.choice([2,3,4,5])
                n     = random.choice([5,6,7,8])
                last  = first + (n-1)*diff
                ans   = n*(first+last)//2
                q = (f"Arithmetic series: first term={first}, common difference={diff}\n"
                     f"What is the sum of the first {n} terms?")
            else:
                dist  = random.choice([120,180,240,300])
                speed = random.choice([40,60,80])
                ans   = dist // speed
                q = (f"Distance: {dist} km  |  Speed: {speed} km/h\n"
                     f"How many hours does the journey take?")
            return (q, ans)

    def submit(self):
        if not self.input_str: return "empty"
        try:    ans = int(self.input_str)
        except:
            self.feedback = "Integers only!"; self.fb_timer = 2.0
            self.input_str = ""; return "invalid"
        q_text, correct = self.questions[self.current]
        self.input_str = ""
        if ans == correct:
            self.current += 1
            if self.current >= len(self.questions): return "correct"
            self.feedback = "Correct!"; self.fb_timer = 1.0
            return "next"
        else:
            self.lives -= 1
            self.feedback = f"Wrong! Answer: {correct}"
            self.fb_timer = 1.5
            if self.lives <= 0: return "dead"
            return "wrong"

    def solved(self): return self.current >= len(self.questions)

    def draw(self, surf, cx, cy):
        if self.current >= len(self.questions): return
        q_text, _ = self.questions[self.current]
        draw_text(surf, f"Question {self.current+1} / {len(self.questions)}",
                  F_BODY, C_MUTED, cx, cy - 210, center=True)
        lines = q_text.split("\n")
        for li, line in enumerate(lines):
            font = F_H2 if self.level == 5 else F_H1
            draw_text(surf, line, font, C_GOLD, cx, cy - 155 + li * 42, center=True)
        box = pygame.Rect(cx - 150, cy + 30, 300, 60)
        draw_panel(surf, box)
        display = self.input_str + ("_" if (time.time() % 1) < 0.6 else "")
        draw_text(surf, display, F_H1, C_WHITE, cx, cy + 60, center=True)
        if self.fb_timer > 0:
            ok  = "Correct" in self.feedback
            col = C_GREEN if ok else C_ERROR
            draw_text(surf, self.feedback, F_H2, col, cx, cy + 110, center=True)
        for i in range(3):
            col = C_ACCENT2 if i < self.lives else C_MUTED
            draw_text(surf, "♥", F_H2, col, cx - 40 + i * 40, cy + 160, center=True)


# ── Maze (levels 6-7) ─────────────────────────────────────────────────────────
class MazePuzzle:
    def __init__(self, level):
        self.cols = 11 + (level - 6) * 4
        self.rows = 11 + (level - 6) * 4
        self.grid = self._gen_maze()
        self.player = [1, 1]
        self.exit   = [self.cols - 2, self.rows - 2]
        self.moves  = 0

    def _gen_maze(self):
        c, r = self.cols, self.rows
        grid    = [[1]*c for _ in range(r)]
        visited = [[False]*c for _ in range(r)]
        def carve(x, y):
            visited[y][x] = True; grid[y][x] = 0
            dirs = [(0,-2),(0,2),(-2,0),(2,0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                if 0 < nx < c-1 and 0 < ny < r-1 and not visited[ny][nx]:
                    grid[y+dy//2][x+dx//2] = 0
                    carve(nx, ny)
        carve(1, 1)
        grid[r-2][c-2] = 0
        return grid

    def move(self, dx, dy):
        nx = self.player[0]+dx; ny = self.player[1]+dy
        if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 0:
            self.player = [nx, ny]; self.moves += 1

    def solved(self): return self.player == self.exit

    def draw(self, surf, ox, oy, cell):
        for ry in range(self.rows):
            for rx in range(self.cols):
                rect = pygame.Rect(ox+rx*cell, oy+ry*cell, cell, cell)
                pygame.draw.rect(surf, C_WALL if self.grid[ry][rx] else C_PATH, rect)
        ex, ey = self.exit
        draw_glow_rect(surf, pygame.Rect(ox+ex*cell, oy+ey*cell, cell, cell),
                       C_GREEN, radius=2)
        px, py = self.player
        draw_glow_rect(surf, pygame.Rect(ox+px*cell+2, oy+py*cell+2, cell-4, cell-4),
                       C_PLAYER, radius=4)


# ── Sequence Memory Puzzle (levels 8-9) ───────────────────────────────────────
#   Features: 3-sec countdown · green glow on correct · red blink on wrong ·
#             retry overlay after wrong press
class SequencePuzzle:
    def __init__(self, level):
        seq_len = 6 + (level - 8) * 3      # level 8=6, level 9=9
        self.colors  = [C_ACCENT, C_ACCENT2, C_GREEN, C_GOLD]
        self.labels  = ["A", "B", "C", "D"]
        self.sequence = [random.randint(0, 3) for _ in range(seq_len)]

        # phases: "countdown" → "show" → "input" → "wrong_flash" → "retry"
        self.phase         = "countdown"
        self.countdown     = 3.0
        self.show_idx      = 0
        self.player_in     = []
        self.timer         = 0
        self.show_duration = max(0.35, 0.9 - (level - 8) * 0.15)
        self.flash_idx     = -1

        self.feedback_idx   = -1
        self.feedback_col   = None
        self.feedback_timer = 0.0
        self.show_retry     = False

    def update(self, dt):
        if self.phase == "countdown":
            self.countdown -= dt
            if self.countdown <= 0:
                self.phase = "show"; self.countdown = 0

        elif self.phase == "show":
            self.timer += dt
            if self.timer >= self.show_duration:
                self.timer = 0; self.flash_idx = -1
                self.show_idx += 1
                if self.show_idx >= len(self.sequence):
                    self.phase = "input"
            else:
                self.flash_idx = (self.sequence[self.show_idx]
                                  if self.timer < self.show_duration * 0.7 else -1)

        elif self.phase == "wrong_flash":
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.phase = "retry"; self.show_retry = True

        if self.feedback_col == C_GREEN and self.feedback_timer > 0 and self.phase == "input":
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.feedback_idx = -1

    def press(self, idx):
        if self.phase != "input": return "wait"
        pos = len(self.player_in)
        if idx == self.sequence[pos]:
            self.player_in.append(idx)
            self.feedback_idx   = idx
            self.feedback_col   = C_GREEN
            self.feedback_timer = 0.4
            if len(self.player_in) == len(self.sequence):
                return "correct"
            return "ok"
        else:
            self.feedback_idx   = idx
            self.feedback_col   = C_ERROR
            self.feedback_timer = 0.55
            self.phase          = "wrong_flash"
            return "wrong"

    def reset_for_retry(self):
        self.phase          = "countdown"
        self.countdown      = 3.0
        self.show_idx       = 0
        self.player_in      = []
        self.timer          = 0
        self.flash_idx      = -1
        self.feedback_idx   = -1
        self.feedback_col   = None
        self.feedback_timer = 0.0
        self.show_retry     = False

    def draw(self, surf, cx, cy):
        btn_size = 120; gap = 20
        total_w  = 4 * btn_size + 3 * gap
        sx = cx - total_w // 2
        sy = cy - btn_size // 2
        btns = []

        for i in range(4):
            rect = pygame.Rect(sx + i*(btn_size+gap), sy, btn_size, btn_size)
            btns.append(rect)

            is_show_flash = (self.flash_idx == i)
            is_feedback   = (self.feedback_idx == i and self.feedback_timer > 0)
            base_col = self.colors[i]

            if is_show_flash:
                draw_glow_rect(surf, rect, base_col, radius=12)
                draw_text(surf, self.labels[i], F_H2, C_WHITE,
                          rect.centerx, rect.centery, center=True)
            elif is_feedback and self.feedback_col == C_GREEN:
                draw_glow_rect(surf, rect, C_GREEN, radius=12)
                draw_text(surf, self.labels[i], F_H2, C_WHITE,
                          rect.centerx, rect.centery, center=True)
            elif is_feedback and self.feedback_col == C_ERROR:
                blink_on = int(self.feedback_timer * 10) % 2 == 0
                col = C_ERROR if blink_on else (60, 5, 5)
                draw_glow_rect(surf, rect, col, radius=12)
                draw_text(surf, self.labels[i], F_H2, C_WHITE,
                          rect.centerx, rect.centery, center=True)
            else:
                pygame.draw.rect(surf, tuple(c//4 for c in base_col), rect, border_radius=12)
                pygame.draw.rect(surf, base_col, rect, 2, border_radius=12)
                draw_text(surf, self.labels[i], F_H2, base_col,
                          rect.centerx, rect.centery, center=True)

        return btns

    def solved(self):
        return (len(self.player_in) == len(self.sequence) and
                self.player_in == self.sequence)


# ── Word Decode (level 10) ────────────────────────────────────────────────────
class WordPuzzle:
    WORDS = ["ALGORITHM", "RECURSION", "ITERATION", "POLYMORPHISM",
             "ABSTRACTION", "INHERITANCE", "ENCRYPTION", "FIBONACCI",
             "CONCURRENCY", "COMPILATION"]

    def __init__(self, level):
        self.word       = random.choice(self.WORDS)
        self.shift      = random.randint(3, 10)
        self.cipher     = self._encode(self.word, self.shift)
        self.hint_used  = False
        self.input_str  = ""
        self.feedback   = ""
        self.fb_timer   = 0
        self.lives      = 4

    def _encode(self, word, shift):
        return "".join(chr((ord(c)-ord("A")+shift)%26+ord("A")) for c in word)

    def submit(self):
        ans = self.input_str.strip().upper(); self.input_str = ""
        if ans == self.word: return "correct"
        self.lives -= 1
        if self.lives <= 0: return "dead"
        self.feedback = f"Not quite! {self.lives} tries left."
        self.fb_timer = 2.0
        return "wrong"

    def hint(self):
        if not self.hint_used:
            self.hint_used = True
            return f"Shift = {self.shift}  (each letter moved +{self.shift})"
        return "Hint already used."

    def draw(self, surf, cx, cy):
        draw_text(surf, "DECODE THE CIPHER WORD", F_H2, C_MUTED, cx, cy-150, center=True)
        draw_text(surf, self.cipher, F_TITLE, C_ACCENT2, cx, cy-80, center=True)
        hint_text = "Press [H] for a hint" if not self.hint_used else f"Hint: shift = {self.shift}"
        draw_text(surf, hint_text, F_BODY, C_GOLD, cx, cy-10, center=True)
        box = pygame.Rect(cx-200, cy+30, 400, 60)
        draw_panel(surf, box)
        display = self.input_str.upper() + ("_" if (time.time()%1)<0.6 else "")
        draw_text(surf, display, F_H1, C_WHITE, cx, cy+60, center=True)
        if self.fb_timer > 0:
            draw_text(surf, self.feedback, F_BODY, C_ERROR, cx, cy+120, center=True)
        for i in range(4):
            col = C_ACCENT2 if i < self.lives else C_MUTED
            draw_text(surf, "♥", F_H2, col, cx-60+i*40, cy+165, center=True)


# =============================================================================
#  LEVEL MAP  — levels 4-5 = math  |  levels 8-9 = sequence  (swapped!)
# =============================================================================
LEVEL_INFO = {
    1:  ("Sliding Tiles",    "Arrange tiles in order. Click adjacent to blank.",    "sliding"),
    2:  ("Sliding Tiles II", "Harder shuffle! Click tiles to slide them.",          "sliding"),
    3:  ("Sliding Tiles III","4x4 grid — the classic challenge!",                   "sliding"),
    4:  ("Math Cipher",      "Solve equations. 3 lives. Type and press ENTER.",     "math"),
    5:  ("Hard Math",        "Multi-step word problems — think carefully!",         "math"),
    6:  ("Maze Escape",      "Navigate the maze. Use WASD or arrow keys.",          "maze"),
    7:  ("Deep Maze",        "Bigger maze, more paths. Find the exit!",             "maze"),
    8:  ("Memory Sequence",  "Watch the pattern. Repeat it perfectly.",             "sequence"),
    9:  ("Memory Sequence+", "Longer pattern, faster flashes. Stay sharp!",        "sequence"),
    10: ("Word Decode",      "Decode the Caesar cipher. 4 lives. [H] for hint.",   "word"),
}

def build_puzzle(level):
    _, _, ptype = LEVEL_INFO[level]
    if ptype == "sliding":  return SlidingPuzzle(level)
    if ptype == "math":     return MathPuzzle(level)
    if ptype == "maze":     return MazePuzzle(level)
    if ptype == "sequence": return SequencePuzzle(level)
    if ptype == "word":     return WordPuzzle(level)


# =============================================================================
#  SCREENS
# =============================================================================
class Screen:
    def handle(self, events, dt): pass
    def draw(self): pass


# ── Main Menu ─────────────────────────────────────────────────────────────────
class MainMenu(Screen):
    def __init__(self, has_save):
        self.has_save = has_save
        self.t = 0; self.hovered = None

    def _buttons(self):
        btns = []
        if self.has_save:
            btns.append(("CONTINUE", pygame.Rect(SCREEN_W//2-150, 320, 300, 54), "continue"))
        btns.append(("NEW GAME", pygame.Rect(SCREEN_W//2-150, 390 if self.has_save else 330, 300, 54), "new"))
        btns.append(("EXIT",     pygame.Rect(SCREEN_W//2-150, 460 if self.has_save else 400, 300, 54), "exit"))
        return btns

    def handle(self, events, dt):
        self.t += dt
        mx, my = pygame.mouse.get_pos(); self.hovered = None
        for _, rect, tag in self._buttons():
            if rect.collidepoint(mx, my): self.hovered = tag
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                for _, rect, tag in self._buttons():
                    if rect.collidepoint(mx, my): return tag
        return None

    def draw(self):
        screen.fill(C_BG); draw_stars(self.t)
        gv = int(128 + 80 * math.sin(self.t * 1.5))
        for dx, dy in [(3,3),(-1,1)]:
            img = F_TITLE.render("MIND MAZE", True, C_DARK)
            screen.blit(img, (SCREEN_W//2 - img.get_width()//2+dx, 120+dy))
        draw_text(screen, "MIND MAZE", F_TITLE, (80, gv, 255), SCREEN_W//2, 120, center=True)
        draw_text(screen, "A Puzzle Adventure", F_BODY, C_MUTED, SCREEN_W//2, 195, center=True)
        for i, (name, _, _) in enumerate(LEVEL_INFO.values()):
            ox = 50 + (i%5)*185; oy = 230 + (i//5)*38
            r = pygame.Rect(ox, oy, 170, 28)
            pygame.draw.rect(screen, C_KEY_BG, r, border_radius=6)
            pygame.draw.rect(screen, C_WALL, r, 1, border_radius=6)
            draw_text(screen, f"Lv{i+1}: {name}", F_TINY, C_MUTED, r.centerx, r.centery, center=True)
        for label, rect, tag in self._buttons():
            draw_button(screen, rect, label, F_H2,
                        C_ACCENT if tag != "exit" else (60,30,60),
                        hover=self.hovered == tag)
        draw_text(screen, "© Tushar's Build",
                  F_TINY, C_MUTED, SCREEN_W//2, SCREEN_H-24, center=True)
        for p in particles: p.draw(screen)


# ── Level Select ──────────────────────────────────────────────────────────────
class LevelSelectScreen(Screen):
    def __init__(self):
        self.t = 0; self.hovered = None

    def _rects(self):
        cols, tw, th, gx, gy = 5, 160, 80, 20, 20
        sx = (SCREEN_W - (cols*tw + (cols-1)*gx)) // 2; sy = 200
        return [pygame.Rect(sx+(i%cols)*(tw+gx), sy+(i//cols)*(th+gy), tw, th)
                for i in range(10)]

    def handle(self, events, dt):
        self.t += dt
        mx, my = pygame.mouse.get_pos(); self.hovered = None
        for i, rect in enumerate(self._rects()):
            if rect.collidepoint(mx, my): self.hovered = i+1
        back = pygame.Rect(40, SCREEN_H-70, 130, 44)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back.collidepoint(mx, my): return ("back", None)
                for i, rect in enumerate(self._rects()):
                    if rect.collidepoint(mx, my): return ("select", i+1)
        return None

    def draw(self):
        screen.fill(C_BG); draw_stars(self.t)
        draw_text(screen, "SELECT STARTING LEVEL", F_H1, C_ACCENT, SCREEN_W//2, 100, center=True)
        draw_text(screen, "Level 1 recommended for new players", F_BODY, C_MUTED, SCREEN_W//2, 150, center=True)
        for i, rect in enumerate(self._rects()):
            lv = i+1; name, _, _ = LEVEL_INFO[lv]
            hover = self.hovered == lv
            col = C_ACCENT if lv<=3 else (C_GOLD if lv<=5 else (C_GREEN if lv<=7 else C_ACCENT2))
            if hover: draw_glow_rect(screen, rect, col, radius=10)
            else:
                pygame.draw.rect(screen, C_KEY_BG, rect, border_radius=10)
                pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            draw_text(screen, f"Level {lv}", F_H2, col, rect.centerx, rect.y+18, center=True)
            draw_text(screen, name, F_TINY, C_MUTED, rect.centerx, rect.y+50, center=True)
        back = pygame.Rect(40, SCREEN_H-70, 130, 44)
        draw_button(screen, back, "← BACK", F_BODY, (40,20,60),
                    hover=back.collidepoint(*pygame.mouse.get_pos()))


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

    def _next_level(self):
        if self.level >= 10: return "win"
        self.level += 1
        self.puzzle = build_puzzle(self.level)
        self.dead   = False
        save_game(self.level)
        return None

    def handle(self, events, dt):
        self.t += dt
        if self.feedback_timer > 0: self.feedback_timer -= dt

        _, _, ptype = LEVEL_INFO[self.level]

        if ptype == "sequence":
            self.puzzle.update(dt)

        if ptype in ("math", "word"):
            if self.puzzle.fb_timer > 0: self.puzzle.fb_timer -= dt

        mx, my = pygame.mouse.get_pos()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    save_game(self.level); return "menu"

                if ptype == "maze":
                    moves = {pygame.K_UP:(0,-1), pygame.K_DOWN:(0,1),
                             pygame.K_LEFT:(-1,0), pygame.K_RIGHT:(1,0),
                             pygame.K_w:(0,-1), pygame.K_s:(0,1),
                             pygame.K_a:(-1,0), pygame.K_d:(1,0)}
                    if e.key in moves:
                        self.puzzle.move(*moves[e.key])
                        if self.puzzle.solved():
                            spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GREEN, 40)
                            if self._next_level() == "win": return "win"

                if ptype in ("math", "word"):
                    if e.key == pygame.K_BACKSPACE:
                        self.puzzle.input_str = self.puzzle.input_str[:-1]
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        result = self.puzzle.submit()
                        if result == "correct":
                            spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GOLD, 50)
                            if self._next_level() == "win": return "win"
                        elif result == "dead":
                            self.dead = True
                    elif ptype == "word" and e.key == pygame.K_h:
                        self.feedback_msg   = self.puzzle.hint()
                        self.feedback_timer = 3.0
                    else:
                        ch = e.unicode
                        if ptype == "math" and (ch.isdigit() or ch == "-"):
                            self.puzzle.input_str += ch
                        elif ptype == "word" and ch.isalpha():
                            self.puzzle.input_str += ch.upper()

            if e.type == pygame.MOUSEBUTTONDOWN:
                back_rect = pygame.Rect(20, 20, 120, 38)
                if back_rect.collidepoint(mx, my):
                    save_game(self.level); return "menu"

                if ptype == "sliding":
                    ts = 90 if self.puzzle.size == 3 else 68
                    n  = self.puzzle.size; total = n*(ts+4)
                    ox = SCREEN_W//2 - total//2; oy = SCREEN_H//2 - total//2 + 20
                    for i in range(n*n):
                        r, c = divmod(i, n)
                        rect = pygame.Rect(ox+c*(ts+4), oy+r*(ts+4), ts, ts)
                        if rect.collidepoint(mx, my):
                            self.puzzle.click(i)
                            if self.puzzle.solved():
                                spawn_particles(SCREEN_W//2, SCREEN_H//2, C_ACCENT, 40)
                                if self._next_level() == "win": return "win"

                if ptype == "sequence" and self.seq_btns:
                    if self.puzzle.show_retry:
                        retry_rect = pygame.Rect(SCREEN_W//2-110, SCREEN_H//2+60, 220, 52)
                        if retry_rect.collidepoint(mx, my):
                            self.puzzle.reset_for_retry()
                    else:
                        for i, rect in enumerate(self.seq_btns):
                            if rect.collidepoint(mx, my):
                                result = self.puzzle.press(i)
                                if result == "correct":
                                    spawn_particles(SCREEN_W//2, SCREEN_H//2, C_GREEN, 40)
                                    if self._next_level() == "win": return "win"

                if self.dead:
                    restart_rect = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2+60,  200, 50)
                    menu_rect    = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2+125, 200, 50)
                    if restart_rect.collidepoint(mx, my):
                        self.puzzle = build_puzzle(self.level); self.dead = False
                    if menu_rect.collidepoint(mx, my):
                        save_game(self.level); return "menu"

        return None

    def draw(self):
        screen.fill(C_BG); draw_stars(self.t)
        dt = clock.get_time() / 1000
        for p in particles[:]:
            if not p.update(dt): particles.remove(p)
        for p in particles: p.draw(screen)

        name, desc, ptype = LEVEL_INFO[self.level]
        draw_text(screen, f"LEVEL {self.level} — {name}", F_H2, C_ACCENT, SCREEN_W//2, 35, center=True)
        draw_text(screen, desc, F_BODY, C_MUTED, SCREEN_W//2, 68, center=True)

        bar_w = 400; bar_x = SCREEN_W//2 - bar_w//2
        pygame.draw.rect(screen, C_KEY_BG, (bar_x, 90, bar_w, 8), border_radius=4)
        pygame.draw.rect(screen, C_ACCENT, (bar_x, 90, int(bar_w*self.level/10), 8), border_radius=4)

        back = pygame.Rect(20, 20, 120, 38)
        draw_button(screen, back, "← MENU", F_SMALL, (40,20,60),
                    hover=back.collidepoint(*pygame.mouse.get_pos()))

        if self.dead:
            self._draw_dead(); return

        if ptype == "sliding":
            ts = 90 if self.puzzle.size == 3 else 68
            n = self.puzzle.size; total = n*(ts+4)
            ox = SCREEN_W//2 - total//2; oy = SCREEN_H//2 - total//2 + 20
            self.puzzle.draw(screen, ox, oy, tile_size=ts)
            draw_text(screen, f"Moves: {self.puzzle.moves}", F_BODY, C_MUTED,
                      SCREEN_W//2, oy+total+20, center=True)

        elif ptype == "math":
            self.puzzle.draw(screen, SCREEN_W//2, SCREEN_H//2 - 20)

        elif ptype == "maze":
            cell = 30 if self.puzzle.cols <= 15 else 22
            tw = self.puzzle.cols*cell; th = self.puzzle.rows*cell
            ox = SCREEN_W//2 - tw//2; oy = SCREEN_H//2 - th//2 + 30
            self.puzzle.draw(screen, ox, oy, cell)
            draw_text(screen, "WASD / Arrow Keys to move", F_SMALL, C_MUTED,
                      SCREEN_W//2, oy+th+14, center=True)

        elif ptype == "sequence":
            self._draw_sequence()

        elif ptype == "word":
            self.puzzle.draw(screen, SCREEN_W//2, SCREEN_H//2 - 60)

        if self.feedback_timer > 0:
            draw_text(screen, self.feedback_msg, F_BODY, C_GOLD,
                      SCREEN_W//2, SCREEN_H-60, center=True)

        draw_text(screen, "ESC → Menu  (progress saved)", F_TINY, C_MUTED,
                  SCREEN_W-20, SCREEN_H-18)

    def _draw_sequence(self):
        p = self.puzzle

        # ── Countdown ──
        if p.phase == "countdown":
            secs  = math.ceil(p.countdown) if p.countdown > 0 else 1
            pulse = 1.0 + 0.15 * math.sin(self.t * 8)
            size  = int(130 * pulse)
            f_big = load_font(size, bold=True)
            col_map = {3: C_ACCENT, 2: C_GOLD, 1: C_ERROR}
            col = col_map.get(secs, C_WHITE)
            draw_text(screen, str(secs), f_big, col, SCREEN_W//2, SCREEN_H//2 - 40, center=True)
            draw_text(screen, "Get ready to remember the pattern!",
                      F_H2, C_MUTED, SCREEN_W//2, SCREEN_H//2 + 100, center=True)
            # Dimmed button preview
            btn_size = 120; gap = 20
            total_w  = 4*btn_size + 3*gap
            sx = SCREEN_W//2 - total_w//2; sy = SCREEN_H//2 + 150
            for i in range(4):
                rect = pygame.Rect(sx+i*(btn_size+gap), sy, btn_size, btn_size)
                c2 = p.colors[i]
                pygame.draw.rect(screen, tuple(c//5 for c in c2), rect, border_radius=12)
                pygame.draw.rect(screen, c2, rect, 1, border_radius=12)
                draw_text(screen, p.labels[i], F_H2, c2,
                          rect.centerx, rect.centery, center=True)
            return

        # ── Show / Input ──
        if p.phase == "show":
            phase_text = "Watch the sequence..."
            prog_text  = f"Showing: {min(p.show_idx+1, len(p.sequence))} / {len(p.sequence)}"
        elif p.phase in ("input", "wrong_flash"):
            phase_text = "Your turn!  Repeat it."
            prog_text  = f"Input: {len(p.player_in)} / {len(p.sequence)}"
        else:
            phase_text = ""; prog_text = ""

        draw_text(screen, phase_text, F_H2, C_GOLD,  SCREEN_W//2, 160, center=True)
        draw_text(screen, prog_text,  F_BODY, C_MUTED, SCREEN_W//2, 200, center=True)

        self.seq_btns = p.draw(screen, SCREEN_W//2, SCREEN_H//2 + 60)

        # ── Retry overlay ──
        if p.show_retry:
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 175)); screen.blit(ov, (0, 0))
            draw_text(screen, "WRONG BUTTON!", F_H1, C_ERROR,
                      SCREEN_W//2, SCREEN_H//2 - 90, center=True)
            draw_text(screen, "Watch the pattern again carefully.",
                      F_H2, C_MUTED, SCREEN_W//2, SCREEN_H//2 - 40, center=True)
            draw_text(screen, "The same sequence will replay from the start.",
                      F_BODY, C_MUTED, SCREEN_W//2, SCREEN_H//2, center=True)
            retry_rect = pygame.Rect(SCREEN_W//2-110, SCREEN_H//2+60, 220, 52)
            mx, my = pygame.mouse.get_pos()
            draw_button(screen, retry_rect, "RETRY →", F_H2, C_ACCENT,
                        hover=retry_rect.collidepoint(mx, my))

    def _draw_dead(self):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0,0,0,160)); screen.blit(ov, (0,0))
        draw_text(screen, "OUT OF LIVES", F_H1, C_ERROR, SCREEN_W//2, SCREEN_H//2-60, center=True)
        draw_text(screen, "The puzzle resets.", F_BODY, C_MUTED, SCREEN_W//2, SCREEN_H//2-20, center=True)
        restart = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2+60,  200, 50)
        menu    = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2+125, 200, 50)
        mx, my  = pygame.mouse.get_pos()
        draw_button(screen, restart, "TRY AGAIN", F_H2, C_ACCENT,   hover=restart.collidepoint(mx,my))
        draw_button(screen, menu,    "MAIN MENU", F_H2, (60,20,60), hover=menu.collidepoint(mx,my))


# ── Win Screen ────────────────────────────────────────────────────────────────
class WinScreen(Screen):
    def __init__(self):
        self.t = 0; delete_save()

    def handle(self, events, dt):
        self.t += dt
        if self.t > 0.5:
            spawn_particles(random.randint(100, SCREEN_W-100),
                            random.randint(100, SCREEN_H//2),
                            random.choice([C_GOLD,C_ACCENT,C_GREEN,C_ACCENT2]), 5)
        mx, my = pygame.mouse.get_pos()
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                btn = pygame.Rect(SCREEN_W//2-150, SCREEN_H//2+100, 300, 54)
                if btn.collidepoint(mx, my):
                    particles.clear(); return "menu"
        return None

    def draw(self):
        screen.fill(C_BG); draw_stars(self.t)
        for p in particles: p.draw(screen)
        gv = int(200 + 55*math.sin(self.t*2))
        draw_text(screen, "MIND MAZE CONQUERED!", F_H1, (255,gv,80),
                  SCREEN_W//2, SCREEN_H//2-120, center=True)
        draw_text(screen, "You solved all 10 levels!", F_H2, C_GREEN,
                  SCREEN_W//2, SCREEN_H//2-60, center=True)
        draw_text(screen, "Your mind is truly a maze master.", F_BODY, C_MUTED,
                  SCREEN_W//2, SCREEN_H//2, center=True)
        btn = pygame.Rect(SCREEN_W//2-150, SCREEN_H//2+100, 300, 54)
        draw_button(screen, btn, "BACK TO MENU", F_H2, C_ACCENT,
                    hover=btn.collidepoint(*pygame.mouse.get_pos()))


# =============================================================================
#  MAIN LOOP
# =============================================================================
def main():
    save = load_game()
    current = MainMenu(has_save=save is not None)

    while True:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        result = current.handle(events, dt)

        if result == "continue" and save:
            current = GameScreen(start_level=save["level"]); save = None
        elif result == "new":
            current = LevelSelectScreen()
        elif isinstance(result, tuple) and result[0] == "select":
            delete_save(); current = GameScreen(start_level=result[1])
        elif isinstance(result, tuple) and result[0] == "back":
            save = load_game(); current = MainMenu(has_save=save is not None)
        elif result == "menu":
            save = load_game(); current = MainMenu(has_save=save is not None)
        elif result == "win":
            current = WinScreen()
        elif result == "exit":
            pygame.quit(); sys.exit()

        current.draw()
        pygame.display.flip()

if __name__ == "__main__":
    main()
