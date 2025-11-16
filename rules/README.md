# Rules

## The Basics
ApocaWarlords is a 2-player tile-based turn-based competitive tower defense game. Think of it as a mix between Clash Royale and Bloons TD Battles. Each player has a Base, which looks like a castle. The objective of the game is for your Base to survive longer than your opponent's ( or equivalently, to DESTROY your opponent's Base ).

"How do I survive?" you're probably asking. Well, as this is a tower defense game, you'll be building Towers to defend your Base. "Defend against what?", you ask? Well, that would be the hired *goons* of your enemy, the Mercenaries. ( Don't worry: you can hire *goons* yourself! ) Oh, and you will also be defending against the endless horde of Demons which are constantly spawning and becoming progressively stronger, until they completely outscale your available space to place defenses! Look on the bright side though, Demons will also be outscaling your enemy.

Defenses and Mercenaries don't come cheap, though. You will need to make money by placing a special type of Tower, the House. If you've ever played Plants vs. Zombies, these are kind of like sunflowers in that game. Be careful not to build too many Houses, though. **With each Tower you build, towers of that type will become 25% more expensive ( rounded down )**.

## Main Game Loop
ApocaWarlords uses *simultaneous turns*. This means that each turn, both players select their actions at the same time, without communication. After both players select their actions, the game world is updated. This repeats until the game ends.

## Players
There are two players, the Red player, and the Blue player. Each player has corresponding:
- Towers
- Mercenaries
- Player Base
- Territory Tiles
- Money

## Player Action
Every turn, each player can decide to do any combination of the following, assuming the decision is valid (more on validity below):
1. Buy a Mercenary
2. Build *or* Destroy a Tower, but not both!
3. Provoke the Demons

An invalid action will cause the player who made it to lose their turn ( they will do nothing ).

### Buying Mercenaries
When either player buys a Mercenary, they must decide which direction the Mercenary starts out from. Mercenaries cost $10.

Depending on the map, different directions will be available. For all maps, there will be at least 2 Mercenary starting directions available per player, and at most 4. Maps are symmetric as to make them fair, so both players will always have the same amount of directions to choose from.

A purchase is valid if the following two conditions hold:
1. There is a Path Tile 1 unit away from the purchasing player's base in the direction which was selected. ( Mercenaries can only walk on path tiles )
2. The purchasing player has $10.

A valid Mercenary purchase will cause $10 to be subtracted from the purchasing player's total money and cause a Mercenary to immediately spawn in the direction selected. Buying Mercenaries happens before buying Towers and before provoking the Demons, so it is possible for a Mercenary purchase to make a player too poor to finish everything they decided to do in a single turn.

### Building/Destroying Towers
When either player builds a Tower, they must decide what type of tower to build and where to build it. Each Tower type has a base price, and **the price of each type of Tower increases by 25% for each one purchased, rounded down, per player**. So, for example, the first House purchased by the Red player will cost $10, then the second will cost $12. This price increase from $10 to $12 would only effect the Red player, since it was Red who did the buying.

Players must build towers on Territory Tiles corresponding to their own team. The layout of Territory Tiles will be different per map. The layout of Territory Tiles is symmetric as to make the game fair. However, there is no restriction as to where on the map these tiles need to be ( expect some crazy maps ).

A Tower build action is valid if the following three conditions hold:
1. The selected bulid location is a Territory Tile belonging to the player building the tower
2. The player has enough money to build the tower
3. There is no Tower already bulit at the selected location

A valid Tower build action will cause the price of the tower to be subtracted from the building player's total money and cause a Tower to spawn immediately. Towers must wait their full cooldown duration after being first built before they can activate. Building Towers happens after Mercenary purchases, but before the chance to provoke the Demons.

When either player destroys a Tower, they must specify where the tower they want to destroy is. **the base price of the Tower will be refunded**. Destroying a tower does not decrease its price.

### Provoking the Demons
Each turn, both players have the chance to provoke the demons. This costs $5, processed after buying mercenaries.

If both players provoke, all Demons are immediately destroyed.

If only one player provokes, all demon spawners will spawn an extra demon (added to their spawn queue).

## World Update

### Mercenary Turn
After both players decide their action, all mercenaries on the board will do one of three actions: move, fight, or wait. 
A mercenary will choose to move if the two path tiles in front of it are empty. The mercenary will then move forward one path tile.
A mercenary will chose to fight if a demon, rival mercenary, or player base blocks either of the next two path tiles. The mercenary will then deal damage to entity blocking its path.
If a mercenary's path is blocked by a friendly mercenary, it will choose to wait, not performing any action.

After all merceneraries have acted, all mercenaries and demons on the board with 0 or less Health will be removed from the game.

By default, mercenaries deal 15 damage and have 20 health.

### Demon Turn
After the Mercenary Turn, all demons on the board will choose to either move forward or attack. A demon chooses to move forward if the two path tiles in front of it are empty. If a mercenary, player base, or another demon block the path, the demon will deal damage to them.

After all demons have acted, all mercenaries and demons on the board with 0 or less Health will be removed from the game.

### Mercenary Spawning
Queued mercenaries spawn after the Mercenaries and Demons have their turn.

### Demon Spawning
Every 10 rounds, all demon spawners on the map add a Demon to their spawn queue. Demons leave the spawn queue immediately if there is no Mercenary or Demon blocking the spawner. Otherwise, they bide their time... 

## Towers
After the Demon Turn, each tower placed on the board will perform an update. 
If a tower updates when its cooldown is equal to 0, it will "activate" and reset its cooldown; The effect that occurs when the tower activates depends on the type of tower (see below). 
If the tower updates when its cooldown is greater than 0, it will reduce the cooldown by 1 and do nothing else.

### House
- Cooldown: 5 turns
- Base Price: $10
- Money Produced Per Activation: $12

### Cannon
- Cooldown: 5 turns
- Base Price: $10
- Range (Circular): 3
- Damage: 5

Special: On hit, does 5 splash damage to Mercenaries/Demons adjacent.

### Crossbow
- Cooldown: 4 turns
- Base Price: $8
- Range (Circular): 5
- Damage: 4

### Minigun
- Cooldown: No Cooldown!
- Base Price: $20
- Range (Circular): 3
- Damage: 2

### Church
- Cooldown: 10 turns
- Base Price: $15
- Range (Circular): 3

Buffs all Mercenaries in range on activation. Buffed Mercs get an extra 10 health and deal an extra 10 damage. Buffs stack.


## Win Conditions
The most standard way to win the game is by one players dealing 200 damage to the rival players's base, thereby destroying it. However, if both players's bases are still standing by turn 300, the game ends via timeout and the winner is determined by the following series of checks, in order of priority:

1. If no base has been destroyed, the player with the most money wins.
2. If both players have the same amount of money, the player with the most towers wins.
3. If both players have the same amount of towers, the player who spent the most on towers wins.
4. If both players have spent the same amount, the player with the most mercenaries wins.
5. If both players have the same amount of mercenaries, the player with the highest sum of mercenary health wins.
6. If both players have the same sum of mercenary health, the game is declared a tie.