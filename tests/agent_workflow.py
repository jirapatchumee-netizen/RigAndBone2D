"""Integration contracts for declarative builds and safe reusable authoring."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from rigtools.client import AgentClient, RigAPIError

class WorkflowContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = pathlib.Path(self.temp.name)
        self.project = self.directory/'rig.rig2d'
        self.recipe = self.directory/'recipe.json'
        # Child precedes parent intentionally; API compiles the hierarchy.
        self.spec = {'schemaVersion':1,'duration':2,'bones':[
            {'id':'arm','parent':'root','length':20,'angle':10},
            {'id':'root','visible':False,'length':1}],
            'frames':[{'time':0,'pose':{}},{'time':2,'pose':{}}]}
        self.recipe.write_text(json.dumps(self.spec))
        self.client = AgentClient()
    def tearDown(self):
        self.client.close()
        self.temp.cleanup()
    def build(self, **values):
        return self.client.request('apply_recipe', self.project, recipe=str(self.recipe), **values)
    def error(self, code, callback):
        with self.assertRaises(RigAPIError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code, caught.exception.response)
    def test_empty_preset_has_no_demo_frames(self):
        result = self.client.request('new',self.project,preset='empty')
        self.assertEqual(result['boneIDs'], ['root'])
        self.assertEqual(result['keyframes'], 0)
    def test_named_hierarchy_and_pose(self):
        built = self.build()
        self.assertEqual(built['boneIDs'], ['root','arm'])
        self.assertEqual(built['keyframes'], 2)
        result = self.client.request('batch',self.project,operations=[
            {'command':'set_bone','bone':'arm','values':{'angle':40}},
            {'command':'keyframe','time':1,'pose':{'arm':55}}])
        self.assertNotEqual(result['revision'],built['revision'])
        self.assertEqual(self.client.request('sample',self.project,time=1)['pose']['arm'],55)
    def test_dry_run_and_replacement(self):
        self.assertTrue(self.build(dry_run=True)['dryRun'])
        self.assertFalse(self.project.exists())
        self.build(); original=self.project.read_bytes()
        self.error('replacement_required',lambda:self.build())
        self.assertEqual(self.project.read_bytes(), original)
        self.spec['bones'][0]['angle']=25;self.recipe.write_text(json.dumps(self.spec))
        self.build(replace=True,dry_run=True)
        self.assertEqual(self.project.read_bytes(),original)
        self.build(replace=True)
        self.assertNotEqual(self.project.read_bytes(),original)
    def test_batch_rollback_and_recovery(self):
        self.build(); original=self.project.read_bytes()
        self.error('unknown_bone',lambda:self.client.request('batch',self.project,operations=[
            {'command':'set_bone','bone':'arm','values':{'angle':90}},
            {'command':'set_bone','bone':'missing','values':{'angle':1}}]))
        self.assertEqual(self.project.read_bytes(),original)
        self.assertTrue(self.client.request('validate',self.project)['valid'])
    def test_batch_validates_final_model(self):
        self.build(); original=self.project.read_bytes()
        self.error('validation_failed',lambda:self.client.request('batch',self.project,operations=[
            {'command':'set_bone','bone':'arm','values':{'angle':30}},
            {'command':'keyframe','time':1,'angles':[0]}]))
        self.assertEqual(self.project.read_bytes(),original)
    def test_batch_dry_run_does_not_write(self):
        self.build();original=self.project.read_bytes()
        self.client.request('batch',self.project,dry_run=True,operations=[
            {'command':'clear_keyframes'}, {'command':'keyframe','time':0,'pose':{'arm':12}}])
        self.assertEqual(self.project.read_bytes(),original)
    def test_cycle_and_missing_asset_do_not_create_project(self):
        self.spec['bones'][1]['parent']='arm';self.recipe.write_text(json.dumps(self.spec))
        self.error('hierarchy_cycle',lambda:self.build())
        self.assertFalse(self.project.exists())
        self.spec['bones'][1].pop('parent');self.spec['bones'][0]['image']='missing.png'
        self.recipe.write_text(json.dumps(self.spec))
        self.error('asset_unreadable',lambda:self.build())
        self.assertFalse(self.project.exists())
    def test_unknown_fields_and_duplicate_ids(self):
        self.spec['bones'][0]['angel']=20;self.recipe.write_text(json.dumps(self.spec))
        self.error('invalid_recipe',lambda:self.build())
        self.spec['bones'][0].pop('angel');self.spec['bones'][0]['id']='root'
        self.recipe.write_text(json.dumps(self.spec))
        self.error('duplicate_id',lambda:self.build())
    def test_duplicate_times_rejected(self):
        self.spec['frames'][1]['time']=0;self.recipe.write_text(json.dumps(self.spec))
        self.error('duplicate_time',lambda:self.build())
    def test_immutable_ids_and_malformed_pose(self):
        self.build()
        self.error('invalid_request',lambda:self.client.request('set_bone',self.project,bone='arm',values={'id':'other'}))
        self.error('invalid_request',lambda:self.client.request('keyframe',self.project,time=1,angles='bad'))
        self.error('invalid_request',lambda:self.client.request('keyframe',self.project,time=True))
    def test_boolean_flags_cannot_accidentally_write(self):
        self.error('invalid_request',lambda:self.build(dry_run='true'))
        self.assertFalse(self.project.exists())
        self.build();original=self.project.read_bytes()
        self.error('invalid_request',lambda:self.client.request('set_bone',self.project,bone='arm',values={'angle':80},expected_revision=123))
        self.assertEqual(self.project.read_bytes(),original)
    def test_keyframe_cleanup(self):
        self.build()
        self.client.request('keyframe',self.project,time=1,pose={'arm':50})
        self.assertEqual(self.client.request('delete_keyframe',self.project,time=1)['keyframes'],2)
        self.assertEqual(self.client.request('clear_keyframes',self.project)['keyframes'],0)
    def test_concurrent_writers_detect_conflict(self):
        revision=self.build()['revision']
        def write(angle):
            with AgentClient() as client:
                try:
                    client.request('set_bone',self.project,bone='arm',values={'angle':angle},expected_revision=revision)
                    return 'ok'
                except RigAPIError as error:
                    return error.code
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(write,[20,30]))
        self.assertEqual(sorted(results),['ok','revision_conflict'])
    def test_output_cannot_destroy_project(self):
        self.build();original=self.project.read_bytes()
        self.error('invalid_request',lambda:self.client.request('render',self.project,output=str(self.project)))
        self.assertEqual(self.project.read_bytes(),original)
    def test_legacy_file_keeps_ids_after_edit(self):
        self.client.request('new',self.project)
        raw=json.loads(self.project.read_text())
        for bone in raw['bones']:bone.pop('id',None)
        self.project.write_text(json.dumps(raw))
        info=self.client.request('inspect',self.project)
        self.assertEqual(info['bones'][5]['id'],'bone-5')
        self.client.request('set_bone',self.project,bone='bone-5',values={'name':'Renamed'})
        info=self.client.request('inspect',self.project)
        self.assertEqual(info['bones'][5]['id'],'bone-5')

if __name__ == '__main__':
    unittest.main(verbosity=2)
