import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
import random
from environment import WumpusEnvironment
from agent import WumpusAgent
from collections import deque
from knowledge_base import KnowledgeBase

class ModernWumpusWorldGUI:
    def __init__(self, grid=None):
        self.root = tk.Tk()
        self.root.title("🏺 Wumpus World - AI Agent Navigation")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        self.initial_grid = grid
        

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
        
        self.agent_scale = 1.0
        self.agent_rotation = 0.0
        self.pulse_phase = 0.0
        
        if grid:
            self.load_environment_from_grid(grid)
        else:
            self.environment.generate_random_environment()
        
        self.setup_styles()
        self.setup_ui()
        self.reset_game()
        self.start_animations()
    
    def setup_styles(self):
        style = ttk.Style()
        
        style.theme_use('clam')
        style.configure('Modern.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['accent_dark'])])
        

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
     self.environment.size = len(grid)
     self.environment.pits.clear()
    
     self.environment.wumpus_positions.clear()
     self.environment.wumpus_alive.clear()
      
     for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            world_y = len(grid) - 1 - y
            
            if cell == 'P':
                self.environment.pits.add((x, world_y))
            elif cell == 'W':
                self.environment.wumpus_positions.add((x, world_y))
                self.environment.wumpus_alive.add((x, world_y))
            elif cell == 'G':
                self.environment.gold_pos = (x, world_y)
    
     self.agent.kb.num_wumpuses = len(self.environment.wumpus_positions)
     
     if not self.environment.gold_pos:
        while True:
            pos = (random.randint(0, self.environment.size-1), 
                   random.randint(0, self.environment.size-1))
            if (pos != (0, 0) and 
                pos not in self.environment.pits and 
                pos not in self.environment.wumpus_positions):
                self.environment.gold_pos = pos
                break
    
     print("Loaded Grid:")
     for row in grid:
        print(' '.join(cell if cell in ['P', 'W', 'G'] else '.' for cell in row))

     print("Wumpus positions:", sorted(list(self.environment.wumpus_positions)))
     print("Wumpus definite:", sorted(list(self.agent.kb.wumpus_definite)))
     print("Wumpus possible:", sorted(list(self.agent.kb.wumpus_possible)))
     print("pit possible:", sorted(list(self.agent.kb.pit_possible)))
     print("pit definitr:", sorted(list(self.agent.kb.pit_definite)))
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
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
        
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        right_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'], width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        self.setup_game_grid(left_frame)
        self.setup_control_panel(right_frame)
        self.setup_status_panel(right_frame)
        self.setup_knowledge_panel(right_frame)
    
    def setup_game_grid(self, parent):
        grid_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = tk.Frame(grid_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=10, pady=(10, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="🎮 Game World (10×10)", 
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
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
        control_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        header = tk.Frame(control_frame, bg=self.colors['bg_secondary'], height=40)
        header.pack(fill=tk.X, padx=15, pady=(15, 0))
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Controls", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, pady=10)
        
        btn_frame = tk.Frame(control_frame, bg=self.colors['bg_secondary'])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
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
        
        sep = tk.Frame(btn_frame, bg=self.colors['grid_line'], height=1)
        sep.pack(fill=tk.X, pady=15)
        
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
                
                # Draw Wumpuses (living and dead)
                if (x, y) in self.environment.wumpus_positions:
                    if (x, y) in self.environment.wumpus_alive:
                        # Living wumpus - glow effect
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
                    else:
                        # Dead wumpus
                        self.canvas.create_rectangle(canvas_x + 8, canvas_y + 8, 
                                                   canvas_x + self.cell_size - 8, 
                                                   canvas_y + self.cell_size - 8, 
                                                   fill='#666666', 
                                                   outline='#333333', width=2)
                        self.canvas.create_text(canvas_x + self.cell_size//2, 
                                              canvas_y + self.cell_size//2, 
                                              text="💀", font=('Segoe UI', 24))
                
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
                    self.canvas.create_text(canvas_x + self.cell_size//4, 
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
            self.canvas.create_oval(center_x - size, center_y - size,
                                  center_x + size, center_y + size,
                                  fill=self.colors['agent_color'], 
                                  outline='#ffffff', width=3)
            
            # Agent direction indicator
            direction_map = {
                'up': (0, -1),
                'down': (0, 1),
                'left': (-1, 0),
                'right': (1, 0)
            }
            
            if self.agent.direction in direction_map:
                dx, dy = direction_map[self.agent.direction]
                arrow_x = center_x + dx * size // 2
                arrow_y = center_y + dy * size // 2
                self.canvas.create_oval(arrow_x - 4, arrow_y - 4,
                                      arrow_x + 4, arrow_y + 4,
                                      fill='#ffffff', outline='')
            
            # Agent emoji
            self.canvas.create_text(center_x, center_y, text="🤖", 
                                  font=('Segoe UI', int(20 * self.agent_scale)))
            
            # Status indicators
            if self.environment.agent_has_gold:
                self.canvas.create_text(center_x, center_y - 30, text="💰", 
                                      font=('Segoe UI', 16))
            
            if self.agent.has_arrow:
                self.canvas.create_text(center_x + 25, center_y - 25, text="🏹", 
                                      font=('Segoe UI', 12))
        else:
            # Dead agent
            self.canvas.create_oval(center_x - 15, center_y - 15,
                                  center_x + 15, center_y + 15,
                                  fill='#666666', outline='#333333', width=2)
            self.canvas.create_text(center_x, center_y, text="💀", 
                                  font=('Segoe UI', 20))
    
    def start_animations(self):
        """Start the animation loop"""
        self.animate()
    
    def animate(self):
        """Animation loop for visual effects"""
        # Update animation variables
        self.pulse_phase += 0.1
        self.agent_scale = 1.0 + 0.1 * math.sin(self.pulse_phase * 2)
        
        # Redraw grid if game is running
        if self.game_running or True:  # Always animate for visual appeal
            self.draw_grid()
        
        # Schedule next animation frame
        self.animation_id = self.root.after(50, self.animate)
    
    def generate_random_environment(self):
        """Generate a new random environment"""
        self.environment.generate_random_environment()
        self.reset_game()
        self.update_status("🎲 New random environment generated!")
    
    def load_environment(self):
        """Load environment from JSON file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Environment",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.environment.load_from_dict(data)
                self.reset_game()
                self.update_status(f"📁 Environment loaded from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load environment: {str(e)}")
    
    def save_environment(self):
        """Save current environment to JSON file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Environment",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                data = self.environment.to_dict()
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                self.update_status(f"💾 Environment saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save environment: {str(e)}")
    
    def load_grid_file(self):
        """Load environment from grid text file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Grid File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                
                # Parse grid content
                lines = content.split('\n')
                grid = []
                for line in lines:
                    if line.strip():
                        # Handle both space-separated and character-by-character formats
                        if ' ' in line:
                            row = line.split()
                        else:
                            row = list(line.strip())
                        grid.append(row)
                
                if grid:
                    self.load_environment_from_grid(grid)
                    self.reset_game()
                    self.update_status(f"📋 Grid loaded from {file_path}")
                else:
                    messagebox.showerror("Error", "No valid grid data found in file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load grid file: {str(e)}")
     
    def start_game(self):
        """Start the game"""
        self.game_running = True
        self.auto_play = False
        
        # Update button states
        self.start_button.config(state='disabled')
        self.step_button.config(state='normal')
        self.auto_button.config(state='normal')
        
        self.update_status("🎮 Game started! Agent is ready to explore.")
        self.update_knowledge_display()
        self.draw_grid()
    def step_game(self):
     """Execute one game step with multiple Wumpus handling"""
     if not self.game_running:
        return
    
     # Check if game is over before taking action
     if self.is_game_over():
        self.end_game()
        return
    
     # Get current perceptions
     percepts = self.environment.get_percepts()
    
     # Agent decides and acts
     action = self.agent.get_action(percepts)
    
     if action:
        self.update_status(f"🎯 Agent action: {action}")
        
        # Execute action in environment and get result
        result = self.environment.execute_action(action)
        self.update_status(f"   → Result: {result}")
        
        # Update agent's state based on action and result
        self.agent.update_state(action, result)
        print("\nAfter step:")
        print("percepts:",percepts)
        print("Wumpus definite:", sorted(list(self.agent.kb.wumpus_definite)))
        print("Wumpus possible:", sorted(list(self.agent.kb.wumpus_possible)))
        print("Pit definite:", sorted(list(self.agent.kb.pit_definite)))
        print("Pit possible:", sorted(list(self.agent.kb.pit_possible)))
        
        # Special handling for gold grab
        if action == "Grab" and "Grabbed gold" in result:
            self.environment.agent_has_gold = True
        
        # Special handling for climb action with gold
        if action == "Climb" and self.environment.agent_has_gold and self.agent.position == (0, 0):
            self.update_status("🎉 Agent successfully climbed out with the gold!")
            self.end_game(victory=True)
            return
        
        # Update displays
        self.update_knowledge_display()
        self.draw_grid()
        
        # Check for game over conditions after action
        game_over_status = self.check_game_status()
        if game_over_status:
            if game_over_status == "victory":
                self.end_game(victory=True)
            else:
                self.end_game(victory=False)
            return
     else:
        self.update_status("🤔 Agent has no valid actions")
    
     # Continue auto-play if enabled
     if self.auto_play and self.game_running:
        try:
            delay = int(self.speed_var.get())
        except ValueError:
            delay = 800
        self.root.after(delay, self.step_game)
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        self.auto_play = not self.auto_play
        
        if self.auto_play:
            self.auto_button.config(text="⏸️ Pause")
            self.step_button.config(state='disabled')
            self.update_status("⏯️ Auto-play enabled")
            # Start auto-play
            try:
                delay = int(self.speed_var.get())
            except ValueError:
                delay = 800
            self.root.after(delay, self.step_game)
        else:
            self.auto_button.config(text="⏯️ Auto Play")
            self.step_button.config(state='normal')
            self.update_status("⏸️ Auto-play paused")
    
    def reset_game(self):
        """Reset the game to initial state with multiple Wumpus support"""
        self.game_running = False
        self.auto_play = False
        
        # Reset agent
        self.agent = WumpusAgent(self.environment.size)
        
        # Reset environment state
        self.environment.agent_pos = (0, 0)
        self.environment.agent_direction = 0
        self.environment.agent_alive = True
        self.environment.agent_has_gold = False
        self.environment.agent_has_arrow = True
        
        # Reset all Wumpuses to alive state
        self.environment.wumpus_alive = self.environment.wumpus_positions.copy()
        
        # Reset button states
        self.start_button.config(state='normal')
        self.step_button.config(state='disabled')
        self.auto_button.config(state='disabled', text="⏯️ Auto Play")
        
        # Update displays
        self.update_status("🔄 Game reset. Ready to start!")
        self.update_knowledge_display()
        self.draw_grid()

    def check_game_status(self):
     """Check game status and return 'victory', 'defeat', or None"""
     # Agent died
     if not self.environment.agent_alive:
        return "defeat"
    
     # Agent won (climbed out with gold)
     if (self.environment.agent_has_gold and 
        self.agent.position == (0, 0)):
        return "victory"
    
     return None
    def is_game_over(self):
     """Check if the game is over"""
     return self.check_game_status() is not None
    
    def end_game(self, victory=False):
        """End the game"""
        self.game_running = False
        self.auto_play = False
        
        # Update button states
        self.start_button.config(state='normal')
        self.step_button.config(state='disabled')
        self.auto_button.config(state='disabled', text="⏯️ Auto Play")
        
        if victory:
            self.update_status("🎉 VICTORY! Agent successfully retrieved the gold!")
            messagebox.showinfo("Victory!", "🎉 Congratulations! The agent has successfully completed the mission!")
        else:
            self.update_status("💀 GAME OVER! Agent died.")
            messagebox.showinfo("Game Over", "💀 The agent has died. Better luck next time!")
        
        self.draw_grid()
    
    def update_status(self, message):
        """Update the status display"""
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + '\n')
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
    
    
    def update_knowledge_display(self):
        """Update the knowledge base display with multiple Wumpus info"""
        kb_info = []
        
        # Current position and direction
        kb_info.append(f"🤖 Position: {self.agent.position}")
        kb_info.append(f"🧭 Direction: {self.agent.direction}")
        kb_info.append(f"🏹 Has Arrow: {self.agent.has_arrow}")
        kb_info.append(f"💰 Has Gold: {self.environment.agent_has_gold}")
        kb_info.append(f"👹 Wumpuses Alive: {len(self.environment.wumpus_alive)}/{len(self.environment.wumpus_positions)}")
        kb_info.append("")
        
        # Visited cells
        kb_info.append(f"👣 Visited: {len(self.agent.kb.visited)} cells")
        visited_str = ", ".join([f"({x},{y})" for x, y in sorted(self.agent.kb.visited)])
        kb_info.append(f"   {visited_str}")
        kb_info.append("")
        
        # Safe cells
        kb_info.append(f"✅ Safe: {len(self.agent.kb.safe_cells)} cells")
        safe_str = ", ".join([f"({x},{y})" for x, y in sorted(self.agent.kb.safe_cells)])
        kb_info.append(f"   {safe_str}")
        kb_info.append("")
        
        # Possible dangers
        if self.agent.kb.pit_possible:
            kb_info.append(f"⚠️ Possible Pits: {len(self.agent.kb.pit_possible)}")
            pit_str = ", ".join([f"({x},{y})" for x, y in sorted(self.agent.kb.pit_possible)])
            kb_info.append(f"   {pit_str}")
        
        if self.agent.kb.wumpus_possible:
            kb_info.append(f"👹 Possible Wumpus Locations: {len(self.agent.kb.wumpus_possible)}")
            wumpus_str = ", ".join([f"({x},{y})" for x, y in sorted(self.agent.kb.wumpus_possible)])
            kb_info.append(f"   {wumpus_str}")
        
        # Current perceptions
        if self.game_running:
            perceptions = self.environment.get_percepts()
            kb_info.append("")
            kb_info.append("🔍 Current Perceptions:")
            for perception in perceptions:
                kb_info.append(f"   • {perception}")
        
        # Update display
        self.kb_text.config(state='normal')
        self.kb_text.delete(1.0, tk.END)
        self.kb_text.insert(tk.END, '\n'.join(kb_info))
        self.kb_text.config(state='disabled')

    
    def run(self):
        """Start the GUI main loop"""
        self.draw_grid()
        self.update_knowledge_display()
        self.root.mainloop()
    
    def __del__(self):
        """Clean up animations when object is destroyed"""
        if hasattr(self, 'animation_id') and self.animation_id:
            self.root.after_cancel(self.animation_id)


