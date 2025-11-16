# This script defines the MegaMiner environment for reinforcement learning using the PettingZoo API.
# It acts as a wrapper around the main game logic, allowing RL agents to interact with the game.
# The environment is designed to be used with libraries like Stable Baselines3 for training RL agents.

import gymnasium
import numpy as np
from gymnasium.spaces import Box, Dict, Discrete
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
import sys
from pathlib import Path

# Add the backend directory to the Python path to import game components.
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from Game import Game
from AIAction import AIAction
import Constants

def env(map_path):
    """
    The env function wraps the raw environment in helpful wrappers provided by PettingZoo.
    These wrappers can enforce constraints and perform standard transformations, which is good practice.
    """
    internal_render_mode = "human"
    env = raw_env(render_mode=internal_render_mode, map_path=map_path)
    # This wrapper asserts that actions are within the defined action space.
    # It's useful for debugging during development to catch invalid actions.
    env = wrappers.AssertOutOfBoundsWrapper(env)
    return env

class raw_env(AECEnv):
    """
    The raw environment for MegaMiner, implementing the PettingZoo AECEnv (Agent-Environment-Cycle) API.
    This class handles the core logic of the environment, including:
    - State Management: Tracking the positions of all entities, player health, money, etc.
    - Action Handling: Receiving actions from agents and applying them to the game state.
    - Observation Generation: Converting the game state into a format that RL agents can understand.
    - Reward Calculation: Providing a reward signal to the agents based on their performance.
    """
    metadata = {
        "render_modes": ["human"],  # "human" mode is a placeholder; visualization is handled by a separate Godot project.
        "name": "MegaMiner_v0",
        "is_parallelizable": True,  # The environment can be run in parallel for faster training.
    }

    # Define maximum map dimensions for padding the observation space.
    # This ensures a consistent observation shape regardless of the actual map size, which is required by most RL libraries.
    MAX_MAP_WIDTH = 50
    MAX_MAP_HEIGHT = 50

    def __init__(self, map_path, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        
        # Load the game map and initialize the game state from the backend.
        self.map_path = map_path
        self.game = Game(self.map_path)
        self.map_size = (len(self.game.game_state.floor_tiles[0]), len(self.game.game_state.floor_tiles))

        # --- PettingZoo Setup ---
        # Define the agents that exist in the environment.
        self.agents = ["player_r", "player_b"]
        self.possible_agents = self.agents[:]
        # The agent_selector is a utility that cycles through agents in a round-robin fashion.
        self._agent_selector = agent_selector(self.agents)
        
        # Define the action and observation spaces for the agents. These must be consistent for all agents.
        self._action_space_dict = self._create_action_space()
        self._observation_space_dict = self._create_observation_space()

        # --- Game State Tracking ---
        # These dictionaries store the current state for each agent.
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents} # True if an agent has reached a terminal state (e.g., won/lost).
        self.truncations = {agent: False for agent in self.agents}   # True if the episode is ended for other reasons (e.g., time limit).
        self.infos = {agent: {} for agent in self.agents}            # Auxiliary diagnostic information.

        # In this simultaneous-move game, we need to store the action of the first agent
        # while we wait for the action of the second agent.
        self.action_r = None
        self.action_b = None

    def observation_space(self, agent):
        """Returns the observation space for a given agent."""
        return self._observation_space_dict

    def action_space(self, agent):
        """Returns the action space for a given agent."""
        return self._action_space_dict

    def _create_action_space(self):
        """
        Defines the action space for an agent.
        We use a MultiDiscrete space, which is a flat vector of discrete choices.
        This is a common way to represent a complex action space for an RL agent.
        The vector is structured as: [action_type, x, y, tower_type, merc_direction]
        """
        return gymnasium.spaces.MultiDiscrete([
            3,  # action_type: 0=nothing, 1=build, 2=destroy
            self.MAX_MAP_WIDTH,  # x-coordinate for the action (0 to MAX_MAP_WIDTH-1)
            self.MAX_MAP_HEIGHT, # y-coordinate for the action (0 to MAX_MAP_HEIGHT-1)
            4,  # tower_type: 0=crossbow, 1=cannon, 2=minigun, 3=house
            5   # merc_direction: 0="", 1=N, 2=S, 3=E, 4=W (used for spawning mercenaries)
        ])

    def _create_observation_space(self):
        """
        Defines the observation space for an agent.
        The observation is a flattened vector combining a multi-channel map representation
        and a vector of game state features. This is suitable for an MLP (Multi-Layer Perceptron) policy.
        A CNN (Convolutional Neural Network) could also be used if the map representation is kept as a 3D tensor.
        """
        # The map is represented as a 3D tensor (Height, Width, Channels).
        map_shape = (self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7)
        # The vector part contains additional global game state information.
        vector_size = 5
        
        # The total observation size is the flattened map plus the vector features.
        total_obs_size = np.prod(map_shape) + vector_size

        return Box(low=-np.inf, high=np.inf, shape=(total_obs_size,), dtype=np.float32)

    def _get_obs(self, agent):
        """
        Constructs the observation vector for the current agent.
        This function gathers all relevant game state information and packs it into the format
        defined by the observation space. It is crucial that this function is deterministic and
        accurately reflects the game state.
        """
        is_red_agent = agent == "player_r"
        map_h, map_w = self.map_size[1], self.map_size[0]

        # --- Map Representation (Multi-channel) ---
        # We use a multi-channel map to represent spatial information. Each channel represents a different aspect of the game state.
        # This is a common technique in RL for games with a spatial component.
        obs_map = np.zeros((self.MAX_MAP_HEIGHT, self.MAX_MAP_WIDTH, 7), dtype=np.float32)
        map_view = obs_map[:map_h, :map_w, :] # A view for easier indexing into the non-padded area.

        # Channel 0: Terrain Type
        # Encodes the type of each tile: 1 for Path, 2 for My Territory, 3 for Opponent's Territory.
        my_territory_char = 'R' if is_red_agent else 'B'
        opp_territory_char = 'B' if is_red_agent else 'R'
        for r_idx, row in enumerate(self.game.game_state.floor_tiles):
            for c_idx, tile in enumerate(row):
                if tile == 'P': map_view[r_idx, c_idx, 0] = 1
                elif tile == my_territory_char: map_view[r_idx, c_idx, 0] = 2
                elif tile == opp_territory_char: map_view[r_idx, c_idx, 0] = 3

        # --- Entity Channels ---
        # Channel 1: Entity Type (1: Tower, 2: Merc, 3: Demon, 4: Base)
        # Channel 2: Health (normalized for mercs, demons, bases)
        # Channel 3: Team Affiliation (1: Mine, -1: Opponent's, 0: Neutral)
        # Channel 4: Tower Type (1-4 for different tower types)
        # Channel 5: Tower Cooldown (normalized)
        # Channel 6: Unit State (1: walking, 2: attacking)
        
        tower_type_map = {"crossbow": 1, "cannon": 2, "minigun": 3, "house": 4}
        for t in self.game.game_state.towers:
            my_team = (is_red_agent and t.team == 'r') or (not is_red_agent and t.team == 'b')
            map_view[t.y, t.x, 1] = 1
            map_view[t.y, t.x, 2] = t.health
            map_view[t.y, t.x, 3] = 1 if my_team else -1
            map_view[t.y, t.x, 4] = tower_type_map.get(t.name.lower(), 0)
            tower_cooldown_map = {
                "HOUSE": Constants.HOUSE_MAX_COOLDOWN, "CANNON": Constants.CANNON_MAX_COOLDOWN,
                "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN, "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
            }
            max_cd = tower_cooldown_map.get(t.name.upper(), 1)
            map_view[t.y, t.x, 5] = t.current_cooldown / max_cd if max_cd > 0 else 0

        merc_state_map = {"walking": 1, "attacking": 2}
        for m in self.game.game_state.mercs:
            my_team = (is_red_agent and m.team == 'r') or (not is_red_agent and m.team == 'b')
            y, x = int(m.y), int(m.x)
            map_view[y, x, 1] = 2
            map_view[y, x, 2] = m.health / Constants.MERCENARY_INITIAL_HEALTH if Constants.MERCENARY_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 1 if my_team else -1
            map_view[y, x, 6] = merc_state_map.get(m.state, 0)

        demon_state_map = {"walking": 1, "attacking": 2}
        for d in self.game.game_state.demons:
            y, x = int(d.y), int(d.x)
            map_view[y, x, 1] = 3
            map_view[y, x, 2] = d.health / Constants.DEMON_INITIAL_HEALTH if Constants.DEMON_INITIAL_HEALTH > 0 else 0
            map_view[y, x, 3] = 0
            map_view[y, x, 6] = demon_state_map.get(d.state, 0)

        base_r = self.game.game_state.player_base_r
        base_b = self.game.game_state.player_base_b
        my_base = base_r if is_red_agent else base_b
        opp_base = base_b if is_red_agent else base_r
        map_view[my_base.y, my_base.x, 1] = 4
        map_view[my_base.y, my_base.x, 2] = my_base.health / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
        map_view[my_base.y, my_base.x, 3] = 1
        map_view[opp_base.y, opp_base.x, 1] = 4
        map_view[opp_base.y, opp_base.x, 2] = opp_base.health / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
        map_view[opp_base.y, opp_base.x, 3] = -1

        # --- Vector Features ---
        # These are global, non-spatial game state variables.
        my_money = self.game.game_state.money_r if is_red_agent else self.game.game_state.money_b
        my_base_health = self.game.game_state.player_base_r.health if is_red_agent else self.game.game_state.player_base_b.health
        opp_money = self.game.game_state.money_b if is_red_agent else self.game.game_state.money_r
        opp_base_health = self.game.game_state.player_base_b.health if is_red_agent else self.game.game_state.player_base_r.health
        turns_remaining = self.game.game_state.turns_remaining

        vector_features = np.array([
            my_money, my_base_health, opp_money, opp_base_health, turns_remaining
        ], dtype=np.float32)

        # Normalize vector features to be roughly in the range [0, 1]. This helps with model training.
        vector_features[0] /= 1000
        vector_features[1] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
        vector_features[2] /= 1000
        vector_features[3] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
        vector_features[4] /= Constants.MAX_TURNS if Constants.MAX_TURNS > 0 else 1
        
        # --- Flatten and Concatenate ---
        # Flatten the map and concatenate it with the vector features to create a single, long observation vector.
        flat_map = obs_map.flatten()
        return np.concatenate([flat_map, vector_features])

    def observe(self, agent):
        """
        Returns the observation for the specified agent.
        This is the public method called by the agent to get its observation.
        """
        return self._get_obs(agent)

    def reset(self, seed=None, options=None):
        """
        Resets the environment to its initial state for a new episode and returns the initial observation.
        """
        # Reset the underlying game engine to a fresh state.
        self.game = Game(self.map_path)

        # Reset the PettingZoo-specific state for the new episode.
        self.agents = self.possible_agents[:]
        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.next()

        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        self.action_r = None
        self.action_b = None

        # Get the initial observation for the first agent to act.
        observation = self._get_obs(self.agent_selection)
        info = self.infos[self.agent_selection]
        
        return observation, info

    def step(self, action):
        """
        Takes a step in the environment for the current agent.
        This involves storing the agent's action, and if all agents have acted,
        running a game turn, calculating rewards, and checking for termination.
        """
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            # If the agent is done, it shouldn't be able to act. Handle this gracefully.
            self._was_dead_step(action)
            return

        agent = self.agent_selection
        
        # --- Decode and Validate Action ---
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        act_type, x, y, tower_type, merc_dir = action
        
        map_w, map_h = self.map_size
        original_x, original_y = action[1], action[2] 

        # Clamp coordinates to be within the map boundaries.
        x = np.clip(original_x, 0, map_w - 1)
        y = np.clip(original_y, 0, map_h - 1)

        # If the agent chose an action outside the map, penalize it and force a "nothing" action.
        # This encourages the agent to learn the map boundaries.
        if original_x >= map_w or original_y >= map_h:
            self.rewards[agent] -= 0.1  # Small penalty for invalid action.
            act_type = 0 # Force "nothing" action.

        ai_action = AIAction(
            action=action_type_map[act_type], x=x, y=y,
            tower_type=tower_type_map[tower_type], merc_direction=merc_dir_map[merc_dir]
        )

        # --- Store action and wait for the other agent ---
        if agent == "player_r":
            self.action_r = ai_action
        else:
            self.action_b = ai_action

        # --- Cycle agent selection for the next turn ---
        self.agent_selection = self._agent_selector.next()

        # --- If both agents have acted, run the game turn ---
        if self.action_r is not None and self.action_b is not None:
            # Store state before the turn to calculate rewards based on the change in state.
            old_health_r = self.game.game_state.player_base_r.health
            old_health_b = self.game.game_state.player_base_b.health
            old_money_r = self.game.game_state.money_r
            old_money_b = self.game.game_state.money_b

            # Run the game turn with the actions from both agents.
            self.game.run_turn(self.action_r, self.action_b)

            # Reset stored actions for the next turn.
            self.action_r = None
            self.action_b = None

            # --- Calculate Rewards ---
            # Reward shaping is crucial for training RL agents effectively.
            # We use a sparse reward for winning/losing and a dense reward for in-game events.
            health_r = self.game.game_state.player_base_r.health
            health_b = self.game.game_state.player_base_b.health
            money_r = self.game.game_state.money_r
            money_b = self.game.game_state.money_b

            # --- Reward Components ---
            # 1. Health Delta: A zero-sum reward for damaging the opponent's base vs. taking damage.
            # This is a primary objective, so it has a high weight.
            health_delta_r = (old_health_b - health_b) - (old_health_r - health_r)
            health_delta_b = (old_health_r - health_r) - (old_health_b - health_b)

            # 2. Economic Delta: A small reward for increasing one's money.
            # This encourages building houses and managing the economy.
            income_r = money_r - old_money_r
            income_b = money_b - old_money_b

            # 3. Time Penalty: A small negative reward each turn to encourage faster wins and prevent passive behavior.
            time_penalty = -0.01

            # --- Total Reward ---
            # The final reward is a weighted sum of the components.
            # Tuning these weights is a key part of training a successful agent.
            w_health = 1.0  # Health is the most important factor.
            w_econ = 0.05   # Economy is a secondary concern.

            reward_r = (w_health * health_delta_r) + (w_econ * income_r) + time_penalty
            reward_b = (w_health * health_delta_b) + (w_econ * income_b) + time_penalty
            
            self.rewards["player_r"] += reward_r
            self.rewards["player_b"] += reward_b

            # --- Check for Termination (Game Over) ---
            if self.game.game_state.is_game_over():
                # A large, sparse reward for winning and a penalty for losing.
                if self.game.game_state.victory == 'r':
                    self.rewards["player_r"] += 100
                    self.rewards["player_b"] -= 100
                elif self.game.game_state.victory == 'b':
                    self.rewards["player_b"] += 100
                    self.rewards["player_r"] -= 100
                
                self.terminations = {a: True for a in self.agents}

            # Update cumulative rewards for logging and debugging.
            for a in self.agents:
                self._cumulative_rewards[a] = self.rewards[a]

        # Handle rendering if enabled.
        if self.render_mode == "human":
            self.render()

    def render(self):
        """
        The game has a Godot-based visualizer, which is a separate process.
        This function is a no-op as rendering is not handled directly within this environment.
        """
        pass

    def close(self):
        """
        Cleans up any resources used by the environment.
        """
        pass

if __name__ == '__main__':
    # This block is for testing the environment to ensure it conforms to the PettingZoo API.
    from pettingzoo.test import api_test

    map_file = str(Path(__file__).resolve().parent.parent / 'maps' / 'map0.json')
    env = env(map_path=map_file)
    
    print("Running PettingZoo API test...")
    # The API test runs a series of checks to ensure the environment is correctly implemented.
    api_test(env, num_cycles=1000, verbose_progress=True)
    print("API test passed!")
