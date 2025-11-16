import sys
import math

def clamp(x, min_x, max_x):
    return min(max(x, min_x), max_x)

def log_msg(msg: str):
    print(msg, file=sys.stderr)

def get_increased_tower_price(current_price, percent_increase: int) -> int:
    return math.floor((1 + 0.01* percent_increase) * current_price)