// Pinned runtime. User programs run in a worker, never on a server.
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
let runtime;
self.onmessage=async({data})=>{try{if(!runtime){runtime=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/'});}self.postMessage({type:'ready'});runtime.globals.set('_payload_json',JSON.stringify(data));let result=await runtime.runPythonAsync(`
import json, io, contextlib, traceback, builtins, copy
_payload = json.loads(_payload_json)
class LimitedOutput(io.StringIO):
    def write(self, value):
        if self.tell() + len(value) > 20000: raise RuntimeError('Output limit reached (20,000 characters).')
        return super().write(value)
_output = LimitedOutput()
_error = None
_results = []
_ns = {'__name__': '__main__'}
_input_lines = iter(_payload.get('stdin','').splitlines())
def _input(prompt=''):
    print(prompt, end='')
    try: return next(_input_lines)
    except StopIteration: raise EOFError('No more input. Fill the input box before running.')
_ns['input'] = _input
try:
    with contextlib.redirect_stdout(_output), contextlib.redirect_stderr(_output):
        exec(compile(_payload['code'], '<student>', 'exec'), _ns)
        if _payload.get('tests'):
            if not callable(_ns.get('solve')): raise ValueError('Define a function named solve with the provided signature.')
            for _test in _payload['tests']:
                try:
                    _actual = _ns['solve'](*copy.deepcopy(_test['args']))
                    _passed = _actual == _test['expected']
                    _results.append({'passed': bool(_passed), 'actual': repr(_actual), 'expected': repr(_test['expected'])})
                except Exception as _e:
                    _results.append({'passed': False, 'actual': type(_e).__name__ + ': ' + str(_e), 'expected': repr(_test['expected'])})
except BaseException:
    _error = traceback.format_exc()
json.dumps({'output': _output.getvalue(), 'error': _error, 'results': _results})
`);self.postMessage({type:'result',...JSON.parse(result)});}catch(error){self.postMessage({type:'failure',error:String(error)});}};
