"""Artwork replacement preserves rig geometry, playback and transaction safety."""
import json
import pathlib
import sys
import tempfile
import unittest

from PIL import Image, ImageChops

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from rigtools.client import AgentClient, RigAPIError


class AssetReplacementContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        self.project = self.directory / 'character.rig2d'
        self.original = self.directory / 'original.png'
        self.replacement = self.directory / 'replacement.png'
        Image.new('RGBA', (20, 100), 'red').save(self.original)
        Image.new('RGBA', (100, 20), 'blue').save(self.replacement)
        recipe = self.directory / 'recipe.json'
        recipe.write_text(json.dumps({
            'schemaVersion': 1, 'duration': 2,
            'bones': [
                {'id': 'root', 'visible': False, 'length': 1},
                {'id': 'hand', 'parent': 'root', 'image': str(self.original),
                 'length': 60, 'width': 24, 'pivotX': 0.25, 'pivotY': 0.2,
                 'x': -35, 'y': -30, 'layer': 2},
                {'id': 'sleeve', 'parent': 'root', 'image': str(self.original),
                 'length': 35, 'width': 16, 'x': 60, 'layer': 1}],
            'frames': [{'time': 0, 'pose': {'hand': -25}},
                       {'time': 1, 'pose': {'hand': 35}},
                       {'time': 2, 'pose': {'hand': -25}}]}))
        self.client = AgentClient()
        self.client.request('apply_recipe', self.project, recipe=str(recipe))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def error(self, code, callback):
        with self.assertRaises(RigAPIError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code, caught.exception.response)

    def render(self, label, time):
        path = self.directory / f'{label}-{time}.png'
        self.client.request('render', self.project, time=time, output=str(path))
        with Image.open(path) as source:
            return source.convert('RGBA')

    def test_replacement_preserves_saved_rig_and_rendered_geometry(self):
        before = json.loads(self.project.read_text())
        poses = {time: self.render('before', time) for time in (0, 0.5, 1)}
        samples = {time: self.client.request('sample', self.project, time=time)['pose']
                   for time in poses}
        result = self.client.request('replace_image', self.project,
                                     bone='hand', image=str(self.replacement))
        after = json.loads(self.project.read_text())
        self.assertNotEqual(before['bones'][1]['image'], after['bones'][1]['image'])
        before['bones'][1]['image'] = after['bones'][1]['image']
        self.assertEqual(before, after)
        with AgentClient() as reopened:
            self.assertEqual(reopened.request('inspect', self.project)['revision'], result['revision'])
            self.assertTrue(reopened.request('validate', self.project)['valid'])
        for time, original in poses.items():
            changed = self.render('after', time)
            self.assertIsNone(ImageChops.difference(original.getchannel('A'), changed.getchannel('A')).getbbox())
            self.assertIsNotNone(ImageChops.difference(original.convert('RGB'), changed.convert('RGB')).getbbox())
            self.assertEqual(samples[time], self.client.request('sample', self.project, time=time)['pose'])
        self.assertIn('replace_image', self.client.request('capabilities')['commands'])
        self.assertTrue(self.client.request('capabilities')['assetReplacement'])

    def test_dry_run_and_invalid_images_leave_file_unchanged(self):
        original = self.project.read_bytes()
        self.client.request('replace_image', self.project, bone=1,
                            image=str(self.replacement), dry_run=True)
        self.assertEqual(self.project.read_bytes(), original)
        corrupt = self.directory / 'corrupt.png'
        corrupt.write_bytes(b'not an image')
        for image in (self.directory / 'missing.png', corrupt):
            self.error('asset_unreadable', lambda: self.client.request(
                'replace_image', self.project, bone='hand', image=str(image)))
            self.assertEqual(self.project.read_bytes(), original)
        self.error('unknown_bone', lambda: self.client.request(
            'replace_image', self.project, bone='missing', image=str(self.replacement)))
        self.assertEqual(self.project.read_bytes(), original)

    def test_batch_rolls_back_and_supports_dry_run(self):
        original = self.project.read_bytes()
        operation = {'command': 'replace_image', 'bone': 'hand', 'image': str(self.replacement)}
        self.client.request('batch', self.project, operations=[operation], dry_run=True)
        self.assertEqual(self.project.read_bytes(), original)
        self.error('unknown_bone', lambda: self.client.request('batch', self.project, operations=[
            operation, {'command': 'set_bone', 'bone': 'missing', 'values': {'angle': 50}}]))
        self.assertEqual(self.project.read_bytes(), original)
        self.client.request('batch', self.project, operations=[operation])
        self.assertNotEqual(self.project.read_bytes(), original)

    def test_sdk_pins_revision_and_rejects_stale_replacement(self):
        with AgentClient() as stale:
            stale.request('inspect', self.project)
            self.client.request('set_bone', self.project, bone='hand', values={'name': 'Updated hand'})
            original = self.project.read_bytes()
            self.error('revision_conflict', lambda: stale.request(
                'replace_image', self.project, bone='hand', image=str(self.replacement)))
            self.assertIn('expected_revision', stale.transcript[-1]['request'])
            self.assertEqual(self.project.read_bytes(), original)
        with AgentClient() as fresh:
            fresh.request('replace_image', self.project, bone='hand', image=str(self.replacement))
            self.assertEqual([item['request']['command'] for item in fresh.transcript], ['inspect', 'replace_image'])
            self.assertEqual(fresh.transcript[-1]['request']['expected_revision'],
                             fresh.transcript[0]['response']['result']['revision'])

    def test_import_image_still_fits_aspect_ratio(self):
        self.client.request('import_image', self.project, bone='hand', image=str(self.replacement))
        hand = self.client.request('inspect', self.project)['bones'][1]
        self.assertEqual(hand['width'], hand['length'] * 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
