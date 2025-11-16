# This script defines the PPO (Proximal Policy Optimization) agent that plays the MegaMiner game.
# It loads a pre-trained PPO model and uses it to decide on actions during the game.
# This script is designed to be run as a separate process by the game engine.

import json
import numpy as np
import sys
from pathlib import Path

# Add the backend directory to the Python path to import game constants.
# This is necessary for the observation conversion function.
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
import Constants

class AIAction:
    """
    Represents one turn of actions in the game.
    This class is a simplified copy from the game's backend to make the agent self-contained.
    It allows the agent to structure its chosen action in a way the game engine understands.
    """
    def __init__(
        self,
        action: str,
        x: int,
        y: int,
        tower_type: str = "",
        merc_direction: str = ""
    ):
        self.action = action.lower().strip()
        self.x = x
        self.y = y
        self.tower_type = tower_type.strip()
        self.merc_direction = merc_direction.upper().strip()

    def to_dict(self):
        """Converts the action to a dictionary."""
        return {
            'action': self.action, 'x': self.x, 'y': self.y,
            'tower_type': self.tower_type, 'merc_direction': self.merc_direction
        }

    def to_json(self):
        """Serializes the action to a JSON string, which is sent to the game engine."""
        return json.dumps(self.to_dict())

def _convert_state_to_obs(game_state: dict, team_color: str) -> np.ndarray:
    """
    Converts the JSON game state received from the game engine into the flattened
    observation vector that the PPO model was trained on.
    
    This function is critical and must exactly match the observation generation
    logic in the training environment (MegaMinerEnv.py). Any mismatch will lead
    to poor performance as the agent will misinterpret the game state.
    """
    map_size = (len(game_state['FloorTiles'][0]), len(game_state['FloorTiles']))
    
    # These must match the values in the training environment.
    MAX_MAP_WIDTH = 50
    MAX_MAP_HEIGHT = 50

    is_red_agent = team_color == "r"
    map_h, map_w = map_size[1], map_size[0]

    # --- Map Representation (Multi-channel) ---
    # Initialize a padded map with zeros.
    obs_map = np.zeros((MAX_MAP_HEIGHT, MAX_MAP_WIDTH, 7), dtype=np.float32)
    map_view = obs_map[:map_h, :map_w, :]

    # Channel 0: Terrain
    my_territory_char = 'R' if is_red_agent else 'B'
    opp_territory_char = 'B' if is_red_agent else 'R'
    for r_idx, row in enumerate(game_state['FloorTiles']):
        for c_idx, tile in enumerate(row):
            if tile == 'P': map_view[r_idx, c_idx, 0] = 1
            elif tile == my_territory_char: map_view[r_idx, c_idx, 0] = 2
            elif tile == opp_territory_char: map_view[r_idx, c_idx, 0] = 3

    # Channels 1-6: Entities
    tower_type_map = {"crossbow": 1, "cannon": 2, "minigun": 3, "house": 4}
    for t in game_state['Towers']:
        my_team = (is_red_agent and t['Team'] == 'r') or (not is_red_agent and t['Team'] == 'b')
        map_view[t['y'], t['x'], 1] = 1
        map_view[t['y'], t['x'], 2] = t.get('Health', 1)
        map_view[t['y'], t['x'], 3] = 1 if my_team else -1
        map_view[t['y'], t['x'], 4] = tower_type_map.get(t['Type'].lower(), 0)
        tower_cooldown_map = {
            "HOUSE": Constants.HOUSE_MAX_COOLDOWN,
            "CANNON": Constants.CANNON_MAX_COOLDOWN,
            "MINIGUN": Constants.MINIGUN_MAX_COOLDOWN,
            "CROSSBOW": Constants.CROSSBOW_MAX_COOLDOWN,
        }
        max_cd = tower_cooldown_map.get(t['Type'].upper(), 1)
        map_view[t['y'], t['x'], 5] = t.get('Cooldown', 0) / max_cd if max_cd > 0 else 0

    merc_state_map = {"walking": 1, "attacking": 2}
    for m in game_state['Mercenaries']:
        my_team = (is_red_agent and m['Team'] == 'r') or (not is_red_agent and m['Team'] == 'b')
        y, x = int(m['y']), int(m['x'])
        map_view[y, x, 1] = 2
        map_view[y, x, 2] = m['Health'] / Constants.MERCENARY_INITIAL_HEALTH if Constants.MERCENARY_INITIAL_HEALTH > 0 else 0
        map_view[y, x, 3] = 1 if my_team else -1
        map_view[y, x, 6] = merc_state_map.get(m['State'], 0)

    demon_state_map = {"walking": 1, "attacking": 2}
    for d in game_state['Demons']:
        y, x = int(d['y']), int(d['x'])
        map_view[y, x, 1] = 3
        map_view[y, x, 2] = d['Health'] / Constants.DEMON_INITIAL_HEALTH if Constants.DEMON_INITIAL_HEALTH > 0 else 0
        map_view[y, x, 3] = 0
        map_view[y, x, 6] = demon_state_map.get(d['State'], 0)

    base_r = game_state['PlayerBaseR']
    base_b = game_state['PlayerBaseB']
    my_base = base_r if is_red_agent else base_b
    opp_base = base_b if is_red_agent else base_r
    map_view[my_base['y'], my_base['x'], 1] = 4
    map_view[my_base['y'], my_base['x'], 2] = my_base['Health'] / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
    map_view[my_base['y'], my_base['x'], 3] = 1
    map_view[opp_base['y'], opp_base['x'], 1] = 4
    map_view[opp_base['y'], opp_base['x'], 2] = opp_base['Health'] / Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 0
    map_view[opp_base['y'], opp_base['x'], 3] = -1

    # --- Vector Features ---
    my_money = game_state['RedTeamMoney'] if is_red_agent else game_state['BlueTeamMoney']
    my_base_health = game_state['PlayerBaseR']['Health'] if is_red_agent else game_state['PlayerBaseB']['Health']
    opp_money = game_state['BlueTeamMoney'] if is_red_agent else game_state['RedTeamMoney']
    opp_base_health = game_state['PlayerBaseB']['Health'] if is_red_agent else game_state['PlayerBaseR']['Health']
    turns_remaining = game_state['TurnsRemaining']

    vector_features = np.array([
        my_money, my_base_health, opp_money, opp_base_health, turns_remaining
    ], dtype=np.float32)

    # Normalize vector features, same as in the training environment.
    vector_features[0] /= 1000
    vector_features[1] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
    vector_features[2] /= 1000
    vector_features[3] /= Constants.PLAYER_BASE_INITIAL_HEALTH if Constants.PLAYER_BASE_INITIAL_HEALTH > 0 else 1
    vector_features[4] /= Constants.MAX_TURNS if Constants.MAX_TURNS > 0 else 1
    
    # --- Flatten and Concatenate ---
    flat_map = obs_map.flatten()
    return np.concatenate([flat_map, vector_features])


