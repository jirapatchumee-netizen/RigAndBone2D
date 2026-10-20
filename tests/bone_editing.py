"""Adding and deleting bones preserves the rest of the animated hierarchy."""
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from rigtools.client import AgentClient, RigAPIError


class BoneEditingContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        self.project = self.directory / 'character.rig2d'
        recipe = self.directory / 'recipe.json'
        recipe.write_text(json.dumps({'schemaVersion': 1, 'duration': 2, 'bones': [
            {'id': 'root', 'visible': False, 'length': 1},
            {'id': 'arm', 'parent': 'root', 'x': -30, 'angle': 15},
            {'id': 'leg', 'parent': 'root', 'x': 30, 'angle': -10},
            {'id': 'hand', 'parent': 'arm', 'y': 40, 'angle': 25},
            {'id': 'foot', 'parent': 'leg', 'y': 45, 'angle': -20}],
            'frames': [{'time': 0, 'label': 'start', 'pose': {}},
                       {'time': 1, 'label': 'middle', 'pose': {'arm': 35, 'leg': -30, 'foot': 10}},
                       {'time': 2, 'label': 'end', 'pose': {}}]}))
        self.client = AgentClient()
        self.client.request('apply_recipe', self.project, recipe=str(recipe))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def error(self, code, **args):
        original = self.project.read_bytes()
        with self.assertRaises(RigAPIError) as caught:
            self.client.request('delete_bone', self.project, **args)
        self.assertEqual(code, caught.exception.code)
        self.assertEqual(original, self.project.read_bytes())

    def test_add_leaf_then_delete_restores_original(self):
        original = json.loads(self.project.read_text())
        added = self.client.request('add_bone', self.project, bone='arm', name='New part')
        identifier = added['boneIDs'][-1]
        self.assertNotIn(identifier, {b['id'] for b in original['bones']})
        info = self.client.request('inspect', self.project)
        self.assertEqual(info['bones'][-1]['parent'], 1)
        for old, frame in zip(original['frames'], info['frames']):
            self.assertEqual(old['angles'] + [0], frame['angles'])
        self.client.request('delete_bone', self.project, bone=identifier)
        self.assertEqual(original, json.loads(self.project.read_text()))

    def test_subtree_deletion_preserves_remaining_world_poses_and_frames(self):
        old = self.client.request('inspect', self.project)
        samples = {t: self.client.request('sample', self.project, time=t)['pose'] for t in (0, .5, 1, 2)}
        self.client.request('delete_bone', self.project, bone='arm', include_descendants=True)
        new = self.client.request('inspect', self.project)
        self.assertEqual([b['id'] for b in new['bones']], ['root', 'leg', 'foot'])
        self.assertEqual([b.get('parent') for b in new['bones']], [None, 0, 1])
        self.assertEqual(new['worldBones'], [dict(b, index=i) for i, b in enumerate(old['worldBones'][j] for j in (0, 2, 4))])
        for previous, current in zip(old['frames'], new['frames']):
            self.assertEqual(current['angles'], [previous['angles'][i] for i in (0, 2, 4)])
            self.assertEqual(current['time'], previous['time'])
            self.assertEqual(current['label'], previous['label'])
        for t, pose in samples.items():
            self.assertEqual({k: v for k, v in pose.items() if k not in {'arm', 'hand'}},
                             self.client.request('sample', self.project, time=t)['pose'])
        self.assertTrue(self.client.request('validate', self.project)['valid'])
        with AgentClient() as reopened:
            self.assertEqual([b['id'] for b in reopened.request('inspect', self.project)['bones']],
                             ['root', 'leg', 'foot'])

    def test_guards_dry_run_and_batch_rollback(self):
        self.error('bone_has_children', bone='arm')
        self.error('invalid_request', bone='root', include_descendants=True)
        self.error('invalid_request', bone='hand', include_descendants='true')
        self.error('unknown_bone', bone='missing')
        original = self.project.read_bytes()
        self.client.request('delete_bone', self.project, bone='arm', include_descendants=True, dry_run=True)
        self.assertEqual(original, self.project.read_bytes())
        with self.assertRaises(RigAPIError):
            self.client.request('batch', self.project, operations=[
                {'command': 'delete_bone', 'bone': 'arm', 'include_descendants': True},
                {'command': 'set_bone', 'bone': 'hand', 'values': {'angle': 10}}])
        self.assertEqual(original, self.project.read_bytes())
        for flag in (1, 'true'):
            with self.assertRaises(RigAPIError):
                self.client.request('batch', self.project, operations=[
                    {'command': 'delete_bone', 'bone': 'hand', 'include_descendants': flag}])
            self.assertEqual(original, self.project.read_bytes())

    def test_sdk_rejects_stale_deletion(self):
        with AgentClient() as stale:
            stale.request('inspect', self.project)
            self.client.request('set_bone', self.project, bone='hand', values={'name': 'Updated'})
            original = self.project.read_bytes()
            with self.assertRaises(RigAPIError) as caught:
                stale.request('delete_bone', self.project, bone='hand')
            self.assertEqual(caught.exception.code, 'revision_conflict')
            self.assertIn('expected_revision', stale.transcript[-1]['request'])
            self.assertEqual(original, self.project.read_bytes())

    def test_malformed_keyframe_before_deletion_returns_error_and_keeps_process_alive(self):
        original = self.project.read_bytes()
        for dry_run in (False, True):
            with self.assertRaises(RigAPIError) as caught:
                self.client.request('batch', self.project, dry_run=dry_run, operations=[
                    {'command': 'keyframe', 'time': 0, 'angles': []},
                    {'command': 'delete_bone', 'bone': 'hand'}])
            self.assertEqual(caught.exception.code, 'validation_failed')
            self.assertEqual(original, self.project.read_bytes())
            self.assertTrue(self.client.request('validate', self.project)['valid'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
