import Constants
from Tower import Tower
from GameState import GameState
from NameSelector import select_tower_name
from Utils import log_msg, get_increased_tower_price

class Church(Tower):
    def __init__(self, x: int, y: int, team_color: str, game_state: GameState):
        super().__init__(
            x, y,
            team_color,
            Constants.CHURCH_MAX_COOLDOWN,
            Constants.CHURCH_RANGE,
            Constants.MINIGUN_DAMAGE, # "I would be dangerous, I just don't FEEL like it!"
            game_state
        )

        self.angle = 0
        self.name = select_tower_name('CH', self.team)

    def get_price(self, game_state: GameState, team_color: str):
        return (game_state.church_price_r if team_color == "r" else game_state.church_price_b)

    def increase_price(self, game_state: GameState, team_color: str):
        if team_color == "r":
            game_state.church_price_r = get_increased_tower_price(game_state.church_price_r, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
        else:
            game_state.church_price_b = get_increased_tower_price(game_state.church_price_b, Constants.TOWER_PRICE_PERCENT_INCREASE_PER_BUY)
    
    def update(self, game_state):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            self.tower_activation(game_state)
    
    def tower_activation(self, game_state : GameState):
        if self.team == "r":
            super().buff_nearby_targets(game_state)
            log_msg(f'Church {self.name} buffed mercs for the Red team.')
        elif self.team == "b":
            super().buff_nearby_targets(game_state)
            log_msg(f'Church {self.name} buffed mercs for the Blue team.')