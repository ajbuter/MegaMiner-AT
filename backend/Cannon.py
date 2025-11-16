import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name
from Utils import get_increased_tower_price

class Cannon(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState) -> None:
        super().__init__(
            x, y,
            team_color,
            Constants.CANNON_MAX_COOLDOWN,
            Constants.CANNON_RANGE,
            Constants.CANNON_DAMAGE,
            game_state
        )

        self.radius = 2 # Cannon shots have a splash radius, this variable shows that
        
        self.name = select_tower_name('CA', self.team)

    def get_price(self, game_state: GameState, team_color: str):
        return (game_state.cannon_price_r if team_color == "r" else game_state.cannon_price_b)
    
    def increase_price(self, game_state: GameState, team_color: str):
        if team_color == "r":
            game_state.cannon_price_r = get_increased_tower_price(game_state.cannon_price_r, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
        else:
            game_state.cannon_price_b = get_increased_tower_price(game_state.cannon_price_b, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_single_priority_target(game_state, True)