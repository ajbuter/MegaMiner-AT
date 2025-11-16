extends Control

signal PlayGame

func _on_play_game_pressed():
	PlayGame.emit()


func _on_watch_replay_pressed():
	pass # Replace with function body.


func _on_quit_pressed():
	get_tree().quit()
