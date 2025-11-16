extends TextureRect

var time = 0

func _process(delta: float) -> void:
	rotation += 1 * delta
	
	time += 1 * delta
	if time > TAU:
		time = 0
	
	scale = Vector2(1 + 0.25 * abs(sin(time)),1 + 0.25 * abs(sin(time)))
