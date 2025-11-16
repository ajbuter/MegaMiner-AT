import Constants
from Entity import Entity

class PlayerBase(Entity):
    def __init__(self, x: int, y: int, team_color: str) -> None:
        super().__init__(Constants.PLAYER_BASE_INITIAL_HEALTH, x, y)
        self.mercenary_queued_up : int = 0
        self.mercenary_queued_down : int = 0
        self.mercenary_queued_left : int = 0
        self.mercenary_queued_right : int = 0

        if team_color in ['r','b']:
            self.team = team_color
        else:
            raise Exception("Player base team_color must be 'r' or 'b'") # TF2 reference?
        
        self.name = "Red Player Base" if self.team == 'r' else "Blue Player Base"