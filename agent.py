import random
from typing import Set, Tuple, List, Optional
from collections import deque
from knowledge_base import KnowledgeBase

class WumpusAgent:
    """Intelligent Wumpus World Agent"""
    
    def __init__(self, size=10):
        self.size = size
        self.position = (0, 0)
        self.direction = 0  # 0=North, 1=East, 2=South, 3=West
        self.has_arrow = True
        self.has_gold = False
        self.kb = KnowledgeBase(size)
        self.plan = deque()
        self.returning_home = False
        
        # Initialize starting position as safe
        self.kb.add_visit((0, 0))
    
    def get_action(self, percepts: List[str]) -> str:
        """Get the next action based on current percepts"""
        # Update knowledge base
        self.kb.add_percept(self.position, percepts)
        
        # Check for gold
        if "Glitter" in percepts and not self.has_gold:
            return "Grab"
        
        # Check for scream (wumpus killed)
        if "Scream" in percepts:
            self.kb.wumpus_killed()
        
        # If we have gold and are at start, climb out
        if self.has_gold and self.position == (0, 0):
            return "Climb"
        
        # If we have gold, return home
        if self.has_gold and not self.returning_home:
            self.returning_home = True
            self.plan.clear()
            path = self._find_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))
        
        # Execute planned actions
        if self.plan:
            return self.plan.popleft()
        
        # Strategic decision making
        return self._choose_action(percepts)
    
    def _choose_action(self, percepts: List[str]) -> str:
        """Choose the best action based on current situation"""
        # Get possible moves
        safe_moves = self._get_safe_moves()
        
        # Priority 1: Explore safe unvisited cells
        safe_unvisited = self.kb.get_safe_unvisited_cells()
        if safe_unvisited:
            # Find closest safe unvisited cell
            closest = min(safe_unvisited, key=lambda pos: self._manhattan_distance(self.position, pos))
            path = self._find_path_to_position(closest)
            if path:
                actions = self._path_to_actions(path)
                self.plan.extend(actions)
                return self.plan.popleft()
        
        # Priority 2: Try to shoot wumpus if we can infer its location
        if self.has_arrow and self.kb.wumpus_alive:
            shoot_action = self._try_shoot_wumpus(percepts)
            if shoot_action:
                return shoot_action
        
        # Priority 3: Take calculated risks
        if not safe_moves and not self.returning_home:
            risky_moves = self._get_risky_moves()
            if risky_moves:
                # Choose least risky move
                best_move = min(risky_moves, key=lambda pos: self._calculate_risk(pos))
                actions = self._get_actions_to_adjacent(best_move)
                if actions:
                    self.plan.extend(actions)
                    return self.plan.popleft()
        
        # Priority 4: Move to safe adjacent cell
        if safe_moves:
            # Prefer unvisited safe cells
            unvisited_safe = [pos for pos in safe_moves if pos not in self.kb.visited]
            if unvisited_safe:
                target = random.choice(unvisited_safe)
            else:
                target = random.choice(safe_moves)
            
            actions = self._get_actions_to_adjacent(target)
            if actions:
                self.plan.extend(actions)
                return self.plan.popleft()
        
        # Priority 5: Return home if stuck
        if not self.returning_home:
            self.returning_home = True
            path = self._find_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))
                return self.plan.popleft()
        
        # Last resort: random safe move or turn
        if safe_moves:
            target = random.choice(safe_moves)
            actions = self._get_actions_to_adjacent(target)
            if actions:
                return actions[0]
        
        return random.choice(["TurnLeft", "TurnRight"])
    
    def _get_safe_moves(self) -> List[Tuple[int, int]]:
        """Get safe adjacent positions"""
        safe_moves = []
        x, y = self.position
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.size and 0 <= ny < self.size and
                self.kb.is_safe((nx, ny))):
                safe_moves.append((nx, ny))
        
        return safe_moves
    
    def _get_risky_moves(self) -> List[Tuple[int, int]]:
        """Get risky but possible adjacent positions"""
        risky_moves = []
        x, y = self.position
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.size and 0 <= ny < self.size and
                not self.kb.is_safe((nx, ny)) and
                not self.kb.is_dangerous((nx, ny))):
                risky_moves.append((nx, ny))
        
        return risky_moves
    
    def _calculate_risk(self, pos: Tuple[int, int]) -> float:
        """Calculate risk score for a position"""
        risk = 0.0
        
        if pos in self.kb.pit_possible:
            risk += 0.5
        
        if pos in self.kb.wumpus_possible and self.kb.wumpus_alive:
            risk += 0.7
        
        return risk
    
    def _try_shoot_wumpus(self, percepts: List[str]) -> Optional[str]:
        """Try to shoot wumpus if we can infer its location"""
        if not self.has_arrow or not self.kb.wumpus_alive:
            return None
        
        # If we sense stench, wumpus is adjacent
        if "Stench" in percepts:
            # Try to determine wumpus location
            wumpus_candidates = []
            x, y = self.position
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.size and 0 <= ny < self.size and
                    (nx, ny) in self.kb.wumpus_possible):
                    wumpus_candidates.append((nx, ny))
            
            # If only one candidate, shoot in that direction
            if len(wumpus_candidates) == 1:
                target = wumpus_candidates[0]
                required_direction = self._get_direction_to_position(target)
                
                if required_direction == self.direction:
                    return "Shoot"
                else:
                    # Turn to face wumpus
                    turn_action = self._get_turn_action(required_direction)
                    self.plan.appendleft("Shoot")  # Shoot after turning
                    return turn_action
        
        return None
    
    def _find_path_to_start(self) -> List[Tuple[int, int]]:
        """Find path back to starting position using A*"""
        return self._find_path_to_position((0, 0))
    
    def _find_path_to_position(self, target: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find path to target position using A* algorithm"""
        if self.position == target:
            return []
        
        # A* pathfinding
        from heapq import heappush, heappop
        
        open_set = [(0, self.position)]
        came_from = {}
        g_score = {self.position: 0}
        f_score = {self.position: self._manhattan_distance(self.position, target)}
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == target:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))
            
            x, y = current
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (x + dx, y + dy)
                
                if (not (0 <= neighbor[0] < self.size and 0 <= neighbor[1] < self.size) or
                    not self.kb.is_safe(neighbor)):
                    continue
                
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._manhattan_distance(neighbor, target)
                    heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found
    
    def _path_to_actions(self, path: List[Tuple[int, int]]) -> List[str]:
        """Convert path to sequence of actions"""
        if not path:
            return []
        
        actions = []
        current_pos = self.position
        current_dir = self.direction
        
        for next_pos in path:
            # Calculate required direction
            required_dir = self._get_direction_to_position(next_pos, current_pos)
            
            # Turn to face the direction
            while current_dir != required_dir:
                if self._get_turn_direction(current_dir, required_dir) == "left":
                    actions.append("TurnLeft")
                    current_dir = (current_dir - 1) % 4
                else:
                    actions.append("TurnRight")
                    current_dir = (current_dir + 1) % 4
            
            # Move forward
            actions.append("Forward")
            current_pos = next_pos
        
        return actions
    
    def _get_actions_to_adjacent(self, target: Tuple[int, int]) -> List[str]:
        """Get actions to move to adjacent position"""
        required_dir = self._get_direction_to_position(target)
        actions = []
        
        # Turn to face target
        current_dir = self.direction
        while current_dir != required_dir:
            if self._get_turn_direction(current_dir, required_dir) == "left":
                actions.append("TurnLeft")
                current_dir = (current_dir - 1) % 4
            else:
                actions.append("TurnRight")
                current_dir = (current_dir + 1) % 4
        
        # Move forward
        actions.append("Forward")
        return actions
    
    def _get_direction_to_position(self, target: Tuple[int, int], from_pos: Tuple[int, int] = None) -> int:
        """Get direction to face target position"""
        if from_pos is None:
            from_pos = self.position
        
        fx, fy = from_pos
        tx, ty = target
        
        if tx > fx:
            return 1  # East
        elif tx < fx:
            return 3  # West
        elif ty > fy:
            return 0  # North
        else:
            return 2  # South
    
    def _get_turn_direction(self, current_dir: int, target_dir: int) -> str:
        """Get optimal turn direction"""
        diff = (target_dir - current_dir) % 4
        return "left" if diff == 3 else "right"
    
    def _get_turn_action(self, target_dir: int) -> str:
        """Get turn action to face target direction"""
        return "TurnLeft" if self._get_turn_direction(self.direction, target_dir) == "left" else "TurnRight"
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def update_state(self, action: str, result: str):
        """Update agent state after action execution"""
        if action == "Forward" and "Moved forward" in result:
            # Update position
            x, y = self.position
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            dx, dy = directions[self.direction]
            self.position = (x + dx, y + dy)
            
            # Mark new position as visited
            self.kb.add_visit(self.position)
            
        elif action == "TurnLeft":
            self.direction = (self.direction - 1) % 4
            
        elif action == "TurnRight":
            self.direction = (self.direction + 1) % 4
            
        elif action == "Grab" and "Grabbed gold" in result:
            self.has_gold = True
            
        elif action == "Shoot":
            self.has_arrow = False
            if "Wumpus died" in result:
                self.kb.wumpus_killed()
    
    def is_stuck(self) -> bool:
        """Check if agent is stuck with no safe moves"""
        safe_moves = self._get_safe_moves()
        risky_moves = self._get_risky_moves()
        
        # If we have gold and can't get home, we're stuck
        if self.has_gold and self.position != (0, 0):
            path_home = self._find_path_to_start()
            if not path_home:
                return True
        
        # If no safe moves and no reasonable risky moves
        if not safe_moves and not risky_moves:
            return True
        
        # If we've visited all safe cells and have no new options
        safe_unvisited = self.kb.get_safe_unvisited_cells()
        if not safe_unvisited and not risky_moves:
            return True
        
        return False