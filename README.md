# 🧠 Mind Maze
 
> A 10-level puzzle adventure built with Python & Pygame — where every level sharpens your mind.
 
---
 
## 📸 Overview
 
**Mind Maze** is a desktop puzzle game featuring 4 unique puzzle types across 10 progressively harder levels. It includes a polished animated UI, auto-save/load system, particle effects, and a lives-based challenge system for later levels.
 
---
 
## 🚀 Getting Started
 
### Prerequisites
 
- Python 3.8+
- pip
### Installation
 
```bash
# 1. Clone or download the project
git clone https://github.com/tusharsh-13/mind-Maze
cd mind-maze
 
# 2. Install the only dependency
pip install pygame
 
# 3. Run the game
python mind_maze.py
```
 
---
 
## 🎮 How to Play
 
### Main Menu
When you launch the game, you'll see the **Main Menu** with three options:
 
| Option | Description |
|--------|-------------|
| **Continue** | Resume from your last saved level |
| **New Game** | Pick any starting level (1–10) |
| **Exit** | Close the game |
 
> Progress is **automatically saved** whenever you advance a level or press `ESC` to return to the menu.
 
---
 
## 🧩 Puzzle Types & Levels
 
### Levels 1–3 · Sliding Tiles
Rearrange numbered tiles into the correct order by clicking tiles adjacent to the blank space.
 
- Level 1 → 3×3 grid, light shuffle
- Level 2 → 3×3 grid, harder shuffle
- Level 3 → 4×4 grid (classic 15-puzzle!)
**Controls:** Click a tile next to the blank space to slide it.
 
---
 
### Levels 4–5 · Memory Sequence
A Simon-says style pattern challenge. Watch the sequence light up, then repeat it in exact order.
 
- Level 4 → 7-step sequence
- Level 5 → 8-step sequence, faster flashes
**Controls:** Click the colored buttons (A / B / C / D) to replay the sequence.
 
---
 
### Levels 6–7 · Maze Navigation
Navigate a procedurally generated maze from the start cell to the glowing green exit.
 
- Level 6 → 11×11 maze
- Level 7 → 15×15 maze
**Controls:**
```
W / ↑   →   Move Up
S / ↓   →   Move Down
A / ←   →   Move Left
D / →   →   Move Right
```
 
---
 
### Levels 8–9 · Math Cipher
Solve a series of arithmetic equations against a 3-lives limit. Type your answer and press `Enter`.
 
- Level 8 → Addition & subtraction only (4 questions)
- Level 9 → Multiplication added to the mix (6 questions)
**Controls:** Type numbers on your keyboard → press `Enter` to submit.
 
> ❤️ You have **3 lives** — each wrong answer costs one. Lose all 3 and the puzzle resets.
 
---
 
### Level 10 · Word Decode
Decode a Caesar-cipher encoded word. The word is scrambled by a random letter shift.
 
- 4 lives
- Press `H` for a one-time hint that reveals the cipher shift value
**Controls:** Type your guess (letters only) → press `Enter` to submit.
 
**Example:**
```
Cipher:  HQFU\SWLRQ
Answer:  ENCRYPTION  (shift = 3)
```
 
---
 
## ⌨️ Global Controls
 
| Key | Action |
|-----|--------|
| `ESC` | Return to Main Menu (progress saved) |
| `H` | Show hint (Word Decode level only) |
| `Enter` | Submit answer (Math / Word levels) |
| `Backspace` | Delete last character (Math / Word levels) |
| `WASD` / `Arrow Keys` | Move player (Maze levels) |
 
---
 
## 💾 Save System
 
Mind Maze uses a lightweight JSON save file (`mind_maze_save.json`) stored in the same directory as the script.
 
- **Auto-saves** on level completion and when returning to the menu via `ESC`
- **Continue** option appears on the main menu only when a save exists
- **New Game** deletes any existing save and lets you start fresh from a chosen level
- Completing Level 10 **deletes the save file** automatically
---
 
## 📁 Project Structure
 
```
mind-maze/
│
├── mind_maze.py          # Main game file (single-file architecture)
├── mind_maze_save.json   # Auto-generated save file (created on first save)
└── README.md             # This file
```
 
---
 
## 🛠️ Tech Stack
 
| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core language |
| **Pygame** | Window, rendering, input, sound |
| **JSON** | Save/load system |
| **Random + Math** | Maze generation, puzzle randomization, animations |
 
---
 
## 🏗️ Architecture
 
The game is built around a simple **screen-state machine**:
 
```
MainMenu  ──►  LevelSelectScreen  ──►  GameScreen  ──►  WinScreen
    ▲                                      │
    └──────────────────────────────────────┘ (ESC / level complete)
```
 
Each puzzle type is its own class:
 
```
SlidingPuzzle   →  Levels 1–3
SequencePuzzle  →  Levels 4–5
MazePuzzle      →  Levels 6–7
MathPuzzle      →  Levels 8–9
WordPuzzle      →  Level 10
```
 
---
 
## ✨ Visual Features
 
- Animated **starfield background**
- **Particle burst effects** on puzzle completion
- **Glow rendering** on buttons, tiles, and the maze player
- Pulsing **level progress bar**
- Responsive **hover states** on all buttons
- **Lives display** with heart icons on challenge levels
---
 
## 🙋 FAQ
 
**Q: The game window doesn't open.**  
A: Make sure pygame is installed: `pip install pygame`
 
**Q: My save file is missing.**  
A: The save file (`mind_maze_save.json`) is created in the same folder as `mind_maze.py`. Make sure you're running the script from its own directory.
 
**Q: Can I add more levels?**  
A: Yes! Add entries to the `LEVEL_INFO` dictionary and create a new puzzle class. The `build_puzzle()` function maps level numbers to puzzle types.
 
**Q: The sequence puzzle reset on a wrong click. Is that a bug?**  
A: No — that's intentional for Levels 4–5. A wrong input resets the sequence so you watch it again.
 
---
 
## 👨‍💻 Author
 
Built by **Tushar** · BTech CSE · Bhopal, India  
Part of a personal project portfolio focused on Python, game development, and AI.
 
---
 
## 📄 License
 
This project is open-source and free to use for learning and personal projects.
 
---
 
*"Train your brain, one puzzle at a time."* 🧠


<img width="1247" height="913" alt="image" src="https://github.com/user-attachments/assets/2c745667-38fc-41de-b4b0-630521d63e1d" />

<img width="1248" height="913" alt="image" src="https://github.com/user-attachments/assets/09e18b45-2450-48b8-92cd-79a3f5a1b675" />




