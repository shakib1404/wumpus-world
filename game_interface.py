# wumpus_world/game_interface.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from environment import WumpusEnvironment
from agent import WumpusAgent

class WumpusWorldGUI:
    """Graphical User Interface for Wumpus World"""
    
    def __init__(self, grid=None):
        self.root = tk.Tk()
        self.root.title("Wumpus World - AI Agent Navigation")
        self.root.geometry("1200x800")
        
        self.environment = WumpusEnvironment(10)
        self.agent = WumpusAgent(10)
        self.game_running = False
        self.auto_play = False
        
        # Load environment from grid if provided
        if grid:
            self.load_environment_from_grid(grid)
        else:
            self.environment.generate_random_environment()
        
        self.setup_ui()
        self.reset_game()
    
    def load_environment_from_grid(self, grid):
        """Load environment from grid representation"""
        self.environment.size = len(grid)
        self.environment.pits.clear()
        
        wumpus_positions = []
        
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                # Convert grid coordinates (y increases downward) to world coordinates (y increases upward)
                world_y = len(grid) - 1 - y
                
                if cell == 'P':
                    self.environment.pits.add((x, world_y))
                elif cell == 'W':
                    wumpus_positions.append((x, world_y))
                elif cell == 'G':
                    self.environment.gold_pos = (x, world_y)
        
        # Set the first Wumpus position (there should be only one, but handle multiple)
        if wumpus_positions:
            self.environment.wumpus_pos = wumpus_positions[0]
            if len(wumpus_positions) > 1:
                print(f"Warning: Multiple Wumpus positions found. Using {wumpus_positions[0]}")
        
        # If no gold position found, place it randomly (avoiding start, pits, and Wumpus)
        if not self.environment.gold_pos:
            while True:
                pos = (random.randint(0, self.environment.size-1), 
                       random.randint(0, self.environment.size-1))
                if (pos != (0, 0) and 
                    pos not in self.environment.pits and 
                    pos != self.environment.wumpus_pos):
                    self.environment.gold_pos = pos
                    break
        
        print(f"Environment loaded from grid:")
        print(f"- Wumpus at: {self.environment.wumpus_pos}")
        print(f"- Gold at: {self.environment.gold_pos}")
        print(f"- Pits at: {sorted(list(self.environment.pits))}")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for game grid
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right panel for controls and info
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Game grid
        self.setup_game_grid(left_frame)
        
        # Control panel
        self.setup_control_panel(right_frame)
        
        # Status panel
        self.setup_status_panel(right_frame)
        
        # Knowledge base panel
        self.setup_knowledge_panel(right_frame)
    
    def setup_game_grid(self, parent):
        """Setup the game grid display"""
        grid_frame = ttk.LabelFrame(parent, text="Wumpus World (10x10)")
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(grid_frame, width=500, height=500, bg='white')
        self.canvas.pack(padx=10, pady=10)
        
        self.cell_size = 48
        self.grid_offset = 10
    
    def setup_control_panel(self, parent):
        """Setup the control panel"""
        control_frame = ttk.LabelFrame(parent, text="Controls")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Environment controls
        ttk.Button(control_frame, text="Generate Random", 
                  command=self.generate_random_environment).pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="Load Environment", 
                  command=self.load_environment).pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="Save Environment", 
                  command=self.save_environment).pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="Load Grid File", 
                  command=self.load_grid_file).pack(fill=tk.X, pady=2)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Game controls
        self.start_button = ttk.Button(control_frame, text="Start Game", 
                                      command=self.start_game)
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.step_button = ttk.Button(control_frame, text="Step", 
                                     command=self.step_game, state='disabled')
        self.step_button.pack(fill=tk.X, pady=2)
        
        self.auto_button = ttk.Button(control_frame, text="Auto Play", 
                                     command=self.toggle_auto_play, state='disabled')
        self.auto_button.pack(fill=tk.X, pady=2)
        
        self.reset_button = ttk.Button(control_frame, text="Reset Game", 
                                      command=self.reset_game)
        self.reset_button.pack(fill=tk.X, pady=2)
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed (ms):").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="1000")
        speed_entry = ttk.Entry(speed_frame, textvariable=self.speed_var, width=8)
        speed_entry.pack(side=tk.RIGHT)
    
    def setup_status_panel(self, parent):
        """Setup the status panel"""
        status_frame = ttk.LabelFrame(parent, text="Agent Status")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=8, width=40, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_knowledge_panel(self, parent):
        """Setup the knowledge base panel"""
        kb_frame = ttk.LabelFrame(parent, text="Knowledge Base")
        kb_frame.pack(fill=tk.BOTH, expand=True)
        
        self.kb_text = tk.Text(kb_frame, height=15, width=40, wrap=tk.WORD)
        kb_scrollbar = ttk.Scrollbar(kb_frame, orient=tk.VERTICAL, command=self.kb_text.yview)
        self.kb_text.configure(yscrollcommand=kb_scrollbar.set)
        
        self.kb_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def draw_grid(self):
        """Draw the game grid"""
        self.canvas.delete("all")
        
        # Draw grid lines
        for i in range(11):
            x = self.grid_offset + i * self.cell_size
            y = self.grid_offset + i * self.cell_size
            self.canvas.create_line(self.grid_offset, y, 
                                  self.grid_offset + 10 * self.cell_size, y, fill='gray')
            self.canvas.create_line(x, self.grid_offset, 
                                  x, self.grid_offset + 10 * self.cell_size, fill='gray')
        
        # Draw coordinate labels
        for i in range(10):
            # X-axis labels (bottom)
            x = self.grid_offset + i * self.cell_size + self.cell_size // 2
            y = self.grid_offset + 10 * self.cell_size + 15
            self.canvas.create_text(x, y, text=str(i), font=('Arial', 8))
            
            # Y-axis labels (left)
            x = self.grid_offset - 15
            y = self.grid_offset + (9 - i) * self.cell_size + self.cell_size // 2
            self.canvas.create_text(x, y, text=str(i), font=('Arial', 8))
        
        # Draw environment elements
        for x in range(10):
            for y in range(10):
                canvas_x = self.grid_offset + x * self.cell_size
                canvas_y = self.grid_offset + (9 - y) * self.cell_size  # Flip Y coordinate
                
                # Draw pits
                if (x, y) in self.environment.pits:
                    self.canvas.create_rectangle(canvas_x + 2, canvas_y + 2, 
                                               canvas_x + self.cell_size - 2, 
                                               canvas_y + self.cell_size - 2, 
                                               fill='black', outline='black')
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="PIT", fill='white', font=('Arial', 8, 'bold'))
                
                # Draw Wumpus
                if (x, y) == self.environment.wumpus_pos and self.environment.wumpus_alive:
                    self.canvas.create_rectangle(canvas_x + 2, canvas_y + 2, 
                                               canvas_x + self.cell_size - 2, 
                                               canvas_y + self.cell_size - 2, 
                                               fill='red', outline='red')
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="W", fill='white', font=('Arial', 16, 'bold'))
                
                # Draw gold
                if (x, y) == self.environment.gold_pos and not self.environment.agent_has_gold:
                    self.canvas.create_oval(canvas_x + self.cell_size//4, 
                                          canvas_y + self.cell_size//4,
                                          canvas_x + 3*self.cell_size//4, 
                                          canvas_y + 3*self.cell_size//4, 
                                          fill='gold', outline='orange', width=2)
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="G", fill='black', font=('Arial', 12, 'bold'))
                
                # Draw visited cells
                if (x, y) in self.agent.kb.visited:
                    self.canvas.create_rectangle(canvas_x + 1, canvas_y + 1, 
                                               canvas_x + self.cell_size - 1, 
                                               canvas_y + self.cell_size - 1, 
                                               fill='lightblue', outline='blue', width=1)
                
                # Draw safe cells
                if (x, y) in self.agent.kb.safe_cells and (x, y) not in self.agent.kb.visited:
                    self.canvas.create_rectangle(canvas_x + 1, canvas_y + 1, 
                                               canvas_x + self.cell_size - 1, 
                                               canvas_y + self.cell_size - 1, 
                                               fill='lightgreen', outline='green', width=1)
                
                # Draw possible dangers
                if (x, y) in self.agent.kb.pit_possible:
                    self.canvas.create_text(canvas_x + self.cell_size//4, 
                                          canvas_y + self.cell_size//4, 
                                          text="P?", fill='red', font=('Arial', 8))
                
                if (x, y) in self.agent.kb.wumpus_possible:
                    self.canvas.create_text(canvas_x + 3*self.cell_size//4, 
                                          canvas_y + self.cell_size//4, 
                                          text="W?", fill='red', font=('Arial', 8))
        
        # Draw agent
        agent_x, agent_y = self.agent.position
        canvas_x = self.grid_offset + agent_x * self.cell_size
        canvas_y = self.grid_offset + (9 - agent_y) * self.cell_size
        
        if self.environment.agent_alive:
            # Draw agent as triangle pointing in current direction
            center_x = canvas_x + self.cell_size // 2
            center_y = canvas_y + self.cell_size // 2
            size = self.cell_size // 3
            
            # Direction vectors: North, East, South, West
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            dx, dy = directions[self.agent.direction]
            
            # Triangle points
            points = [
                center_x + dx * size, center_y + dy * size,  # Tip
                center_x - dy * size//2 - dx * size//2, center_y + dx * size//2 - dy * size//2,  # Left
                center_x + dy * size//2 - dx * size//2, center_y - dx * size//2 - dy * size//2   # Right
            ]
            
            self.canvas.create_polygon(points, fill='blue', outline='darkblue', width=2)
            
            # Show if agent has gold
            if self.agent.has_gold:
                self.canvas.create_text(center_x, center_y + size + 8, 
                                      text="GOLD", fill='gold', font=('Arial', 8, 'bold'))
        else:
            # Draw dead agent
            self.canvas.create_text(canvas_x + self.cell_size//2, 
                                  canvas_y + self.cell_size//2, 
                                  text="☠", fill='red', font=('Arial', 20))
    
    def update_status(self):
        """Update the status display"""
        status = self.agent.get_status()
        percepts = self.environment.get_percepts()
        
        status_info = f"""Position: {status['position']}
Direction: {status['direction']}
Has Arrow: {status['has_arrow']}
Has Gold: {status['has_gold']}
Alive: {self.environment.agent_alive}

Current Percepts:
- Stench: {percepts.get('stench', False)}
- Breeze: {percepts.get('breeze', False)}
- Glitter: {percepts.get('glitter', False)}
- Bump: {percepts.get('bump', False)}
- Scream: {percepts.get('scream', False)}

Performance:
- Path Length: {status['path_length']}
- Actions Taken: {status['actions_taken']}
- Current Plan: {status['current_plan']} steps
- Loop Detected: {status['loop_detected']}

Environment:
- Wumpus at: {self.environment.wumpus_pos}
- Wumpus Alive: {self.environment.wumpus_alive}
- Gold at: {self.environment.gold_pos}
- Pits: {len(self.environment.pits)}
- Game Running: {self.game_running}
"""
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, status_info)
    
    def update_knowledge_base(self):
        """Update the knowledge base display"""
        kb_info = f"""Knowledge Base Summary:
- Visited Cells: {len(self.agent.kb.visited)}
- Safe Cells: {len(self.agent.kb.safe_cells)}
- Facts: {len(self.agent.kb.facts)}
- Clauses: {len(self.agent.kb.clauses)}
- Possible Pits: {len(self.agent.kb.pit_possible)}
- Possible Wumpus: {len(self.agent.kb.wumpus_possible)}

Recent Facts:
"""
        
        # Show last 10 facts
        recent_facts = list(self.agent.kb.facts)[-10:]
        for fact in recent_facts:
            kb_info += f"- {fact}\n"
        
        kb_info += f"\nSafe Cells: {sorted(list(self.agent.kb.safe_cells))}\n"
        kb_info += f"Visited Cells: {sorted(list(self.agent.kb.visited))}\n"
        
        if self.agent.kb.pit_possible:
            kb_info += f"Possible Pits: {sorted(list(self.agent.kb.pit_possible))}\n"
        
        if self.agent.kb.wumpus_possible:
            kb_info += f"Possible Wumpus: {sorted(list(self.agent.kb.wumpus_possible))}\n"
        
        kb_info += f"\nAction Sequence:\n"
        recent_actions = self.agent.action_sequence[-10:]
        for i, action in enumerate(recent_actions):
            kb_info += f"{len(self.agent.action_sequence) - len(recent_actions) + i + 1}. {action}\n"
        
        self.kb_text.delete(1.0, tk.END)
        self.kb_text.insert(tk.END, kb_info)
    
    def load_grid_file(self):
        """Load environment from grid file"""
        filename = filedialog.askopenfilename(
            title="Load Grid File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    grid = [list(line.strip()) for line in f if line.strip()]
                
                self.load_environment_from_grid(grid)
                self.reset_game()
                self.draw_grid()
                messagebox.showinfo("Grid Loaded", f"Grid loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load grid file: {str(e)}")
    
    def generate_random_environment(self):
        """Generate a new random environment"""
        self.environment.generate_random_environment()
        self.reset_game()
        self.draw_grid()
        messagebox.showinfo("Environment", "New random environment generated!")
    
    def load_environment(self):
        """Load environment from file"""
        filename = filedialog.askopenfilename(
            title="Load Environment",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.environment.load_from_file(filename)
                self.reset_game()
                self.draw_grid()
                messagebox.showinfo("Environment", f"Environment loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load environment: {str(e)}")
    
    def save_environment(self):
        """Save current environment to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Environment",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.environment.save_to_file(filename)
                messagebox.showinfo("Environment", f"Environment saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save environment: {str(e)}")
    
    def start_game(self):
        """Start the game"""
        self.game_running = True
        self.start_button.config(state='disabled')
        self.step_button.config(state='normal')
        self.auto_button.config(state='normal')
        
        # Initialize agent at starting position
        self.environment.agent_pos = (0, 0)
        self.environment.agent_direction = 0
        self.environment.agent_alive = True
        self.environment.agent_has_arrow = True
        self.environment.agent_has_gold = False
        self.environment.wumpus_alive = True
        
        self.agent.position = (0, 0)
        self.agent.direction = 0
        self.agent.has_arrow = True
        self.agent.has_gold = False
        
        # Get initial percepts
        percepts = self.environment.get_percepts()
        self.agent.add_percepts(percepts)
        
        self.update_display()
    
    def step_game(self):
        """Execute one step of the game"""
        if not self.game_running or not self.environment.agent_alive:
            return
        
        # Get current percepts
        percepts = self.environment.get_percepts()
        
        # Agent chooses action
        action = self.agent.choose_action(percepts)
        
        # Execute action in environment
        result = self.environment.move_agent(action)
        
        # Update agent state
        if action == 'FORWARD' and result['success']:
            self.agent.update_position(self.environment.agent_pos)
        elif action == 'TURN_LEFT' and result['success']:
            self.agent.direction = (self.agent.direction - 1) % 4
        elif action == 'TURN_RIGHT' and result['success']:
            self.agent.direction = (self.agent.direction + 1) % 4
        elif action == 'GRAB' and result['success']:
            self.agent.has_gold = True
        elif action == 'SHOOT' and result['success']:
            self.agent.has_arrow = False
        
        # Update environment state
        self.environment.agent_direction = self.agent.direction
        
        # Check game end conditions
        if result['game_over']:
            self.game_running = False
            self.auto_play = False
            self.start_button.config(state='normal')
            self.step_button.config(state='disabled')
            self.auto_button.config(text='Auto Play', state='disabled')
            
            if result['won']:
                messagebox.showinfo("Game Over", "Congratulations! Agent found the gold and escaped!")
            else:
                messagebox.showinfo("Game Over", "Game Over! Agent died or climbed out without gold.")
        
        self.update_display()
        
        # Continue auto play if enabled
        if self.auto_play and self.game_running:
            try:
                delay = int(self.speed_var.get())
            except ValueError:
                delay = 1000
            self.root.after(delay, self.step_game)
    
    def toggle_auto_play(self):
        """Toggle auto play mode"""
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.auto_button.config(text='Stop Auto')
            self.step_button.config(state='disabled')
            self.step_game()  # Start auto play
        else:
            self.auto_button.config(text='Auto Play')
            self.step_button.config(state='normal')
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.game_running = False
        self.auto_play = False
        
        # Reset environment
        self.environment.agent_pos = (0, 0)
        self.environment.agent_direction = 0
        self.environment.agent_alive = True
        self.environment.agent_has_arrow = True
        self.environment.agent_has_gold = False
        self.environment.wumpus_alive = True
        
        # Reset agent
        self.agent = WumpusAgent(self.environment.size)
        
        # Reset UI
        self.start_button.config(state='normal')
        self.step_button.config(state='disabled')
        self.auto_button.config(text='Auto Play', state='disabled')
        
        self.update_display()
    
    def update_display(self):
        """Update all display elements"""
        self.draw_grid()
        self.update_status()
        self.update_knowledge_base()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()