extends OptionButton

func _ready():
	var map_files = DirAccess.get_files_at("../maps")
	for file: String in map_files:
		self.add_item(file.substr(0, file.length() - 5))
