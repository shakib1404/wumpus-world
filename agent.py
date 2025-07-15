import random
from typing import Set, Tuple, List, Optional, Dict
from collections import deque
from heapq import heappush, heappop
from knowledge_base import KnowledgeBase
from Action import ActionSelector, Action  # Import the ActionSelector and Action classes

class WumpusAgent:
    def __init__(self, size=10):
        self.size = size
        self.reset()

    def reset(self):
        self.position = (0, 0)
        self.direction = 0  # 0=North, 1=East, 2=South, 3=West
        self.has_arrow = True
        self.has_gold = False
        self.kb = KnowledgeBase(self.size)
        self.plan = deque()
        self.returning_home = False
        self.score = 0
        self.move_count = 0
        self.shot_attempted = False
        self.last_stench_positions = set()
        self.consecutive_stench = 0
        self.danger_threshold = 0.1  # Much more conservative threshold
        self.last_safe_position = (0, 0)  # Track last known safe position
        
        # Initialize the ActionSelector
        self.action_selector = ActionSelector(
            epsilon=0.1,
            curiosity_weight=0.3,
            decay_rate=0.995
        )

    def get_action(self, percepts: List[str]) -> str:
        
        self.kb.add_percept(self.position, percepts)
        self.move_count += 1

        # Update stench tracking
        if "Stench" in percepts:
            self.last_stench_positions.add(self.position)
            self.consecutive_stench += 1
        else:
            self.consecutive_stench = 0

        # Handle gold pickup
        if "Glitter" in percepts and not self.has_gold:
            return "Grab"

        # Handle wumpus death
        if "Scream" in percepts:
            self.kb.wumpus_killed()
            self.score += 100
            self.shot_attempted = False
            self.last_stench_positions = set()
            self.consecutive_stench = 0

        # Handle reaching home with gold
        if self.has_gold and self.position == (0, 0):
            return "Climb"

        # Start returning home when we have gold
        if self.has_gold and not self.returning_home:
            self.returning_home = True
            self.plan.clear()
            path = self._find_safe_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))

        # Execute planned actions if available
        if self.plan:
            next_action = self.plan.popleft()
            # Double-check that planned move is still safe
            if next_action == "Forward":
                next_pos = self._get_next_position()
                if not self._is_definitely_safe(next_pos):
                    self.plan.clear()  # Clear unsafe plan
                    return self._choose_action_with_selector(percepts)
            return next_action

        return self._choose_action_with_selector(percepts)
    def _choose_action_with_selector(self, percepts: List[str]) -> str:
     """Use ActionSelector to choose the best action"""
     
    
     # Get available actions from ActionSelector
     available_actions = self.action_selector.get_available_actions(
        self.position, 
        self.size, 
        self.has_arrow
     )
    
     # First try to filter only safe actions
     safe_actions = self._filter_safe_actions(available_actions, percepts)

     if self.kb.safe_cells==self.kb.visited:
        print("No safe actions available, considering risky moves")
        risky_action = self._choose_risky_move(available_actions, percepts)
        if risky_action:
            return risky_action
    
     if safe_actions:
        # Use ActionSelector to pick the best safe action
        selected_action = self.action_selector.select_action(
            self.position,
            self.kb,
            safe_actions,
            self.has_arrow
        )
        return self._convert_action_to_command(selected_action)
     # If no safe actions, check if we should make a risky move
     
     # If no safe actions, check if we should make a risky move
     if self._should_make_risky_move():
        print("No safe actions available, considering risky moves")
        risky_action = self._choose_risky_move(available_actions, percepts)
        if risky_action:
            return risky_action
    
     # Emergency fallback if no safe or risky moves available
     return self._emergency_action(percepts)
    
    def _should_make_risky_move(self) -> bool:
     """Determine if we should consider making a risky move"""
     # Only consider risky moves if we've explored all definitely safe cells
     safe_unvisited = self._get_definitely_safe_unvisited()
     return len(safe_unvisited) == 0

    def _choose_risky_move(self, available_actions: List[Action], percepts: List[str]) -> Optional[str]:
     """Choose the least risky move when no safe options are available"""
     risky_moves = []
     print(available_actions)
    
     for action in available_actions:
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:  # Out of bounds
                continue
                
            if target_pos not in self.kb.visited:
                # Calculate risk score (lower is better)
                pit_prob = self.kb.get_pit_probability(target_pos)
                wumpus_prob = self.kb.get_wumpus_probability(target_pos)
                risk_score = pit_prob * 1000 + wumpus_prob * 1000
                
                # Add small bonus for potentially revealing new information
                info_bonus = self._calculate_information_gain(target_pos)
                risk_score -= info_bonus
                
                risky_moves.append((risk_score, action, target_pos))
     print(risky_moves)
     if not risky_moves:
        return None
        
     # Sort by risk score (lowest first)
     risky_moves.sort(key=lambda x: x[0])
     print("sorted moves",risky_moves)
    
     # Choose the least risky move
     best_score, best_action, best_pos = risky_moves[0]
    
     # Only proceed if the risk is below our threshold
     if best_score <=940:  # Adjust threshold as needed
        return self._convert_action_to_command(best_action)
    
     return None
 
    def _calculate_information_gain(self, pos: Tuple[int, int]) -> float:
     """Calculate how much information we might gain by visiting this position"""
     if pos in self.kb.visited:
        return 0.0
        
     info_gain = 0.0
    
     # Check adjacent cells for possible dangers this could resolve
     for adj in self._get_adjacent(pos):
        if adj in self.kb.pit_possible or adj in self.kb.wumpus_possible:
            info_gain += 50.0
        
            
     # Bonus if this position is adjacent to multiple unknown cells
     unknown_adjacent = sum(1 for adj in self._get_adjacent(pos) 
                          if adj not in self.kb.visited)
     info_gain += unknown_adjacent * 20.0 
    
     return info_gain
 
    def _filter_safe_actions(self, actions: List[Action], percepts: List[str]) -> List[Action]:
     """Filter actions to only include safe ones"""
     safe_actions = []
     for action in actions:
        if action in [Action.GRAB, Action.CLIMB]:
            safe_actions.append(action)
            continue
            
        if action.value.startswith("shoot_"):
            if self.has_arrow:
                safe_actions.append(action)
            continue
            
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:  # Out of bounds
                continue
                
            # Only allow moves to definitely safe positions
            if self._is_definitely_safe(target_pos):
                safe_actions.append(action)
    
     return safe_actions
    def _is_action_safe(self, action: Action, percepts: List[str]) -> bool:
        """Check if an action is safe to perform"""
        
        # GRAB and CLIMB are always safe to attempt
        if action in [Action.GRAB, Action.CLIMB]:
            return True
        
        # Shooting actions are safe if we have arrow
        if action.value.startswith("shoot_"):
            return self.has_arrow
        
        # Movement actions need safety check
        if action.value.startswith("move_"):
            target_pos = self._get_target_position_from_action(action)
            if target_pos is None:  # Out of bounds
                return False
            
            # Only allow moves to definitely safe positions
            return self._is_definitely_safe(target_pos)
        
        return True

    def _get_target_position_from_action(self, action: Action) -> Optional[Tuple[int, int]]:
        """Get target position for a movement action"""
        x, y = self.position
        
        if action == Action.MOVE_UP:
            return (x, y + 1) if y + 1 < self.size else None
        elif action == Action.MOVE_DOWN:
            return (x, y - 1) if y - 1 >= 0 else None
        elif action == Action.MOVE_LEFT:
            return (x - 1, y) if x - 1 >= 0 else None
        elif action == Action.MOVE_RIGHT:
            return (x + 1, y) if x + 1 < self.size else None
        
        return None

    def _convert_action_to_command(self, action: Action) -> str:
        """Convert Action enum to string command"""
        
        if action == Action.GRAB:
            return "Grab"
        elif action == Action.CLIMB:
            return "Climb"
        elif action in [Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT]:
            return self._handle_movement_action(action)
        elif action in [Action.SHOOT_UP, Action.SHOOT_DOWN, Action.SHOOT_LEFT, Action.SHOOT_RIGHT]:
            return self._handle_shooting_action(action)
        
        return "TurnLeft"  # Default fallback

    def _handle_movement_action(self, action: Action) -> str:
        """Handle movement action by turning to correct direction and moving forward"""
        required_dir = self._get_required_direction_for_action(action)
        
        if self.direction == required_dir:
            return "Forward"
        else:
            # Plan the movement for next turn
            self.plan.appendleft("Forward")
            return self._get_turn_action(required_dir)

    def _handle_shooting_action(self, action: Action) -> str:
        """Handle shooting action by turning to correct direction and shooting"""
        required_dir = self._get_required_direction_for_action(action)
        
        if self.direction == required_dir:
            return "Shoot"
        else:
            # Plan the shooting for next turn
            self.plan.appendleft("Shoot")
            return self._get_turn_action(required_dir)

    def _get_required_direction_for_action(self, action: Action) -> int:
        """Get the direction needed for a movement or shooting action"""
        if action in [Action.MOVE_UP, Action.SHOOT_UP]:
            return 0  # North
        elif action in [Action.MOVE_RIGHT, Action.SHOOT_RIGHT]:
            return 1  # East
        elif action in [Action.MOVE_DOWN, Action.SHOOT_DOWN]:
            return 2  # South
        elif action in [Action.MOVE_LEFT, Action.SHOOT_LEFT]:
            return 3  # West
        
        return self.direction  # Default to current direction

    def _choose_action(self, percepts: List[str]) -> str:
        """Original action selection method as fallback"""
        # Priority 1: Emergency retreat if in immediate danger
        if self._is_in_immediate_danger(percepts):
            return self._emergency_action(percepts)

        # Priority 2: Try to shoot wumpus if we have a clear shot
        if "Stench" in percepts and not self.shot_attempted and self.has_arrow:
            shoot_action = self._try_shoot_wumpus(percepts)
            if shoot_action:
                return shoot_action

        # Priority 3: Explore definitely safe unvisited cells
        safe_unvisited = self._get_definitely_safe_unvisited()
        if safe_unvisited:
            target = self._choose_best_safe_target(safe_unvisited)
            path = self._find_safe_path_to_position(target)
            if path:
                self.plan.extend(self._path_to_actions(path))
                return self.plan.popleft()

        # Priority 4: Return home if no safe exploration options
        if not self.returning_home:
            self.returning_home = True
            path = self._find_safe_path_to_start()
            if path:
                self.plan.extend(self._path_to_actions(path))
                return self.plan.popleft()

        # Priority 5: Emergency fallback
        return self._emergency_action(percepts)

    def _is_in_immediate_danger(self, percepts: List[str]) -> bool:
        """Check if agent is in immediate danger and needs to retreat"""
        # If we sense danger and haven't shot yet, we're in danger
        if ("Stench" in percepts or "Breeze" in percepts) and not self.shot_attempted:
            return True
        
        # Check if current position has become dangerous based on new information
        if not self._is_definitely_safe(self.position):
            return True
            
        return False

    def _emergency_action(self, percepts: List[str]) -> str:
        """Handle emergency situations with safe retreat"""
        # Try to find a safe adjacent cell to move to
        safe_moves = self._get_safe_adjacent_moves()
        
        if safe_moves:
            # Choose the safest move (preferably back to last safe position)
            if self.last_safe_position in safe_moves:
                target = self.last_safe_position
            else:
                target = min(safe_moves, key=lambda pos: self._manhattan_distance(pos, self.last_safe_position))
            
            actions = self._get_actions_to_adjacent(target)
            if actions:
                return actions[0]
        
        # If no safe moves, try to shoot if we have arrow and detect stench
        if "Stench" in percepts and self.has_arrow and not self.shot_attempted:
            shoot_action = self._try_shoot_wumpus(percepts)
            if shoot_action:
                return shoot_action
        
        # Last resort: turn around
        return "TurnLeft"

    def _get_safe_adjacent_moves(self) -> List[Tuple[int, int]]:
        """Get all adjacent cells that are definitely safe"""
        safe_moves = []
        x, y = self.position
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.size and 0 <= ny < self.size and 
                self._is_definitely_safe((nx, ny))):
                safe_moves.append((nx, ny))
        
        return safe_moves

    def _is_definitely_safe(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is definitely safe (no possibility of danger)"""
        if pos in self.kb.visited:
            return True
        
        if pos in self.kb.safe_cells:
            # Double-check it's not in any danger sets
            if pos in self.kb.pit_possible or pos in self.kb.wumpus_possible:
                return False
            return True
        
        return False

    def _get_definitely_safe_unvisited(self) -> Set[Tuple[int, int]]:
        """Get cells that are definitely safe and unvisited"""
        safe_unvisited = set()
        
        for pos in self.kb.safe_cells:
            if pos not in self.kb.visited and self._is_definitely_safe(pos):
                safe_unvisited.add(pos)
        
        return safe_unvisited

    def _choose_best_safe_target(self, safe_targets: Set[Tuple[int, int]]) -> Tuple[int, int]:
        """Choose the best safe target based on exploration value"""
        def target_score(pos):
            # Prefer closer targets
            distance_score = 1.0 / (1 + self._manhattan_distance(self.position, pos))
            
            # Prefer targets with more unexplored neighbors
            unexplored_neighbors = sum(1 for adj in self._get_adjacent(pos) 
                                     if adj not in self.kb.visited and self._is_definitely_safe(adj))
            exploration_score = unexplored_neighbors * 0.5
            
            return distance_score + exploration_score
        
        return max(safe_targets, key=target_score)

    def _try_shoot_wumpus(self, percepts: List[str]) -> Optional[str]:
        """Try to shoot wumpus with high confidence - updated for multiple Wumpuses"""
        if not self.has_arrow or self.shot_attempted or not self.kb.wumpus_alive:
            return None

        if "Stench" in percepts:
            x, y = self.position
            
            # Look for high-confidence wumpus locations
            possible_targets = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.size and 0 <= ny < self.size and 
                    (nx, ny) in self.kb.wumpus_possible and
                    self.kb.get_wumpus_probability((nx, ny)) > 0.7):  # Slightly lower threshold for multiple Wumpuses
                    possible_targets.append((nx, ny))
            
            if possible_targets:
                # Choose the target with highest probability
                target = max(possible_targets, key=lambda pos: self.kb.get_wumpus_probability(pos))
                required_dir = self._get_direction_to_position(target)
                
                if required_dir == self.direction:
                    self.shot_attempted = True
                    return "Shoot"
                else:
                    # Plan to turn and shoot
                    turn_action = self._get_turn_action(required_dir)
                    self.plan.appendleft("Shoot")
                    return turn_action

        return None

    def _find_safe_path_to_position(self, target: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find a path using only definitely safe cells"""
        if self.position == target:
            return []

        open_set = [(0, self.position)]
        came_from = {}
        g_score = {self.position: 0}

        while open_set:
            current = heappop(open_set)[1]
            
            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))

            for neighbor in self._get_adjacent(current):
                if not self._is_definitely_safe(neighbor):
                    continue

                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self._manhattan_distance(neighbor, target)
                    heappush(open_set, (f_score, neighbor))

        return []

    def _find_safe_path_to_start(self) -> List[Tuple[int, int]]:
        """Find a safe path back to starting position"""
        return self._find_safe_path_to_position((0, 0))

    def _get_next_position(self) -> Tuple[int, int]:
        """Get the position agent would move to if going forward"""
        x, y = self.position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = directions[self.direction]
        return (x + dx, y + dy)

    def _path_to_actions(self, path: List[Tuple[int, int]]) -> List[str]:
        """Convert path to sequence of actions"""
        if not path:
            return []

        actions = []
        current_pos = self.position
        current_dir = self.direction

        for next_pos in path:
            required_dir = self._get_direction_to_position(next_pos, current_pos)
            
            while current_dir != required_dir:
                if self._get_turn_direction(current_dir, required_dir) == "left":
                    actions.append("TurnLeft")
                    current_dir = (current_dir - 1) % 4
                else:
                    actions.append("TurnRight")
                    current_dir = (current_dir + 1) % 4

            actions.append("Forward")
            current_pos = next_pos

        return actions

    def _get_actions_to_adjacent(self, target: Tuple[int, int]) -> List[str]:
        """Get actions to move to adjacent cell"""
        required_dir = self._get_direction_to_position(target)
        actions = []
        current_dir = self.direction

        while current_dir != required_dir:
            if self._get_turn_direction(current_dir, required_dir) == "left":
                actions.append("TurnLeft")
                current_dir = (current_dir - 1) % 4
            else:
                actions.append("TurnRight")
                current_dir = (current_dir + 1) % 4

        actions.append("Forward")
        return actions

    def _get_direction_to_position(self, target: Tuple[int, int], from_pos: Tuple[int, int] = None) -> int:
        """Get direction needed to reach target position"""
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
        """Determine if we should turn left or right"""
        diff = (target_dir - current_dir) % 4
        return "left" if diff == 3 else "right"

    def _get_turn_action(self, target_dir: int) -> str:
        """Get the turn action needed to face target direction"""
        return "TurnLeft" if self._get_turn_direction(self.direction, target_dir) == "left" else "TurnRight"

    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _get_adjacent(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all adjacent positions within bounds"""
        x, y = pos
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                adjacent.append((nx, ny))
        return adjacent

    def update_state(self, action: str, result: str):
        """Update agent state based on action result"""
        if action == "Forward" and "Moved forward" in result:
            x, y = self.position
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            dx, dy = directions[self.direction]
            new_pos = (x + dx, y + dy)
            
            # Update last safe position before moving
            if self._is_definitely_safe(self.position):
                self.last_safe_position = self.position
            
            self.position = new_pos
            self.kb.add_visit(self.position)
            self.score -= 1

        elif action == "TurnLeft":
            self.direction = (self.direction - 1) % 4

        elif action == "TurnRight":
            self.direction = (self.direction + 1) % 4

        elif action == "Grab" and "Grabbed gold" in result:
            self.has_gold = True
            self.score += 1000

        elif action == "Shoot":
            self.has_arrow = False
            self.score -= 10
            if "Wumpus died" in result:
                self.kb.wumpus_killed()

        elif action == "Climb" and "Climbed out" in result:
            self.score += 500

    def get_score(self) -> int:
        return self.score

    def is_alive(self) -> bool:
        return True