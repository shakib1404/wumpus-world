import random
import math
from typing import Set, Tuple, List, Dict, Optional
from enum import Enum

class Action(Enum):
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    SHOOT_UP = "shoot_up"
    SHOOT_DOWN = "shoot_down"
    SHOOT_LEFT = "shoot_left"
    SHOOT_RIGHT = "shoot_right"
    GRAB = "grab"
    CLIMB = "climb"

class ActionSelector:
    def __init__(self, epsilon=0.1, curiosity_weight=0.3, decay_rate=0.995):
        self.epsilon = epsilon  # Exploration probability
        self.curiosity_weight = curiosity_weight  # Weight for curiosity bonus
        self.decay_rate = decay_rate  # Decay rate for epsilon
        self.step_count = 0
        
    def select_action(self, current_pos: Tuple[int, int], knowledge_base, 
                     available_actions: List[Action], has_arrow: bool = True) -> Action:
        """
        Select the best action using improved logic with randomization,
        curiosity bonus, and epsilon-greedy exploration.
        """
        self.step_count += 1
        
        # Decay epsilon over time to reduce exploration as we learn more
        current_epsilon = self.epsilon * (self.decay_rate ** self.step_count)
        
        # Epsilon-greedy: sometimes choose random action
        if random.random() < current_epsilon:
            return random.choice(available_actions)
        
        # Calculate utilities for all available actions
        action_utilities = {}
        
        for action in available_actions:
            utility = self._calculate_action_utility(
                current_pos, action, knowledge_base, has_arrow
            )
            action_utilities[action] = utility
        
        # Find actions with maximum utility
        max_utility = max(action_utilities.values())
        best_actions = [action for action, utility in action_utilities.items() 
                       if utility == max_utility]
        
        # Tie-breaking with randomization
        if len(best_actions) > 1:
            # Add small random noise to break ties
            tie_breaker = {action: random.random() * 0.1 for action in best_actions}
            best_action = max(best_actions, key=lambda a: tie_breaker[a])
        else:
            best_action = best_actions[0]
        
        return best_action
    
    def _calculate_action_utility(self, current_pos: Tuple[int, int], 
                                 action: Action, knowledge_base, has_arrow: bool) -> float:
        """Calculate utility for a specific action"""
        
        if action == Action.GRAB:
            # High utility if gold is present
            return 1000.0 if self._gold_present(current_pos) else -100.0
        
        elif action == Action.CLIMB:
            # High utility if at starting position and have gold
            if current_pos == (0, 0) and self._have_gold():
                return 1000.0
            return -100.0
        
        elif action.value.startswith("shoot_"):
            return self._calculate_shoot_utility(current_pos, action, knowledge_base, has_arrow)
        
        elif action.value.startswith("move_"):
            return self._calculate_move_utility(current_pos, action, knowledge_base)
        
        return 0.0
    
    def _calculate_move_utility(self, current_pos: Tuple[int, int], 
                               action: Action, knowledge_base) -> float:
        """Calculate utility for movement actions"""
        target_pos = self._get_target_position(current_pos, action)
        
        if target_pos is None:  # Out of bounds
            return -1000.0
        
        base_utility = 0.0
        
        # Safety considerations
        if knowledge_base.is_definitely_safe(target_pos):
            base_utility += 100.0  # High reward for definitely safe moves
        elif knowledge_base.is_safe(target_pos):
            base_utility += 50.0   # Medium reward for likely safe moves
        elif knowledge_base.is_dangerous(target_pos):
            # Calculate risk
            pit_prob = knowledge_base.get_pit_probability(target_pos)
            wumpus_prob = knowledge_base.get_wumpus_probability(target_pos)
            
            # Heavy penalty for dangerous moves
            danger_penalty = -(pit_prob * 500 + wumpus_prob * 400)
            base_utility += danger_penalty
        
        # Curiosity bonus for unexplored areas
        if target_pos not in knowledge_base.visited:
            curiosity_bonus = self._calculate_curiosity_bonus(target_pos, knowledge_base)
            base_utility += curiosity_bonus
        
        # Distance penalty (prefer closer unexplored areas)
        distance_penalty = self._calculate_distance_penalty(current_pos, target_pos)
        base_utility -= distance_penalty
        
        # Exploration bonus for positions that might reveal new information
        exploration_bonus = self._calculate_exploration_bonus(target_pos, knowledge_base)
        base_utility += exploration_bonus
        
        return base_utility
    
    def _calculate_shoot_utility(self, current_pos: Tuple[int, int], 
                                action: Action, knowledge_base, has_arrow: bool) -> float:
        """Calculate utility for shooting actions"""
        if not has_arrow:
            return -1000.0  # Can't shoot without arrow
        
        target_pos = self._get_target_position(current_pos, action)
        if target_pos is None:
            return -100.0  # Can't shoot out of bounds
        
        # High utility if likely wumpus location
        wumpus_prob = knowledge_base.get_wumpus_probability(target_pos)
        if wumpus_prob > 0.5:
            return 200.0 + wumpus_prob * 100
        elif wumpus_prob > 0.2:
            return 50.0 + wumpus_prob * 50
        
        return -10.0  # Small penalty for wasting arrow
    
    def _calculate_curiosity_bonus(self, pos: Tuple[int, int], knowledge_base) -> float:
        """Calculate curiosity bonus for unexplored positions"""
        if pos in knowledge_base.visited:
            return 0.0
        
        # Base curiosity bonus
        base_bonus = 30.0 * self.curiosity_weight
        
        # Additional bonus for positions that could reveal information about many unknowns
        adjacent_unknowns = sum(1 for adj in knowledge_base._get_adjacent(pos)
                               if adj not in knowledge_base.visited)
        
        information_bonus = adjacent_unknowns * 10.0 * self.curiosity_weight
        
        return base_bonus + information_bonus
    
    def _calculate_distance_penalty(self, current_pos: Tuple[int, int], 
                                   target_pos: Tuple[int, int]) -> float:
        """Calculate penalty based on Manhattan distance"""
        distance = abs(current_pos[0] - target_pos[0]) + abs(current_pos[1] - target_pos[1])
        return distance * 2.0  # Small penalty to prefer closer positions
    
    def _calculate_exploration_bonus(self, pos: Tuple[int, int], knowledge_base) -> float:
        """Calculate bonus for positions that might reveal new information"""
        if pos in knowledge_base.visited:
            return 0.0
        
        # Bonus for positions adjacent to danger possibilities
        adjacent_positions = knowledge_base._get_adjacent(pos)
        
        information_value = 0.0
        
        # Bonus for positions that could help resolve pit possibilities
        for adj in adjacent_positions:
            if adj in knowledge_base.pit_possible:
                information_value += 15.0
            if adj in knowledge_base.wumpus_possible:
                information_value += 20.0
        
        return information_value
    
    def _get_target_position(self, current_pos: Tuple[int, int], 
                            action: Action) -> Optional[Tuple[int, int]]:
        """Get target position for an action"""
        x, y = current_pos
        
        if action in [Action.MOVE_UP, Action.SHOOT_UP]:
            return (x, y + 1)
        elif action in [Action.MOVE_DOWN, Action.SHOOT_DOWN]:
            return (x, y - 1)
        elif action in [Action.MOVE_LEFT, Action.SHOOT_LEFT]:
            return (x - 1, y)
        elif action in [Action.MOVE_RIGHT, Action.SHOOT_RIGHT]:
            return (x + 1, y)
        
        return None
    
    def _gold_present(self, pos: Tuple[int, int]) -> bool:
        """Check if gold is present at current position"""
        # This should be implemented based on your game state
        # For now, return False as placeholder
        return False
    
    def _have_gold(self) -> bool:
        """Check if agent has gold"""
        # This should be implemented based on your game state
        # For now, return False as placeholder
        return False
    
    def get_available_actions(self, current_pos: Tuple[int, int], 
                             world_size: int, has_arrow: bool = True) -> List[Action]:
        """Get list of available actions from current position"""
        actions = []
        x, y = current_pos
        
        # Movement actions
        if y + 1 < world_size:
            actions.append(Action.MOVE_UP)
        if y - 1 >= 0:
            actions.append(Action.MOVE_DOWN)
        if x - 1 >= 0:
            actions.append(Action.MOVE_LEFT)
        if x + 1 < world_size:
            actions.append(Action.MOVE_RIGHT)
        
        # Shooting actions (if has arrow)
        if has_arrow:
            if y + 1 < world_size:
                actions.append(Action.SHOOT_UP)
            if y - 1 >= 0:
                actions.append(Action.SHOOT_DOWN)
            if x - 1 >= 0:
                actions.append(Action.SHOOT_LEFT)
            if x + 1 < world_size:
                actions.append(Action.SHOOT_RIGHT)
        
        # Always available actions
        actions.append(Action.GRAB)
        actions.append(Action.CLIMB)
        
        return actions