import Constants
import math
from PlayerBase import PlayerBase
from DemonSpawner import DemonSpawner

class GameState:
    def __init__(
        self,
        map_json_data: dict,
    ) -> None:

        # Initialization which is independent of the map JSON
        self.turns_remaining = Constants.MAX_TURNS
        self.victory = None
        # Human-readable reason why a team won
        self.victory_reason = ""
        self.money_r = Constants.INITIAL_MONEY
        self.money_b = Constants.INITIAL_MONEY
        self.mercs = []
        self.towers = []
        self.demons = []

        self.crossbow_price_b = Constants.CROSSBOW_BASE_PRICE
        self.cannon_price_b = Constants.CANNON_BASE_PRICE
        self.house_price_b = Constants.HOUSE_BASE_PRICE
        self.minigun_price_b = Constants.MINIGUN_BASE_PRICE
        self.church_price_b = Constants.CHURCH_BASE_PRICE
        
        self.crossbow_price_r = Constants.CROSSBOW_BASE_PRICE
        self.cannon_price_r = Constants.CANNON_BASE_PRICE
        self.house_price_r = Constants.HOUSE_BASE_PRICE
        self.minigun_price_r = Constants.MINIGUN_BASE_PRICE
        self.church_price_r = Constants.CHURCH_BASE_PRICE
        
        # Initialization which depends on the map JSON
        self.floor_tiles = map_json_data['FloorTiles']

        self.entity_grid = []
        for i in range(len(self.floor_tiles)):
            row = [None] * len(self.floor_tiles[0])
            self.entity_grid.append(row)

        self.player_base_r = PlayerBase(
            x=map_json_data["PlayerBaseR"]["x"],
            y=map_json_data["PlayerBaseR"]["y"],
            team_color='r'
        )
        self.player_base_b = PlayerBase(
            x=map_json_data["PlayerBaseB"]["x"],
            y=map_json_data["PlayerBaseB"]["y"],
            team_color='b'
        )

        self.demon_spawners = []
        for demon_spawner in map_json_data["DemonSpawners"]:
            self.demon_spawners.append(DemonSpawner(
                demon_spawner["x"],
                demon_spawner["y"],
                demon_spawner["initial_target"]
            ))

        # Compute mercenary paths, from Red to Blue player bases
        self.mercenary_path_left  = self.compute_mercenary_path((self.player_base_r.x-1, self.player_base_r.y), (self.player_base_r.x, self.player_base_r.y), (self.player_base_b.x, self.player_base_b.y))
        self.mercenary_path_right = self.compute_mercenary_path((self.player_base_r.x+1, self.player_base_r.y), (self.player_base_r.x, self.player_base_r.y), (self.player_base_b.x, self.player_base_b.y))
        self.mercenary_path_up    = self.compute_mercenary_path((self.player_base_r.x, self.player_base_r.y-1), (self.player_base_r.x, self.player_base_r.y), (self.player_base_b.x, self.player_base_b.y))
        self.mercenary_path_down  = self.compute_mercenary_path((self.player_base_r.x, self.player_base_r.y+1), (self.player_base_r.x, self.player_base_r.y), (self.player_base_b.x, self.player_base_b.y))


    def is_out_of_bounds(self, x: int, y: int) -> bool:
        return x < 0 or x >= len(self.floor_tiles[0]) or y < 0 or y >= len(self.floor_tiles)

    
    def compute_mercenary_path(self, start_point: tuple, red_base_location: tuple, blue_base_location: tuple) -> list:
        
        if self.is_out_of_bounds(start_point[0],start_point[1]): return None

        if self.floor_tiles[start_point[1]][start_point[0]] == 'O':
            # Do bastard DFS algorithm: raise exception if there's any branch in the path
            computed_path = [start_point]
            current_tile = start_point
            traversed = set()
            traversed.add(start_point)

            # Loop through new neighboring tiles until there are none left or a branch is detected
            while current_tile != None:
                # Find the next tile in the path
                for neighbor in [
                    (current_tile[0] - 1, current_tile[1]),
                    (current_tile[0] + 1, current_tile[1]),
                    (current_tile[0], current_tile[1] - 1),
                    (current_tile[0], current_tile[1] + 1)
                ]:
                    current_tile = None
                    if (neighbor not in traversed and
                        not self.is_out_of_bounds(neighbor[0], neighbor[1]) and
                        not neighbor == red_base_location and
                        not neighbor == blue_base_location and
                        self.floor_tiles[neighbor[1]][neighbor[0]] == 'O'):
                        traversed.add(neighbor)
                        if current_tile == None: current_tile = neighbor
                        else: raise Exception('Branching detected in mercenary path')
                        break # <- The for loop always sets current tile to none, thus always ending the while loop. So we break once we find the neighbor
                
                # Record the next tile
                if current_tile != None: # The last path will always be None, so we write this to exlude it
                    computed_path.append(current_tile)

            return computed_path # Forgot this line
        else:
            return None

    def is_game_over(self) -> bool:
        return self.turns_remaining <= 0 or self.victory != None