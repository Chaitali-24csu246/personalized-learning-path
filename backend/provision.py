"""Operator-only bootstrap. Never copy a secret key into web/config.js.
Uses stdlib HTTPS; prompts for project secret and passwords without echo.
"""
import argparse,json,getpass,urllib.request,urllib.error
p=argparse.ArgumentParser();p.add_argument('--reset',help='Reset a known username password');args=p.parse_args()
url=input('Supabase project URL (https://...supabase.co): ').strip().rstrip('/')
if not url.startswith('https://') or not url.endswith('.supabase.co'):raise SystemExit('Use your official Supabase project HTTPS URL.')
secret=getpass.getpass('Legacy service_role JWT key (hidden; never the anon key): ')
if not secret.startswith('eyJ'):raise SystemExit('Use the legacy service_role JWT key from your project API settings.')
def call(path,data=None,method='POST'):
 req=urllib.request.Request(url+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'apikey':secret,'Authorization':'Bearer '+secret,'Content-Type':'application/json','Prefer':'return=representation'})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
 except urllib.error.HTTPError as e:raise SystemExit(f'Operation failed ({e.code}). Check project/schema/key; no passwords were printed.')
def password(name):
 pw=getpass.getpass(f'Choose password for {name} (at least 12 characters): ')
 if len(pw)<12 or pw!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords must match and contain at least 12 characters.')
 return pw
for name in ([args.reset] if args.reset else ['vanshika','srishti','chaitali','vasvi','admin']):
 import re
 if not re.fullmatch('[a-z][a-z0-9_-]{2,39}',name):raise SystemExit('Invalid username.')
 existing=call('/rest/v1/profiles?username=eq.'+name+'&select=id',method='GET')
 if existing:
  if args.reset:call('/auth/v1/admin/users/'+existing[0]['id'],{'password':password(name)},'PUT');print('Password reset:',name)
  else:print('Already provisioned, skipped:',name)
  continue
 if args.reset:raise SystemExit('Username not found.')
 user=call('/auth/v1/admin/users',{'email':name+'@students.learningpath.invalid','password':password(name),'email_confirm':True})
 call('/rest/v1/profiles',{'id':user['id'],'username':name,'display_name':name.title(),'role':'admin' if name=='admin' else 'student'})
 print('Created:',name)
print('Done. Store/distribute passwords privately. Students can change their password after signing in.')
