# 🏺 Wumpus World - AI Agent Navigation

A modern implementation of the classic Wumpus World AI problem with an intelligent agent that uses logical reasoning and probabilistic inference to navigate a dangerous cave system.

## 📋 Table of Contents

- [Overview](#overview)
- [Game Rules](#game-rules)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Game Logic](#game-logic)
- [AI Agent Architecture](#ai-agent-architecture)
- [File Structure](#file-structure)
- [Grid Format](#grid-format)
- [Features](#features)
- [Controls](#controls)

## 🎯 Overview

The Wumpus World is a classic AI problem where an intelligent agent must navigate a 10x10 grid cave system to find gold while avoiding deadly pits and multiple Wumpuses. The agent uses logical reasoning, probability calculations, and strategic planning to survive and succeed.

### Key Objectives:
- 🏆 Find and collect the gold
- 🏠 Return safely to the starting position (0,0)
- 💀 Avoid falling into pits or being eaten by Wumpuses
- 🏹 Use the arrow strategically to eliminate Wumpuses when necessary

## 🎮 Game Rules

### Environment Elements:
- **Agent (🤖)**: The AI player that navigates the world
- **Gold (💰)**: The treasure to be collected (+1000 points)
- **Wumpus (👹)**: Deadly creatures that kill the agent on contact
- **Pits (⚫)**: Deep holes that cause instant death
- **Safe Cells**: Empty spaces that can be traversed safely

### Percepts (Sensory Information):
- **Stench**: Detected when adjacent to a living Wumpus
- **Breeze**: Detected when adjacent to a pit
- **Glitter**: Detected when gold is in the same cell
- **Scream**: Heard when a Wumpus is killed by an arrow

### Actions Available:
- **Movement**: Forward, TurnLeft, TurnRight
- **Interaction**: Grab (gold), Climb (exit at start)
- **Combat**: Shoot (arrow in current direction)

### Scoring System:
- **+1000**: Collecting gold
- **+500**: Successfully climbing out with gold
- **-1**: Each movement action
- **-10**: Shooting the arrow
- **Death**: Game over (pit or Wumpus)

## 🚀 Setup & Installation

### Prerequisites:
- Python 3.7 or higher
- tkinter (usually included with Python)

### Installation Steps:

1. **Clone or download the project files**
```bash
# Ensure all files are in the same directory:
# main.py, agent.py, environment.py, game_interface.py
# knowledge_base.py, Action.py, grid*.txt files
```

2. **No additional dependencies required** - uses only Python standard library

3. **Verify installation**
```bash
python main.py
```

## 💻 Usage

### Basic Usage:
```bash
python main.py
```

### Command Line Options:
The game loads `grid2.txt` by default. To use different grids, modify the `grid_file_path` in `main.py`:

```python
grid_file_path = "grid2.txt"  # Change to grid.txt, grid3.txt, etc.
```

### Available Grid Files:
- `grid.txt` - Complex layout with multiple Wumpuses and pits
- `grid2.txt` - Moderate difficulty (default)
- `grid3.txt` - Multiple Wumpuses spread across the map
- `grid4.txt` - Strategic pit placement
- `grid5.txt` - High difficulty with dense obstacles

## 🧠 Game Logic

### Core Game Loop:

1. **Perception Phase**
   - Agent receives sensory information (Stench, Breeze, Glitter)
   - Updates knowledge base with new percepts
   - Analyzes safety of current and adjacent positions

2. **Reasoning Phase**
   - Processes percepts using logical inference
   - Updates probability maps for dangers
   - Identifies safe, dangerous, and unknown cells
   - Plans optimal path to objectives

3. **Action Selection Phase**
   - Evaluates available actions using utility functions
   - Considers safety, exploration value, and goal achievement
   - Applies epsilon-greedy strategy for exploration vs exploitation
   - Executes chosen action

4. **State Update Phase**
   - Updates agent position and orientation
   - Modifies game state based on action results
   - Updates score and game status

### Decision Making Process:

#### Priority System:
1. **Emergency Retreat**: If in immediate danger
2. **Gold Collection**: If gold is detected (Glitter)
3. **Wumpus Elimination**: Strategic arrow usage
4. **Safe Exploration**: Visit definitely safe unvisited cells
5. **Return Home**: Navigate back to start with gold
6. **Risk Assessment**: Evaluate risky moves when no safe options

#### Safety Analysis:
- **Definitely Safe**: Visited cells or cells with no danger possibilities
- **Probably Safe**: Cells in safe set but not definitively proven
- **Possibly Dangerous**: Cells in pit_possible or wumpus_possible sets
- **Definitely Dangerous**: Confirmed pit or Wumpus locations

## 🤖 AI Agent Architecture

### Knowledge Base System:

#### Core Data Structures:
```python
visited = set()              # Cells the agent has been to
safe_cells = set()           # Cells known to be safe
pit_possible = set()         # Cells that might contain pits
wumpus_possible = set()      # Cells that might contain Wumpuses
pit_definite = set()         # Confirmed pit locations
wumpus_definite = set()      # Confirmed Wumpus locations
no_pit = set()              # Cells definitely safe from pits
no_wumpus = set()           # Cells definitely safe from Wumpuses
```

#### Inference Rules:

**Pit Logic:**
- If Breeze detected → adjacent cells may have pits
- If no Breeze → adjacent cells are pit-free
- Visited cells cannot have pits

**Wumpus Logic:**
- If Stench detected → adjacent cells may have Wumpuses
- If no Stench → adjacent cells are Wumpus-free
- Multiple Wumpuses supported (configurable)

**Safety Inference:**
- Cell is safe if: visited OR (no pit AND no Wumpus possibilities)
- Cell is dangerous if: confirmed pit/Wumpus OR high probability

### Action Selection Algorithm:

#### Utility Calculation:
```python
def calculate_utility(action):
    utility = base_value
    
    # Safety considerations
    if definitely_safe(target):
        utility += 100
    elif dangerous(target):
        utility -= (pit_prob * 500 + wumpus_prob * 400)
    
    # Exploration bonus
    if unvisited(target):
        utility += curiosity_bonus + information_gain
    
    # Distance penalty
    utility -= manhattan_distance * 2
    
    return utility
```

#### Epsilon-Greedy Strategy:
- **Exploration**: Random action with probability ε (decays over time)
- **Exploitation**: Choose action with highest utility
- **Tie-breaking**: Random selection among equally good actions

### Path Planning:

#### A* Search Algorithm:
- **Heuristic**: Manhattan distance to goal
- **Cost**: Number of moves required
- **Constraints**: Only use definitely safe cells
- **Fallback**: Risk assessment if no safe path exists

## 📁 File Structure

```
wumpus-world/
├── main.py              # Entry point and game initialization
├── agent.py             # AI agent implementation
├── environment.py       # Game world simulation
├── game_interface.py    # Modern GUI interface
├── knowledge_base.py    # Logical reasoning system
├── Action.py           # Action selection and utility calculation
├── grid.txt            # Game scenario 1
├── grid2.txt           # Game scenario 2 (default)
├── grid3.txt           # Game scenario 3
├── grid4.txt           # Game scenario 4
├── grid5.txt           # Game scenario 5
└── README.md           # This file
```

### File Descriptions:

#### `main.py`
- Application entry point
- Grid file parsing
- GUI initialization
- Game loop coordination

#### `agent.py` (1,200+ lines)
- **WumpusAgent class**: Main AI agent implementation
- **Decision making**: Action selection and planning
- **State management**: Position, direction, inventory tracking
- **Strategy execution**: Emergency handling, exploration, goal pursuit

#### `environment.py`
- **WumpusEnvironment class**: Game world simulation
- **World generation**: Random and file-based environment creation
- **Physics simulation**: Movement, collision detection
- **Percept generation**: Stench, Breeze, Glitter detection

#### `game_interface.py` (900+ lines)
- **ModernWumpusWorldGUI class**: Advanced graphical interface
- **Real-time visualization**: Animated agent, environment rendering
- **Interactive controls**: Manual stepping, auto-play, speed control
- **Status displays**: Knowledge base, agent statistics, game state

#### `knowledge_base.py`
- **KnowledgeBase class**: Logical reasoning engine
- **Inference system**: Percept processing and logical deduction
- **Probability calculation**: Risk assessment for unknown cells
- **Safety analysis**: Definitive and probabilistic safety determination

#### `Action.py`
- **Action enum**: Available action types
- **ActionSelector class**: Intelligent action selection
- **Utility functions**: Action evaluation and comparison
- **Exploration strategy**: Epsilon-greedy with curiosity bonus

## 🗺️ Grid Format

### Grid File Structure:
- **10x10 character grid**
- **Coordinate system**: (0,0) at bottom-left, (9,9) at top-right
- **File format**: Text file with one row per line

### Symbol Legend:
```
- : Empty space (safe)
P : Pit (deadly)
W : Wumpus (deadly, can be killed)
G : Gold (objective)
```

### Example Grid (grid2.txt):
```
--P-------  # Row 9 (top)
------W---  # Row 8
----P-----  # Row 7
---G--P---  # Row 6
W------P--  # Row 5
-----W----  # Row 4
--P-------  # Row 3
------P---  # Row 2
----P---W-  # Row 1
----------  # Row 0 (bottom, agent starts at 0,0)
```

### Grid Coordinate Mapping:
- **File row 0** → **World Y=9** (top of display)
- **File row 9** → **World Y=0** (bottom of display, start position)
- **Agent starts**: Always at world coordinates (0,0)

## ✨ Features

### Modern GUI Interface:
- **Real-time visualization** with smooth animations
- **Interactive controls** for stepping through agent decisions
- **Knowledge base display** showing agent's reasoning
- **Status panels** with detailed game information
- **Customizable speed** for auto-play mode

### Advanced AI Capabilities:
- **Multi-Wumpus support** (configurable number)
- **Probabilistic reasoning** for uncertain situations
- **Strategic arrow usage** with high-confidence targeting
- **Emergency retreat** when in immediate danger
- **Optimal path planning** using A* search algorithm

### Flexible Environment System:
- **Random world generation** with configurable parameters
- **File-based scenarios** for consistent testing
- **Multiple difficulty levels** through different grid files
- **Save/load functionality** for custom environments

## 🎮 Controls

### GUI Controls:

#### Environment Management:
- **🎲 Generate Random**: Create new random world
- **📁 Load Environment**: Load saved environment file
- **💾 Save Environment**: Save current environment
- **📋 Load Grid File**: Load from grid text files

#### Game Control:
- **▶️ Start Game**: Begin agent execution
- **⏭️ Step**: Execute single agent action
- **⏯️ Auto Play**: Toggle continuous execution
- **🔄 Reset**: Reset game to initial state

#### Display Options:
- **Speed Control**: Adjust auto-play speed (milliseconds)
- **Real-time Updates**: Knowledge base and status information
- **Visual Indicators**: Agent state, inventory, danger zones

### Keyboard Shortcuts:
- **Space**: Step through one action
- **Enter**: Start/stop auto-play
- **R**: Reset game
- **Escape**: Exit application

## 🏆 Scoring & Performance

### Score Components:
- **Gold Collection**: +1000 points
- **Successful Exit**: +500 points
- **Movement Penalty**: -1 point per move
- **Arrow Cost**: -10 points per shot
- **Death Penalty**: Game over

### Performance Metrics:
- **Success Rate**: Percentage of games completed successfully
- **Average Score**: Points earned across multiple games
- **Efficiency**: Steps taken to complete objectives
- **Survival Rate**: Percentage of games where agent survives

### Optimal Strategy:
1. **Conservative Exploration**: Only move to definitely safe cells
2. **Information Gathering**: Prioritize moves that reveal new information
3. **Strategic Shooting**: Only shoot when Wumpus probability > 70%
4. **Efficient Pathfinding**: Use shortest safe path to objectives
5. **Risk Management**: Retreat when no safe options available

---

## 🔧 Advanced Configuration

### Customizing Agent Behavior:

#### In `agent.py`:
```python
# Adjust risk tolerance
self.danger_threshold = 0.1  # Lower = more conservative

# Modify exploration strategy
self.action_selector = ActionSelector(
    epsilon=0.1,           # Exploration rate
    curiosity_weight=0.3,  # Exploration bonus
    decay_rate=0.995       # Learning rate decay
)
```

#### In `environment.py`:
```python
# Change world parameters
def __init__(self, size=10, num_wumpuses=2):
    self.size = size              # World dimensions
    self.num_wumpuses = num_wumpuses  # Number of Wumpuses
```

### Creating Custom Grids:

1. **Create new .txt file** with 10x10 character grid
2. **Use symbols**: `-` (empty), `P` (pit), `W` (Wumpus), `G` (gold)
3. **Update main.py** to reference your grid file
4. **Test thoroughly** to ensure solvability

---

*This implementation demonstrates advanced AI techniques including logical reasoning, probabilistic inference, strategic planning, and adaptive behavior in uncertain environments.*