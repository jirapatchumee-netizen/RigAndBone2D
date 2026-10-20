"""Local JSONL SDK. No model/provider dependency, no implicit mutation retries."""
import json
import pathlib
import selectors
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
BINARY = ROOT / 'dist/RigAndBone2D.app/Contents/MacOS/RigAndBone2D'
MUTATIONS = {'set_bone', 'add_bone', 'delete_bone', 'reorder_layers', 'import_image', 'replace_image', 'keyframe', 'set_duration',
             'delete_keyframe', 'clear_keyframes', 'batch', 'apply_recipe'}

class RigAPIError(RuntimeError):
    def __init__(self, response):
        self.response = response
        self.code = response.get('error_code', 'transport_error')
        super().__init__(response.get('error', str(response)))

class AgentClient:
    def __init__(self, binary=BINARY, timeout=30):
        self.process = subprocess.Popen([str(binary), '--agent'], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, text=True, bufsize=1)
        self.timeout = timeout
        self.revisions = {}
        self.transcript = []
        self.sequence = 0
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def _request(self, command, project=None, **values):
        self.sequence += 1
        request = dict(id=f'sdk-{self.sequence}', command=command, **values)
        if project is not None:
            request['project'] = str(pathlib.Path(project).resolve())
        self.process.stdin.write(json.dumps(request, allow_nan=False) + '\n')
        self.process.stdin.flush()
        if not self.selector.select(self.timeout):
            self.process.terminate()
            raise RigAPIError({'error': 'Agent response timed out', 'error_code': 'transport_error'})
        line = self.process.stdout.readline()
        try:
            response = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise RigAPIError({'error': 'Invalid or missing JSONL response', 'error_code': 'transport_error'}) from exc
        self.transcript.append(dict(request=request, response=response))
        if response.get('id') != request['id']:
            raise RigAPIError({'error': 'Response ID mismatch', 'error_code': 'transport_error'})
        if not response.get('ok'):
            raise RigAPIError(response)
        result = response['result']
        if project is not None and 'revision' in result:
            self.revisions[request['project']] = result['revision']
        return result

    def request(self, command, project=None, **values):
        if project is not None:
            path = str(pathlib.Path(project).resolve())
            if command in MUTATIONS and pathlib.Path(path).exists() and 'expected_revision' not in values:
                if path not in self.revisions:
                    self._request('inspect', path)
                values['expected_revision'] = self.revisions[path]
        return self._request(command, project, **values)

    def save_transcript(self, path):
        pathlib.Path(path).write_text(json.dumps(self.transcript, indent=2) + '\n')

    def close(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.selector.close()
        self.process.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
