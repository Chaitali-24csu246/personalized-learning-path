"""Start the website without installing dependencies. Python 3.10+ required."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import argparse,webbrowser,threading
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--no-browser',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parent/'web'
handler=partial(SimpleHTTPRequestHandler,directory=str(root))
try: server=ThreadingHTTPServer(('127.0.0.1',args.port),handler)
except OSError as e: raise SystemExit(f'Cannot open port {args.port}: {e}. Try python start.py --port 8001')
print(f'Learning Path: http://localhost:{args.port}\nPress Ctrl+C to stop. Keep this window open.')
if not args.no_browser: threading.Timer(.5,lambda:webbrowser.open(f'http://localhost:{args.port}')).start()
try:server.serve_forever()
except KeyboardInterrupt: print('\nStopped.')
finally: server.server_close()
