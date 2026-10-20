"""Layer ordering changes compositing while preserving the animated skeleton."""
import json
import pathlib
import sys
import tempfile
import unittest
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from rigtools.client import AgentClient, RigAPIError


class LayerOrderingContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        self.project = self.directory / 'layers.rig2d'
        for name, color in [('red', 'red'), ('blue', 'blue'), ('green', 'lime')]:
            Image.new('RGBA', (40, 40), color).save(self.directory / f'{name}.png')
        self.spec = {'schemaVersion': 1, 'duration': 1, 'bones': [
            {'id': 'root', 'visible': False, 'length': 1, 'layer': -20},
            {'id': 'back', 'parent': 'root', 'image': 'red.png', 'x': -10, 'y': -10,
             'length': 40, 'width': 40, 'pivotX': .5, 'pivotY': .5, 'layer': 1},
            {'id': 'front', 'parent': 'back', 'image': 'blue.png', 'x': 10, 'y': 10,
             'length': 40, 'width': 40, 'pivotX': .5, 'pivotY': .5, 'layer': 2},
            {'id': 'side', 'parent': 'root', 'image': 'green.png', 'x': 70,
             'length': 40, 'width': 40, 'pivotX': .5, 'pivotY': .5, 'layer': 2}],
            'frames': [{'time': 0, 'pose': {}}, {'time': .5, 'pose': {'back': 25, 'front': -10}},
                       {'time': 1, 'pose': {}}]}
        self.recipe = self.directory / 'recipe.json'
        self.recipe.write_text(json.dumps(self.spec))
        self.client = AgentClient()
        self.client.request('apply_recipe', self.project, recipe=str(self.recipe))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def render(self, label):
        path = self.directory / (label + '.png')
        self.client.request('render', self.project, time=0, output=str(path))
        with Image.open(path) as image:
            return image.convert('RGBA')

    def assert_order(self, order):
        bones = self.client.request('inspect', self.project)['bones']
        indices = sorted(range(len(bones)), key=lambda i: (bones[i]['layer'], i), reverse=True)
        self.assertEqual([bones[i]['id'] for i in indices], order)

    def test_front_to_back_order_preserves_all_other_project_data(self):
        original = json.loads(self.project.read_text())
        info = self.client.request('inspect', self.project)
        poses = {t: self.client.request('sample', self.project, time=t)['pose'] for t in (0, .25, .5, 1)}
        self.assertEqual(self.render('before').getpixel((192, 192)), (0, 0, 255, 255))
        order = ['back', 'front', 'side', 'root']
        self.client.request('reorder_layers', self.project, order=order)
        self.assert_order(order)
        after = json.loads(self.project.read_text())
        for bone in original['bones']:
            bone.pop('layer')
        for bone in after['bones']:
            bone.pop('layer')
        self.assertEqual(original, after)
        self.assertEqual(info['worldBones'], self.client.request('inspect', self.project)['worldBones'])
        self.assertEqual(self.render('after').getpixel((192, 192)), (255, 0, 0, 255))
        for t, pose in poses.items():
            self.assertEqual(pose, self.client.request('sample', self.project, time=t)['pose'])
        with AgentClient() as reopened:
            reopened.request('render', self.project, time=0, output=str(self.directory / 'reopened.png'))
        with Image.open(self.directory / 'reopened.png') as image:
            self.assertEqual(self.render('saved').tobytes(), image.convert('RGBA').tobytes())
        self.client.request('export_sheet', self.project, output=str(self.directory / 'sheet.png'))
        with Image.open(self.directory / 'sheet.png') as image:
            self.assertEqual(image.crop((0, 0, 384, 384)).convert('RGBA').tobytes(), self.render('first').tobytes())

    def test_invalid_order_and_batch_rollback_preserve_file(self):
        original = self.project.read_bytes()
        for order in ([], ['root'], ['root', 'back', 'front', 'front'],
                      ['root', 'back', 'front', 'missing'], 'bad', [0, 1, 2, True]):
            with self.assertRaises(RigAPIError):
                self.client.request('reorder_layers', self.project, order=order)
            self.assertEqual(original, self.project.read_bytes())
        self.client.request('reorder_layers', self.project, order=[1, 2, 3, 0], dry_run=True)
        self.assertEqual(original, self.project.read_bytes())
        with self.assertRaises(RigAPIError):
            self.client.request('batch', self.project, operations=[
                {'command': 'reorder_layers', 'order': [1, 2, 3, 0]},
                {'command': 'set_bone', 'bone': 'missing', 'values': {'angle': 1}}])
        self.assertEqual(original, self.project.read_bytes())
        self.client.request('batch', self.project, operations=[
            {'command': 'reorder_layers', 'order': [1, 2, 3, 0]}])
        self.assert_order(['back', 'front', 'side', 'root'])

    def test_sdk_stale_revision_rejection(self):
        with AgentClient() as stale:
            stale.request('inspect', self.project)
            self.client.request('set_bone', self.project, bone='side', values={'name': 'Renamed'})
            original = self.project.read_bytes()
            with self.assertRaises(RigAPIError) as caught:
                stale.request('reorder_layers', self.project, order=['back', 'front', 'side', 'root'])
            self.assertEqual(caught.exception.code, 'revision_conflict')
            self.assertIn('expected_revision', stale.transcript[-1]['request'])
            self.assertEqual(original, self.project.read_bytes())

    def test_legacy_indices_and_equal_layers(self):
        self.client.request('set_bone', self.project, bone='back', values={'layer': 2})
        self.assertEqual(self.render('tied').getpixel((192, 192)), (0, 0, 255, 255))
        original = json.loads(self.project.read_text())
        for bone in original['bones']:
            bone.pop('id')
        self.project.write_text(json.dumps(original))
        with AgentClient() as fresh:
            fresh.request('reorder_layers', self.project, order=[1, 2, 3, 0])
            self.assertTrue(fresh.request('validate', self.project)['valid'])
            self.assertEqual([b['id'] for b in fresh.request('inspect', self.project)['bones']],
                             ['bone-0', 'bone-1', 'bone-2', 'bone-3'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
