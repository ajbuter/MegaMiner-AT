import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name
from Utils import get_increased_tower_price

class Minigun(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState) -> None:
        super().__init__(
            x, y,
            team_color,
            Constants.MINIGUN_MAX_COOLDOWN,
            Constants.MINIGUN_RANGE,
            Constants.MINIGUN_DAMAGE,
            game_state
        )

    def get_price(self, game_state: GameState, team_color: str):
        return (game_state.minigun_price_r if team_color == "r" else game_state.minigun_price_b)

    def increase_price(self, game_state: GameState, team_color: str):
        if team_color == "r":
            game_state.minigun_price_r = get_increased_tower_price(game_state.minigun_price_r, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
        else:
            game_state.minigun_price_b = get_increased_tower_price(game_state.minigun_price_b, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
        self.name = select_tower_name('M',self.team)
    
    def tower_activation(self, game_state: GameState):
        super().shoot_all_targets_in_range(game_state)