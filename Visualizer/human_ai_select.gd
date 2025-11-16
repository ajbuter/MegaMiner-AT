extends Control

signal Go(ready : bool, ready2 : bool)
signal Back

@export var player_select_one : PlayerSelect
@export var player_select_two : PlayerSelect


func _on_back_pressed():
	Back.emit()

func _on_go_pressed(): # I love hard coding!
	var player1_ready : bool = player_select_one.line_edit.text != "" ##If the text is "" then you either havent picked a file or haven't selected a team name
	var player2_ready : bool = player_select_two.line_edit.text != ""
	
	# set map from option picker
	GameSettings.selected_map = "../maps/" + $"MapPicker".get_item_text($"MapPicker".get_selected_id()) + ".json"
	
	if player1_ready && player2_ready:
		Go.emit(player_select_one.is_AI, player_select_two.is_AI)
		
	else:
		# Check to see if either side has a problem and print both
		if !player1_ready:
			if player_select_one.is_AI:
				printerr("Player 1 doesn't have AI file selected!")
			else:
				printerr("Player 1 doesn't have team name selected!")
			
			if player_select_two.is_AI:
				printerr("Player 2 doesn't have AI file selected!")
			else:
				printerr("Player 2 doesn't have team name selected!")
