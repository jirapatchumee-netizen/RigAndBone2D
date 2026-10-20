"""Artwork can move in bone coordinates without changing the skeleton or animation."""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from rigtools.client import AgentClient, RigAPIError, ROOT


class ImageOffsetContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        self.project = self.directory / 'character.rig2d'
        self.recipe = self.directory / 'recipe.json'
        Image.new('RGBA', (20, 30), 'red').save(self.directory / 'marker.png')
        Image.new('RGBA', (10, 10), 'lime').save(self.directory / 'child.png')
        self.spec = {'schemaVersion': 1, 'duration': 1, 'bones': [
            {'id': 'root', 'visible': False, 'length': 1},
            {'id': 'marker', 'parent': 'root', 'image': 'marker.png',
             'length': 30, 'width': 20, 'pivotX': 0, 'pivotY': 0,
             'x': -40, 'y': -20, 'angle': 90},
            {'id': 'child', 'parent': 'marker', 'image': 'child.png',
             'length': 10, 'width': 10, 'pivotX': 0, 'pivotY': 0, 'x': 70}],
            'frames': [{'time': 0, 'pose': {}}, {'time': .5, 'pose': {'marker': 180}},
                       {'time': 1, 'pose': {}}]}
        self.recipe.write_text(json.dumps(self.spec))
        self.client = AgentClient()
        self.client.request('apply_recipe', self.project, recipe=str(self.recipe))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def render(self, name, time=0):
        path = self.directory / (name + '.png')
        self.client.request('render', self.project, time=time, output=str(path))
        with Image.open(path) as image:
            return image.convert('RGBA')

    def points(self, image, channel):
        return {(x, y) for y in range(image.height) for x in range(image.width)
                if image.getpixel((x, y))[channel] > 200
                and image.getpixel((x, y))[1-channel] < 20
                and image.getpixel((x, y))[3] > 200}

    def test_local_offsets_move_artwork_not_bones_or_children(self):
        before = json.loads(self.project.read_text())
        world = self.client.request('inspect', self.project)['worldBones']
        original = [self.render('before-' + str(t), t) for t in (0, .5)]
        samples = [self.client.request('sample', self.project, time=t)['pose'] for t in (0, .5)]
        self.client.request('set_bone', self.project, bone='marker',
                            values={'imageOffsetX': 12, 'imageOffsetY': -7})
        after = json.loads(self.project.read_text())
        for key in ('imageOffsetX', 'imageOffsetY'):
            after['bones'][1].pop(key)
        self.assertEqual(before, after)
        self.assertEqual(world, self.client.request('inspect', self.project)['worldBones'])
        for i, (t, delta) in enumerate(((0, (7, 12)), (.5, (-12, 7)))):
            moved = self.render('after-' + str(t), t)
            red = self.points(original[i], 0)
            self.assertTrue(red)
            self.assertEqual(self.points(moved, 0), {(x+delta[0], y+delta[1]) for x, y in red})
            self.assertEqual(self.points(original[i], 1), self.points(moved, 1))
            self.assertEqual(samples[i], self.client.request('sample', self.project, time=t)['pose'])
        with AgentClient() as reopened:
            marker = reopened.request('inspect', self.project)['bones'][1]
            self.assertEqual((marker['imageOffsetX'], marker['imageOffsetY']), (12, -7))
        self.client.request('export_sheet', self.project, output=str(self.directory / 'sheet.png'))
        with Image.open(self.directory / 'sheet.png') as sheet:
            self.assertEqual(sheet.crop((0, 0, 384, 384)).convert('RGBA').tobytes(),
                             self.render('same-pose').tobytes())

    def test_legacy_defaults_reset_and_replacement(self):
        baseline = self.render('legacy').tobytes()
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 0, 'imageOffsetY': 0})
        self.assertEqual(baseline, self.render('zero').tobytes())
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 12, 'imageOffsetY': -7})
        self.client.request('replace_image', self.project, bone='marker', image=str(self.directory / 'child.png'))
        marker = self.client.request('inspect', self.project)['bones'][1]
        self.assertEqual((marker['imageOffsetX'], marker['imageOffsetY']), (12, -7))
        self.client.request('replace_image', self.project, bone='marker', image=str(self.directory / 'marker.png'))
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 0, 'imageOffsetY': 0})
        self.assertEqual(baseline, self.render('reset').tobytes())

    def test_recipe_offsets_and_transaction_rejection(self):
        self.spec['bones'][1].update(imageOffsetX=12, imageOffsetY=-7)
        self.recipe.write_text(json.dumps(self.spec))
        other = self.directory / 'recipe-offset.rig2d'
        self.client.request('apply_recipe', other, recipe=str(self.recipe))
        info = self.client.request('inspect', other)
        self.assertEqual(info['bones'][1]['imageOffsetX'], 12)
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 12, 'imageOffsetY': -7})
        path = self.directory / 'recipe.png'
        self.client.request('render', other, time=0, output=str(path))
        with Image.open(path) as image:
            self.assertEqual(image.convert('RGBA').tobytes(), self.render('patched').tobytes())
        original = self.project.read_bytes()
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 99}, dry_run=True)
        self.assertEqual(original, self.project.read_bytes())
        for bad in ('bad', True, {'x': 1}):
            with self.assertRaises(RigAPIError):
                self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': bad})
            self.assertEqual(original, self.project.read_bytes())
        with self.assertRaises(RigAPIError):
            self.client.request('batch', self.project, operations=[
                {'command': 'set_bone', 'bone': 'marker', 'values': {'imageOffsetX': 99}},
                {'command': 'set_bone', 'bone': 'missing', 'values': {'imageOffsetY': 1}}])
        self.assertEqual(original, self.project.read_bytes())
        schema = self.client.request('get_schema')
        self.assertIn('imageOffsetY', schema['properties']['bones']['items']['properties'])

    @unittest.skipUnless(shutil.which('godot'), 'Godot not installed')
    def test_godot_preserves_sprite_offset_and_child_transform(self):
        from rigtools.godot import export_godot, run_godot
        self.client.request('set_bone', self.project, bone='marker', values={'imageOffsetX': 12, 'imageOffsetY': -7})
        config = self.directory / 'handoff.json'
        config.write_text(json.dumps({'schemaVersion': 1, 'id': 'offset', 'density': 1,
                                     'clips': [{'name': 'idle', 'start': 0, 'end': 1, 'loop': True}]}))
        game = self.directory / 'game'
        export_godot(self.client, self.project, config, game / 'generated')
        (game / 'project.godot').write_text('[application]\nconfig/name="Offsets"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        (game / 'verify.gd').write_text('''extends SceneTree
func _initialize():
    var visual = load('res://generated/visual.tscn').instantiate()
    var marker = visual.get_node('root/marker')
    assert(marker.get_node('Art').position.is_equal_approx(Vector2(12, -7)))
    assert(marker.position.is_equal_approx(Vector2(-40, -20)))
    assert(marker.get_node('child').position.is_equal_approx(Vector2(70, 0)))
    print('OFFSET_EXPORT_OK')
    visual.free()
    quit()
''')
        run_godot('godot', game, '--editor', '--import')
        self.assertIn('OFFSET_EXPORT_OK', run_godot('godot', game, '--script', 'verify.gd'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
