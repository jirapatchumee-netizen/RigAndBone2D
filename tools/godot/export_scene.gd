extends SceneTree

func _initialize():
    var data = JSON.parse_string(FileAccess.get_file_as_string('res://payload.json'))
    var visual = Node2D.new()
    visual.name = 'Visual'
    visual.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
    var atlas = load('res://character/atlas.png')
    var nodes = {}
    var paths = {}
    for b in data.bones:
        var node = Node2D.new()
        node.name = b.id
        var parent = visual if b.parent == null else nodes[b.parent]
        parent.add_child(node)
        node.owner = visual
        node.position = Vector2(b.x, b.y)
        node.rotation = deg_to_rad(b.angle)
        nodes[b.id] = node
        paths[b.id] = str(visual.get_path_to(node))
        if b.has('art'):
            var art = b.art
            var sprite = Sprite2D.new()
            sprite.name = 'Art'
            var texture = AtlasTexture.new()
            texture.atlas = atlas
            texture.region = Rect2(art.region[0], art.region[1], art.region[2], art.region[3])
            texture.filter_clip = true
            sprite.texture = texture
            sprite.centered = false
            sprite.flip_h = art.mirror
            sprite.position = Vector2(art.offset[0], art.offset[1])
            sprite.scale = Vector2(art.size[0]/art.region[2], art.size[1]/art.region[3])
            sprite.z_as_relative = false
            sprite.z_index = b.drawOrder
            node.add_child(sprite)
            sprite.owner = visual
    var player = AnimationPlayer.new()
    player.name = 'AnimationPlayer'
    visual.add_child(player)
    player.owner = visual
    var library = AnimationLibrary.new()
    for clip in data.clips:
        var animation = Animation.new()
        animation.length = clip.length
        animation.loop_mode = Animation.LOOP_LINEAR if clip.loop else Animation.LOOP_NONE
        for i in data.bones.size():
            var values = []
            for pose in clip.poses: values.append(pose[i])
            var constant = true
            for value in values:
                if abs(value-values[0])>0.000001: constant=false
            var track = animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(track, NodePath(paths[data.bones[i].id]+':rotation'))
            animation.track_set_interpolation_loop_wrap(track, false)
            animation.value_track_set_update_mode(track, Animation.UPDATE_CONTINUOUS)
            # Every bone gets a starting key so switching clips resets the full pose.
            for k in values.size():
                if not constant or k==0:
                    animation.track_insert_key(track, clip.times[k], deg_to_rad(values[k]))
        for event in clip.events: animation.add_marker(event.name, event.time)
        library.add_animation(clip.name, animation)
    player.add_animation_library('', library)
    var socket_paths = {}
    for socket in data.sockets: socket_paths[socket] = paths[data.sockets[socket]]
    visual.set_meta('sockets', socket_paths)
    var packed = PackedScene.new()
    if packed.pack(visual)!=OK or ResourceSaver.save(packed,'res://character/visual.tscn')!=OK:
        quit(1)
        return
    visual.free()
    quit(0)
