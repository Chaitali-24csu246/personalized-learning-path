"""Write PUBLIC frontend configuration. Reads environment variables for CI,
or prompts locally. Rejects known secret key formats before writing."""
import base64,json,os,re
from pathlib import Path
url=os.environ.get('SUPABASE_URL') or input('Supabase project URL: ').strip()
key=os.environ.get('SUPABASE_ANON_KEY') or input('Public anon/publishable key: ').strip()
if not re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co',url):raise SystemExit('Expected https://PROJECT.supabase.co without a trailing slash.')
if key.startswith('sb_secret_'):raise SystemExit('Refusing a SECRET key in browser configuration.')
if not key.startswith('sb_publishable_'):
 try:
  token=key.split('.')[1];data=json.loads(base64.urlsafe_b64decode(token+'='*((4-len(token)%4)%4)))
  if data.get('role')!='anon':raise ValueError()
 except Exception:raise SystemExit('Expected the public anon JWT or sb_publishable_ key, never service_role.')
p=Path(__file__).resolve().parents[1]/'web/config.js'
p.write_text('// Public connection settings. No server secrets.\nwindow.LEARNING_PATH_CONFIG = '+json.dumps({'supabaseUrl':url,'supabaseAnonKey':key,'usernameDomain':'students.learningpath.invalid'},indent=2)+';\n')
print('Public configuration written to web/config.js.')
