extends SceneTree

func _initialize():
    call_deferred('verify')

func verify():
    var arena = load('res://gameplay/arena.tscn').instantiate()
    root.add_child(arena)
    await physics_frame
    var other = arena.CHARACTER.instantiate()
    root.add_child(other)
    var path = 'root/torso/determined-head/Art'
    assert(arena.visual.get_node(path).texture.atlas == other.get_node(path).texture.atlas, 'Atlas must be shared between instances')
    assert(arena.visual.get_node_or_null('training-dummy-stand')==null)
    var arguments = OS.get_cmdline_user_args()
    if arguments.size()>0:
        var expected = JSON.parse_string(FileAccess.get_file_as_string(arguments[0]))
        for sample in expected:
            arena.player.play('attack')
            arena.player.seek(sample.time,true)
            for id in sample.bones:
                var node = arena.visual.find_child(id,true,false)
                var value = sample.bones[id]
                var point = node.global_position-arena.actor.global_position
                assert(point.distance_to(Vector2(value[0],value[1]))<0.001, 'World position mismatch: '+id)
                assert(abs(wrapf(node.global_rotation-value[2],-PI,PI))<0.0001, 'World rotation mismatch: '+id)
    arena.attack()
    for i in 210: await physics_frame
    assert(arena.damage_count==1, 'Attack must damage target exactly once')
    assert(arena.hp==90)
    assert(not arena.attacking)
    arena.actor.position.x=120
    arena.attack()
    for i in 210: await physics_frame
    assert(arena.damage_count==1, 'Out-of-range attack must miss')
    print(JSON.stringify({'ok':true,'sharedAtlas':true,'hits':arena.damage_count,'hp':arena.hp,'missVerified':true}))
    other.queue_free()
    arena.queue_free()
    quit(0)
