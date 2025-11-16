# For conveniently distinguishing different mercs/demons in the logs 

index_r  = 0
index_b  = 0
index_d  = 0
index_tr = 0
index_tb = 0

merc_name_table_red = ["Rodney", "Robert", "Ryan", "Raulston", "Russell", "Ronald", "Roger", "Roland", "Ralph", "Raymond", "Ricky", "Reuben", "Rafael", "Randy", "Rocco", "Raul", "Rory", "Rex", "Ruben", "Rhys", "Ronan", "Ross", "Roman", "Remy", "Reed", "Ramsey", "Rudy", "Rylan", "Rishi", "Rainer", "Ronin", "Rafe", "Ryker", "Ray", "Rick", "Raj", "Raiden", "Reese", "Rami", "River", "Roderick", "Roosevelt", "Roland", "Rashad", "Ridley", "Raulito", "Roscoe", "Rafferty", "Renzo", "Rowan"]

merc_name_table_blue = ["Ben", "Boole", "Billy", "Benson", "Bradley", "Brayden", "Brent", "Brett", "Brody", "Brock", "Bruce", "Barry", "Bobby", "Bryan", "Brady", "Bill", "Bob", "Blaine", "Blake", "Basil", "Beau", "Barrett", "Brodie", "Bo", "Benedict", "Boris", "Byron", "Baxter", "Bowie", "Bennett", "Bryce", "Benton", "Benedek", "Blaise", "Branson", "Benedictus", "Bingham", "Bodie", "Bram", "Briar", "Blair", "Buster", "Bishop", "Boden", "Bernard", "Boris", "Benny", "Baldwin", "Barney", "Benedetto", "Basilio"]

demon_name_table = ["Doyle", "Drake", "Donald", "Dorian", "Dylan", "Douglas", "Dean", "Dennis", "Darren", "Damon", "Dale", "Desmond", "Drew", "Davis", "Derrick", "Dustin", "Devin", "Dominic", "Diego", "Dexter", "Damian", "Declan", "Dario", "Dane", "Donovan", "Dimitri", "Darrell", "Darnell", "Daniel", "Derrick", "Dash", "Duncan", "Dallas", "Dario", "Dorian", "Deacon", "Darren", "Dayton", "Dirk", "Dewey", "Dax", "Dilan", "Dmitri", "Darryl", "Dominick", "Deshaun", "Domenico", "Dario", "Deandre", "Dion", "Darwin"]

red_tower_name_table = ["Optimus", "Wheeljack", "BumbleBee", "Tonnenman", "Holdsworth", "Cliffjumper", "Prowl", "Jazz", "Sideswipe", "Ratchet", "Ironhide", "Hound", "Mirage", "Trailbreaker", "Sunstreaker", "Bluestreak", "Windcharger", "Brawn", "Huffer", "Gears", "Skyfire", "Grimlock", "Slag", "Sludge", "Snarl", "Swoop", "Warpath", "Tracks", "Grapple", "Blaster", "Red Alert", "Smokescreen", "Perceptor", "Seaspray", "Hoist", "Powerglide", "Beachcomber", "Inferno", "Cosmos", "Omega", "Devcon", "Skids", "Alpha", "Silverbolt", "Air Raid", "Slingshot", "Skydive", "Fireflight", "Superion", "Streetwise"]

blue_tower_name_table = ["Megatron", "Galvatron", "Skywarp", "Starscream", "Thundercracker", "Soundwave", "Shockwave", "Reflector", "Shrapnel", "Bombshell", "Kiclback", "Hook", "Scrapper", "Bonecrusher", "Long Haul", "Scavenger", "Mixmaster", "Devastator", "Thrust", "Blitzwing", "Dirge", "Astrotrain", "Motormaster", "Drag Strip", "Dead End", "Breakdown", "Wildrider", "Menasor", "Brawl", "Swindle", "Blastoff", "Vortex", "Onslaught", "Bruticus", "Cyclonus", "Scourge", "Octane", "Trypticon", "Rampage", "Headstrong", "Razorclaw", "Divebomb", "Predaking", "Runamuck", "Runabout", "Ripper", "Blot", "Cutthroat", "Abominus", "Skullcruncher"]

def select_merc_name(team_color: str) -> str:
    global index_r, index_b
    if team_color == 'r':
        name = merc_name_table_red[index_r]
        index_r = (index_r + 1) % len(merc_name_table_red)
        return name
    elif team_color == 'b':
        name = merc_name_table_blue[index_b]
        index_b = (index_b + 1) % len(merc_name_table_blue)
        return name

def select_demon_name() -> str:
    global index_d
    name = demon_name_table[index_d]
    index_d = (index_d + 1) % len(demon_name_table)
    return name

# tower char should be a short string indicating the type of tower
def select_tower_name(tower_type: str, team_color: str) -> str:
    global index_tr, index_tb
    
    if team_color == 'r':
        name = f'R_{tower_type}_{red_tower_name_table[index_tr]}'
        index_tr = (index_tr + 1) % len(red_tower_name_table)
        return name
    elif team_color == 'b':
        name = f'B_{tower_type}_{blue_tower_name_table[index_tb]}'
        index_tb = (index_tb + 1) % len(blue_tower_name_table)
        return name