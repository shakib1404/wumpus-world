# wumpus_world/game_interface.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
import random
from environment import WumpusEnvironment
from agent import WumpusAgent

class ModernWumpusWorldGUI:
    """Modern Graphical User Interface for Wumpus World"""

   
    
    def __init__(self, grid=None):
        self.root = tk.Tk()
        self.root.title("🏺 Wumpus World - AI Agent Navigation")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Modern color scheme
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3d3d3d',
            'accent': '#00d4ff',
            'accent_dark': '#0099cc',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'danger': '#ff4444',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'text_muted': '#888888',
            'grid_line': '#444444',
            'cell_visited': '#264653',
            'cell_safe': '#2a9d8f',
            'cell_danger': '#e76f51',
            'agent_color': '#00d4ff',
            'gold_color': '#ffd700',
            'wumpus_color': '#ff6b6b',
            'pit_color': '#2c2c2c'
        }
        
        self.environment = WumpusEnvironment(10)
        self.agent = WumpusAgent(10)
        self.game_running = False
        self.auto_play = False
        self.animation_id = None
        
        # Animation variables
        self.agent_scale = 1.0
        self.agent_rotation = 0.0
        self.pulse_phase = 0.0
        
        # Load environment from grid if provided
        if grid:
            self.load_environment_from_grid(grid)
        else:
            self.environment.generate_random_environment()
        
        self.setup_styles()
        self.setup_ui()
        self.reset_game()
        self.start_animations()
    
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        
        # Configure dark theme
        style.theme_use('clam')
        
        # Button styles
        style.configure('Modern.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['accent_dark'])])
        
        # Accent button style
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['bg_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_dark']),
                           ('pressed', self.colors['accent'])])
        
        # Frame styles
        style.configure('Modern.TFrame',
                       background=self.colors['bg_secondary'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_secondary'],
                       borderwidth=0,
                       relief='flat')
        
        # Label styles
        style.configure('Modern.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Title.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 12, 'bold'))
        
        # LabelFrame styles
        style.configure('Modern.TLabelframe',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('Modern.TLabelframe.Label',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Entry styles
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       insertcolor=self.colors['text_primary'])
        
        # Separator styles
        style.configure('Modern.TSeparator',
                       background=self.colors['grid_line'])
    
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
        
        # Set the first Wumpus position
        if wumpus_positions:
            self.environment.wumpus_pos = wumpus_positions[0]
            if len(wumpus_positions) > 1:
                print(f"Warning: Multiple Wumpus positions found. Using {wumpus_positions[0]}")
        
        # If no gold position found, place it randomly
        if not self.environment.gold_pos:
            while True:
                pos = (random.randint(0, self.environment.size-1), 
                       random.randint(0, self.environment.size-1))
                if (pos != (0, 0) and 
                    pos not in self.environment.pits and 
                    pos != self.environment.wumpus_pos):
                    self.environment.gold_pos = pos
                    break
    
    def setup_ui(self):
        """Setup the modern user interface"""
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="🏺 WUMPUS WORLD", 
                              font=('Segoe UI', 24, 'bold'),
                              fg=self.colors['accent'],
                              bg=self.colors['bg_primary'])
        title_label.pack(side=tk.LEFT, pady=10)
        
        subtitle_label = tk.Label(header_frame, 
                                 text="AI Agent Navigation System",
                                 font=('Segoe UI', 12),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_primary'])
        subtitle_label.pack(side=tk.LEFT, padx=(20, 0), pady=10)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for game grid
        left_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Right panel for controls and info
        right_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'], width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        # Setup panels
        self.setup_game_grid(left_frame)
        self.setup_control_panel(right_frame)
        self.setup_status_panel(right_frame)
        self.setup_knowledge_panel(right_frame)
    
    def setup_game_grid(self, parent):
        """Setup the modern game grid display"""
        grid_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Grid header
        header = tk.Frame(grid_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="🎮 Game World (10×10)", 
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
        # Canvas with modern styling
        canvas_frame = tk.Frame(grid_frame, bg=self.colors['bg_secondary'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, 
                               width=600, height=600,
                               bg=self.colors['bg_tertiary'],
                               highlightthickness=0,
                               relief='flat')
        self.canvas.pack(expand=True)
        
        self.cell_size = 55
        self.grid_offset = 25
    
    def setup_control_panel(self, parent):
        """Setup the modern control panel"""
        control_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Header
        header = tk.Frame(control_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=15, pady=(15, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Controls", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
        # Button container
        btn_frame = tk.Frame(control_frame, bg=self.colors['bg_secondary'])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Environment controls
        env_frame = tk.Frame(btn_frame, bg=self.colors['bg_secondary'])
        env_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(env_frame, text="Environment:", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary']).pack(anchor=tk.W)
        
        self.create_modern_button(env_frame, "🎲 Generate Random", self.generate_random_environment)
        self.create_modern_button(env_frame, "📁 Load Environment", self.load_environment)
        self.create_modern_button(env_frame, "💾 Save Environment", self.save_environment)
        self.create_modern_button(env_frame, "📋 Load Grid File", self.load_grid_file)
        
        # Separator
        sep = tk.Frame(btn_frame, bg=self.colors['grid_line'], height=1)
        sep.pack(fill=tk.X, pady=15)
        
        # Game controls
        game_frame = tk.Frame(btn_frame, bg=self.colors['bg_secondary'])
        game_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(game_frame, text="Game:", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary']).pack(anchor=tk.W)
        
        self.start_button = self.create_modern_button(game_frame, "▶️ Start Game", self.start_game, accent=True)
        self.step_button = self.create_modern_button(game_frame, "⏭️ Step", self.step_game, enabled=False)
        self.auto_button = self.create_modern_button(game_frame, "⏯️ Auto Play", self.toggle_auto_play, enabled=False)
        self.reset_button = self.create_modern_button(game_frame, "🔄 Reset", self.reset_game)
        
        # Speed control
        speed_frame = tk.Frame(btn_frame, bg=self.colors['bg_secondary'])
        speed_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(speed_frame, text="Speed (ms):", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT)
        
        self.speed_var = tk.StringVar(value="800")
        speed_entry = tk.Entry(speed_frame, textvariable=self.speed_var, 
                              bg=self.colors['bg_tertiary'],
                              fg=self.colors['text_primary'],
                              borderwidth=0,
                              width=8,
                              font=('Segoe UI', 9))
        speed_entry.pack(side=tk.RIGHT, padx=(5, 0))
    
    def create_modern_button(self, parent, text, command, accent=False, enabled=True):
        """Create a modern styled button"""
        bg_color = self.colors['accent'] if accent else self.colors['bg_tertiary']
        fg_color = self.colors['bg_primary'] if accent else self.colors['text_primary']
        
        btn = tk.Button(parent, text=text, command=command,
                       bg=bg_color, fg=fg_color,
                       borderwidth=0, relief='flat',
                       font=('Segoe UI', 9, 'bold'),
                       cursor='hand2' if enabled else 'arrow',
                       state='normal' if enabled else 'disabled',
                       pady=8)
        btn.pack(fill=tk.X, pady=2)
        
        # Hover effects
        if enabled:
            def on_enter(e):
                btn.config(bg=self.colors['accent_dark'] if accent else self.colors['accent'])
                if not accent:
                    btn.config(fg=self.colors['bg_primary'])
            
            def on_leave(e):
                btn.config(bg=bg_color, fg=fg_color)
            
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
        
        return btn
    
    def setup_status_panel(self, parent):
        """Setup the modern status panel"""
        status_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Header
        header = tk.Frame(status_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=15, pady=(15, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="📊 Agent Status", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
        # Status text with modern styling
        text_frame = tk.Frame(status_frame, bg=self.colors['bg_secondary'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.status_text = tk.Text(text_frame, height=10, 
                                  bg=self.colors['bg_tertiary'],
                                  fg=self.colors['text_primary'],
                                  borderwidth=0,
                                  relief='flat',
                                  wrap=tk.WORD,
                                  font=('Consolas', 9),
                                  selectbackground=self.colors['accent'])
        
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                               command=self.status_text.yview,
                               bg=self.colors['bg_tertiary'],
                               troughcolor=self.colors['bg_secondary'],
                               width=12)
        
        self.status_text.configure(yscrollcommand=scrollbar.set)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_knowledge_panel(self, parent):
        """Setup the modern knowledge base panel"""
        kb_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        kb_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Header
        header = tk.Frame(kb_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=15, pady=(15, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="🧠 Knowledge Base", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
        # Knowledge text with modern styling
        text_frame = tk.Frame(kb_frame, bg=self.colors['bg_secondary'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.kb_text = tk.Text(text_frame, 
                              bg=self.colors['bg_tertiary'],
                              fg=self.colors['text_primary'],
                              borderwidth=0,
                              relief='flat',
                              wrap=tk.WORD,
                              font=('Consolas', 9),
                              selectbackground=self.colors['accent'])
        
        kb_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                   command=self.kb_text.yview,
                                   bg=self.colors['bg_tertiary'],
                                   troughcolor=self.colors['bg_secondary'],
                                   width=12)
        
        self.kb_text.configure(yscrollcommand=kb_scrollbar.set)
        self.kb_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def draw_grid(self):
        """Draw the modern game grid with animations"""
        self.canvas.delete("all")
        
        # Draw grid background with subtle pattern
        for i in range(10):
            for j in range(10):
                x = self.grid_offset + i * self.cell_size
                y = self.grid_offset + j * self.cell_size
                
                # Alternating pattern
                if (i + j) % 2 == 0:
                    fill_color = self.colors['bg_tertiary']
                else:
                    fill_color = '#404040'
                
                self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                           fill=fill_color, outline='', width=0)
        
        # Draw grid lines
        for i in range(11):
            x = self.grid_offset + i * self.cell_size
            y = self.grid_offset + i * self.cell_size
            self.canvas.create_line(self.grid_offset, y, 
                                  self.grid_offset + 10 * self.cell_size, y, 
                                  fill=self.colors['grid_line'], width=1)
            self.canvas.create_line(x, self.grid_offset, 
                                  x, self.grid_offset + 10 * self.cell_size, 
                                  fill=self.colors['grid_line'], width=1)
        
        # Draw coordinate labels with modern styling
        for i in range(10):
            # X-axis labels
            x = self.grid_offset + i * self.cell_size + self.cell_size // 2
            y = self.grid_offset + 10 * self.cell_size + 18
            self.canvas.create_text(x, y, text=str(i), 
                                  font=('Segoe UI', 10, 'bold'),
                                  fill=self.colors['text_secondary'])
            
            # Y-axis labels
            x = self.grid_offset - 18
            y = self.grid_offset + (9 - i) * self.cell_size + self.cell_size // 2
            self.canvas.create_text(x, y, text=str(i), 
                                  font=('Segoe UI', 10, 'bold'),
                                  fill=self.colors['text_secondary'])
        
        # Draw environment elements with enhanced visuals
        self.draw_environment_elements()
        
        # Draw agent with animations
        self.draw_agent()
    
    def draw_environment_elements(self):
        """Draw environment elements with modern styling"""
        for x in range(10):
            for y in range(10):
                canvas_x = self.grid_offset + x * self.cell_size
                canvas_y = self.grid_offset + (9 - y) * self.cell_size
                
                # Draw visited cells
                if (x, y) in self.agent.kb.visited:
                    self.canvas.create_rectangle(canvas_x + 2, canvas_y + 2, 
                                               canvas_x + self.cell_size - 2, 
                                               canvas_y + self.cell_size - 2, 
                                               fill=self.colors['cell_visited'], 
                                               outline=self.colors['accent'], width=2)
                
                # Draw safe cells
                elif (x, y) in self.agent.kb.safe_cells:
                    self.canvas.create_rectangle(canvas_x + 2, canvas_y + 2, 
                                               canvas_x + self.cell_size - 2, 
                                               canvas_y + self.cell_size - 2, 
                                               fill=self.colors['cell_safe'], 
                                               outline=self.colors['success'], width=1)
                
                # Draw pits with depth effect
                if (x, y) in self.environment.pits:
                    # Shadow effect
                    self.canvas.create_oval(canvas_x + 5, canvas_y + 5, 
                                          canvas_x + self.cell_size - 5, 
                                          canvas_y + self.cell_size - 5, 
                                          fill='#000000', outline='')
                    # Main pit
                    self.canvas.create_oval(canvas_x + 8, canvas_y + 8, 
                                          canvas_x + self.cell_size - 8, 
                                          canvas_y + self.cell_size - 8, 
                                          fill=self.colors['pit_color'], 
                                          outline=self.colors['text_muted'], width=2)
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="⚫", font=('Segoe UI', 20))
                
                # Draw Wumpus with glow effect
                if (x, y) == self.environment.wumpus_pos and self.environment.wumpus_alive:
                    # Glow effect
                    glow_size = 4 + int(2 * math.sin(self.pulse_phase))
                    self.canvas.create_rectangle(canvas_x + 5 - glow_size, canvas_y + 5 - glow_size, 
                                               canvas_x + self.cell_size - 5 + glow_size, 
                                               canvas_y + self.cell_size - 5 + glow_size, 
                                               fill='#ff4444', outline='', stipple='gray25')
                    
                    # Wumpus body
                    self.canvas.create_rectangle(canvas_x + 8, canvas_y + 8, 
                                               canvas_x + self.cell_size - 8, 
                                               canvas_y + self.cell_size - 8, 
                                               fill=self.colors['wumpus_color'], 
                                               outline='#cc0000', width=2)
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="👹", font=('Segoe UI', 24))
                
                # Draw gold with sparkle effect
                if (x, y) == self.environment.gold_pos and not self.environment.agent_has_gold:
                    # Sparkle effect
                    sparkle_offset = int(3 * math.sin(self.pulse_phase * 2))
                    self.canvas.create_oval(canvas_x + 12 + sparkle_offset, 
                                          canvas_y + 12 + sparkle_offset,
                                          canvas_x + self.cell_size - 12 + sparkle_offset, 
                                          canvas_y + self.cell_size - 12 + sparkle_offset, 
                                          fill=self.colors['gold_color'], 
                                          outline='#cc9900', width=3)
                    
                    # Gold symbol
                    self.canvas.create_text(canvas_x + self.cell_size//2, 
                                          canvas_y + self.cell_size//2, 
                                          text="💰", font=('Segoe UI', 20))
                
                # Draw possible dangers with transparency effect
                if (x, y) in self.agent.kb.pit_possible:
                    self.canvas.create_text(canvas_x + self.cell_size//4, 
                                          canvas_y + self.cell_size//4, 
                                          text="P?", fill=self.colors['danger'], 
                                          font=('Segoe UI', 10, 'bold'))
                
                if (x, y) in self.agent.kb.wumpus_possible:
                    self.canvas.create_text(canvas_x + 3*self.cell_size//4, 
                                          canvas_y + self.cell_size//4, 
                                          text="W?", fill=self.colors['danger'], 
                                          font=('Segoe UI', 10, 'bold'))
    
    def draw_agent(self):
        """Draw agent with modern animations"""
        agent_x, agent_y = self.agent.position
        canvas_x = self.grid_offset + agent_x * self.cell_size
        canvas_y = self.grid_offset + (9 - agent_y) * self.cell_size
        
        center_x = canvas_x + self.cell_size // 2
        center_y = canvas_y + self.cell_size // 2
        
        if self.environment.agent_alive:
            # Animated glow effect
            glow_radius = 25 + int(5 * math.sin(self.pulse_phase))
            self.canvas.create_oval(center_x - glow_radius, center_y - glow_radius,
                                  center_x + glow_radius, center_y + glow_radius,
                                  fill=self.colors['agent_color'], outline='', stipple='gray25')
            
            # Agent body with scaling animation
            size = int(self.cell_size // 3 * self.agent_scale)
            
            # Direction vectors: North, East, South, West
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            dx, dy = directions[self.agent.direction]
            
            # Animated triangle
            points = [
                center_x + dx * size, center_y + dy * size,  # Tip
                center_x - dy * size//2 - dx * size//2, center_y + dx * size//2 - dy * size//2,  # Left
                center_x + dy * size//2 - dx * size//2, center_y - dx * size//2 - dy * size//2   # Right
            ]
            
            self.canvas.create_polygon(points, fill=self.colors['agent_color'], 
                                     outline='#0099cc', width=3, smooth=True)
            
            # Agent face
            self.canvas.create_text(center_x, center_y, text="🤖", 
                                  font=('Segoe UI', 16))
            
            # Show gold indicator
            if self.agent.has_gold:
                self.canvas.create_text(center_x, center_y + size + 12, 
                                      text="💰", font=('Segoe UI', 12))
                
            # Show arrow indicator
            if self.agent.has_arrow:
                self.canvas.create_text(center_x + size + 8, center_y - size - 8, 
                                      text="🏹", font=('Segoe UI', 10))
        else:
            # Dead agent with fade effect
            self.canvas.create_text(center_x, center_y, text="💀", 
                                  fill=self.colors['danger'], font=('Segoe UI', 24))
            self.canvas.create_text(center_x, center_y + 20, text="DEAD", 
                                  fill=self.colors['danger'], font=('Segoe UI', 8, 'bold'))
    
    def start_animations(self):
        """Start the animation loop"""
        self.animate()
    
    def animate(self):
        """Animation loop for visual effects"""
        self.pulse_phase += 0.1
        self.agent_scale = 1.0 + 0.1 * math.sin(self.pulse_phase)
        
        # Redraw grid to update animations
        self.draw_grid()
        
        # Schedule next frame
        self.animation_id = self.root.after(50, self.animate)
    
    def generate_random_environment(self):
        """Generate a new random environment"""
        self.environment.generate_random_environment()
        self.reset_game()
        self.update_status("🎲 New random environment generated!")
    
    def load_environment(self):
        """Load environment from JSON file"""
        filename = filedialog.askopenfilename(
            title="Load Environment",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                self.environment.size = data.get('size', 10)
                self.environment.pits = set(tuple(pit) for pit in data.get('pits', []))
                self.environment.wumpus_pos = tuple(data.get('wumpus_pos', (1, 1)))
                self.environment.gold_pos = tuple(data.get('gold_pos', (8, 8)))
                self.environment.wumpus_alive = data.get('wumpus_alive', True)
                self.environment.agent_has_gold = data.get('agent_has_gold', False)
                
                self.reset_game()
                self.update_status(f"📁 Environment loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load environment: {str(e)}")
    
    def save_environment(self):
        """Save current environment to JSON file"""
        filename = filedialog.asksaveasfilename(
            title="Save Environment",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                data = {
                    'size': self.environment.size,
                    'pits': list(self.environment.pits),
                    'wumpus_pos': list(self.environment.wumpus_pos),
                    'gold_pos': list(self.environment.gold_pos),
                    'wumpus_alive': self.environment.wumpus_alive,
                    'agent_has_gold': self.environment.agent_has_gold
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.update_status(f"💾 Environment saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save environment: {str(e)}")
    
    def load_grid_file(self):
        """Load environment from grid text file"""
        filename = filedialog.askopenfilename(
            title="Load Grid File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                # Parse grid
                grid = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip comments
                        row = [cell.strip() for cell in line.split()]
                        if row:
                            grid.append(row)
                
                if grid:
                    self.load_environment_from_grid(grid)
                    self.reset_game()
                    self.update_status(f"📋 Grid loaded from {filename}")
                else:
                    messagebox.showerror("Error", "No valid grid data found in file")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load grid file: {str(e)}")
    
    def start_game(self):
        """Start the game"""
        self.game_running = True
        self.start_button.config(state='disabled')
        self.step_button.config(state='normal')
        self.auto_button.config(state='normal')
        self.update_status("🎮 Game started! Agent is exploring...")
        self.update_knowledge_base()
    
    def step_game(self):
        """Execute one step of the game"""
        if not self.game_running:
            return
        
        if self.environment.agent_alive:
            # Get percepts
            percepts = self.environment.get_percepts()
            
            # Agent processes percepts and decides action
            action = self.agent.get_action(percepts)
            
            # Execute action
            result = self.environment.execute_action(action)
            
            # Update agent state
            self.agent.update_state(action, result)
            
            # Update display
            self.draw_grid()
            self.update_status(f"🎯 Action: {action} | Result: {result}")
            self.update_knowledge_base()
            
            # Check game end conditions
            if not self.environment.agent_alive:
                self.game_over("💀 Agent died!")
            elif self.environment.agent_has_gold and self.agent.position == (0, 0):
                self.game_over("🏆 Victory! Agent escaped with gold!")
            elif self.agent.is_stuck():
                self.game_over("🤔 Agent is stuck - no safe moves available!")
        else:
            self.game_over("💀 Agent is dead!")
    
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        self.auto_play = not self.auto_play
        
        if self.auto_play:
            self.auto_button.config(text="⏸️ Pause")
            self.step_button.config(state='disabled')
            self.auto_step()
        else:
            self.auto_button.config(text="⏯️ Auto Play")
            self.step_button.config(state='normal')
            if hasattr(self, 'auto_step_id'):
                self.root.after_cancel(self.auto_step_id)
    
    def auto_step(self):
        """Auto-play step with delay"""
        if self.auto_play and self.game_running:
            self.step_game()
            try:
                delay = max(100, int(self.speed_var.get()))
            except ValueError:
                delay = 800
            self.auto_step_id = self.root.after(delay, self.auto_step)
    
    def reset_game(self):
       def reset_game(self):
        """Reset the game to initial state"""
        self.game_running = False
        self.auto_play = False
        
        # Reset environment
        self.environment.agent_alive = True
        self.environment.agent_has_gold = False
        self.environment.wumpus_alive = True
        
        # Reset agent directly
        self.agent.position = (0, 0)
        self.agent.direction = 0
        self.agent.has_arrow = True
        self.agent.has_gold = False
        
        # Reset UI
        self.start_button.config(state='normal')
        self.step_button.config(state='disabled')
        self.auto_button.config(state='disabled', text="⏯️ Auto Play")
        
        # Update display
        self.draw_grid()
        self.update_status("🔄 Game reset. Ready to start!")
        self.update_knowledge_base()
    def game_over(self, message):
        """Handle game over"""
        self.game_running = False
        self.auto_play = False
        
        self.start_button.config(state='disabled')
        self.step_button.config(state='disabled')
        self.auto_button.config(state='disabled')
        
        self.update_status(f"🎮 GAME OVER: {message}")
        
        # Show game over dialog
        result = messagebox.askyesno("Game Over", f"{message}\n\nWould you like to play again?")
        if result:
            self.reset_game()
    
    def update_status(self, message):
        """Update status display"""
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
    
    def update_knowledge_base(self):
        """Update knowledge base display"""
        self.kb_text.config(state='normal')
        self.kb_text.delete(1.0, tk.END)
        
        # Agent info
        self.kb_text.insert(tk.END, f"🤖 AGENT STATUS\n")
        self.kb_text.insert(tk.END, f"Position: {self.agent.position}\n")
        self.kb_text.insert(tk.END, f"Direction: {['North', 'East', 'South', 'West'][self.agent.direction]}\n")
        self.kb_text.insert(tk.END, f"Has Gold: {self.agent.has_gold}\n")
        self.kb_text.insert(tk.END, f"Has Arrow: {self.agent.has_arrow}\n")
        self.kb_text.insert(tk.END, f"Alive: {self.environment.agent_alive}\n\n")
        
        # Knowledge base info
        self.kb_text.insert(tk.END, f"🧠 KNOWLEDGE BASE\n")
        self.kb_text.insert(tk.END, f"Visited: {len(self.agent.kb.visited)} cells\n")
        self.kb_text.insert(tk.END, f"Safe: {len(self.agent.kb.safe_cells)} cells\n")
        self.kb_text.insert(tk.END, f"Possible Pits: {len(self.agent.kb.pit_possible)}\n")
        self.kb_text.insert(tk.END, f"Possible Wumpus: {len(self.agent.kb.wumpus_possible)}\n\n")
        
        # Environment info
        self.kb_text.insert(tk.END, f"🏺 ENVIRONMENT\n")
        self.kb_text.insert(tk.END, f"Wumpus: {self.environment.wumpus_pos} ({'Alive' if self.environment.wumpus_alive else 'Dead'})\n")
        self.kb_text.insert(tk.END, f"Gold: {self.environment.gold_pos} ({'Available' if not self.environment.agent_has_gold else 'Collected'})\n")
        self.kb_text.insert(tk.END, f"Pits: {len(self.environment.pits)} locations\n")
        
        # Current percepts
        if self.game_running:
            percepts = self.environment.get_percepts()
            self.kb_text.insert(tk.END, f"\n📡 CURRENT PERCEPTS\n")
            for percept in percepts:
                self.kb_text.insert(tk.END, f"• {percept}\n")
        
        self.kb_text.config(state='disabled')
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
        
        # Cleanup animations
        if self.animation_id:
            self.root.after_cancel(self.animation_id)


    