class Agent:
    """
    The main agent class that the game engine interacts with.
    """
    def initialize_and_set_name(self, initial_game_state: dict, team_color: str) -> str:
        """
        This method is called once at the beginning of the game.
        It's used to initialize the agent, load the model, and set the agent's name.
        """
        self.team_color = team_color
        
        # We need to import the PPO class from stable-baselines3.
        # This is done inside the method to avoid loading the library if the agent is not used.
        from stable_baselines3 import PPO

        # Load the trained PPO model. The path points to the best model saved during training.
        model_path = Path(__file__).resolve().parent.parent / "training" / "models" / "best_model" / "best_model.zip"
        print(f"DEBUG: Attempting to load model from: {model_path}", file=sys.stderr)
        try:
            self.model = PPO.load(model_path)
            print("DEBUG: Model loaded successfully.", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to load PPO model: {e}", file=sys.stderr)
            raise # Re-raise the exception to crash the agent process if the model can't be loaded.
        
        # Return the name of the agent.
        return "PPO_Agent"
    
    def do_turn(self, game_state: dict) -> AIAction:
        """
        This method is called once per turn.
        It receives the current game state and must return an AIAction object.
        """
        print("DEBUG: do_turn called.", file=sys.stderr)
        
        # 1. Convert the game state dictionary into the numpy array observation format.
        observation = _convert_state_to_obs(game_state, self.team_color)
        print(f"DEBUG: Observation created, shape: {observation.shape}", file=sys.stderr)
        
        # Reshape the observation to have a batch dimension of 1, as the model expects.
        observation = observation.reshape(1, -1)
        print(f"DEBUG: Observation reshaped, new shape: {observation.shape}", file=sys.stderr)
        
        # 2. Use the loaded model to predict the action based on the observation.
        # `deterministic=True` means the model will always choose the action with the highest probability.
        print("DEBUG: Calling model.predict...", file=sys.stderr)
        try:
            action_vector, _states = self.model.predict(observation, deterministic=True)
            print(f"DEBUG: model.predict returned action_vector: {action_vector}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to predict action: {e}", file=sys.stderr)
            raise
        
        # 3. Decode the action vector from the model back into an AIAction object.
        # The action_vector is a numpy array, e.g., [1, 10, 15, 0, 0].
        action_type_map = {0: "nothing", 1: "build", 2: "destroy"}
        tower_type_map = {0: "crossbow", 1: "cannon", 2: "minigun", 3: "house"}
        merc_dir_map = {0: "", 1: "N", 2: "S", 3: "E", 4: "W"}

        # Extract the discrete action choices from the vector.
        act_type, x, y, tower_type, merc_dir = np.int64(action_vector[0]).tolist()

        # Create the AIAction object.
        ai_action = AIAction(
            action=action_type_map[act_type],
            x=x,
            y=y,
            tower_type=tower_type_map[tower_type],
            merc_direction=merc_dir_map[merc_dir]
        )
        print(f"DEBUG: AIAction object created: {ai_action.to_dict()}", file=sys.stderr)
        
        # Return the action to the game engine.
        return ai_action

# -- DRIVER CODE (DO NOT ALTER) --
# This part of the script handles the communication with the game engine.
# It reads the game state from standard input and writes the agent's actions to standard output.
if __name__ == '__main__':
    # Determine team color from the first line of input.
    team_color = 'r' if input() == "--YOU ARE RED--" else 'b'
    
    # Read the initial game state.
    initial_state_json = ""
    while True:
        line = input()
        if line == "--END INITIAL GAME STATE--":
            break
        initial_state_json += line
    game_state_init = json.loads(initial_state_json)

    # Initialize the agent.
    agent = Agent()
    # The first output must be the agent's name.
    print(agent.initialize_and_set_name(game_state_init, team_color))
    # The second output is the action for the first turn.
    print(agent.do_turn(game_state_init).to_json())

    # Main game loop.
    while True:
        # Read the game state for the current turn.
        turn_state_json = ""
        while True:
            line = input()
            if line == "--END OF TURN--":
                break
            turn_state_json += line
        game_state_this_turn = json.loads(turn_state_json)
        # Output the agent's action for this turn.
        print(agent.do_turn(game_state_this_turn).to_json())