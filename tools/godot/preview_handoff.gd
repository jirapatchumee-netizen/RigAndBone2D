extends SceneTree
func _initialize(): call_deferred('capture')
func capture():
    root.size = Vector2i(960,540)
    var arena = load('res://gameplay/arena.tscn').instantiate()
    root.add_child(arena)
    arena.set_physics_process(false)
    arena.player.play('attack')
    arena.player.seek(1.3,true)
    for i in 5: await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png('res://../../scratch/godot-impact.png')
    quit()
