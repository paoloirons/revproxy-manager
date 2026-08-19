import ipaddress, os, secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from db import init_db, connect, one, all
from security import hash_password, verify_password, make_session, read_session, valid_cidr, effective_client_ip, ip_in_any

BASE_DIR=Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_app):
 init_db()
 yield

app=FastAPI(title='RevProxy Manager',docs_url=None,redoc_url=None,lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(BASE_DIR/'static')),name='static')
templates=Jinja2Templates(directory=str(BASE_DIR/'templates'))
COOKIE_SECURE=os.getenv('SECURE_COOKIES','0')=='1'

def client_info(request):
 peer=request.client.host if request.client else ''
 trusted=[r['cidr'] for r in all('SELECT cidr FROM trusted_proxies')]
 xff=request.headers.get('x-forwarded-for','')
 return peer,xff,effective_client_ip(peer,xff,trusted),trusted

def acl_allows(request):
 cidrs=[r['cidr'] for r in all('SELECT cidr FROM management_acl')]
 if not cidrs: return True
 return ip_in_any(client_info(request)[2],cidrs)

def session(request): return read_session(request.cookies.get('rpm_session',''))
def auth(request): return session(request) if acl_allows(request) else None
def csrf_ok(request, token):
 s=session(request); return bool(s and token and secrets.compare_digest(s.get('c',''),token))

def set_cookie(resp,username):
 csrf=secrets.token_urlsafe(24)
 resp.set_cookie('rpm_session',make_session(username,csrf),httponly=True,samesite='strict',secure=COOKIE_SECURE,max_age=43200)
 return csrf

def normalize_prefix(value):
 v='/' + value.strip().lstrip('/')
 if v!='/' and not v.endswith('/'): v+='/'
 return v

def validate_upstream(value):
 u=value.strip(); p=urlparse(u)
 if p.scheme not in ('http','https') or not p.hostname: raise ValueError('Upstream deve essere http:// o https:// valido')
 if p.username or p.password: raise ValueError('Credenziali nell’URL upstream non consentite')
 return u.rstrip('/')+'/'

@app.get('/healthz')
def health(): return {'ok':True}

@app.get('/',response_class=HTMLResponse)
def root(request:Request):
 if not one('SELECT id FROM users LIMIT 1'): return RedirectResponse('/setup',303)
 if not acl_allows(request): return templates.TemplateResponse(request,'blocked.html',{'ip':client_info(request)[2]},status_code=403)
 if not session(request): return RedirectResponse('/login',303)
 return RedirectResponse('/dashboard',303)

@app.get('/setup',response_class=HTMLResponse)
def setup_get(request:Request):
 if one('SELECT id FROM users LIMIT 1'): return RedirectResponse('/',303)
 peer,xff,ip,trusted=client_info(request)
 return templates.TemplateResponse(request,'setup.html',{'ip':ip,'error':None})

@app.post('/setup')
def setup_post(request:Request,username:str=Form(...),password:str=Form(...),confirm:str=Form(...),restrict_ip:str|None=Form(None)):
 if one('SELECT id FROM users LIMIT 1'): return RedirectResponse('/',303)
 error=None
 if len(username.strip())<3: error='Username troppo corto'
 elif len(password)<10: error='Password: almeno 10 caratteri'
 elif password!=confirm: error='Le password non coincidono'
 if error: return templates.TemplateResponse(request,'setup.html',{'ip':client_info(request)[2],'error':error},status_code=400)
 with connect() as db:
  db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(username.strip(),hash_password(password)))
  if restrict_ip:
   ip=ipaddress.ip_address(client_info(request)[2]); db.execute('INSERT INTO management_acl(cidr,description) VALUES(?,?)',(f'{ip}/{ip.max_prefixlen}','Initial setup'))
 resp=RedirectResponse('/dashboard',303); set_cookie(resp,username.strip()); return resp

@app.get('/login',response_class=HTMLResponse)
def login_get(request:Request):
 if not acl_allows(request): return templates.TemplateResponse(request,'blocked.html',{'ip':client_info(request)[2]},status_code=403)
 return templates.TemplateResponse(request,'login.html',{'error':None})

@app.post('/login')
def login_post(request:Request,username:str=Form(...),password:str=Form(...)):
 if not acl_allows(request): return templates.TemplateResponse(request,'blocked.html',{'ip':client_info(request)[2]},status_code=403)
 u=one('SELECT * FROM users WHERE username=?',(username,))
 if not u or not verify_password(password,u['password_hash']): return templates.TemplateResponse(request,'login.html',{'error':'Credenziali non valide'},status_code=401)
 resp=RedirectResponse('/dashboard',303); set_cookie(resp,username); return resp

@app.post('/logout')
def logout(request:Request,csrf:str=Form(...)):
 if not csrf_ok(request,csrf): return JSONResponse({'detail':'CSRF'},403)
 resp=RedirectResponse('/login',303); resp.delete_cookie('rpm_session'); return resp

@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(request:Request):
 s=auth(request)
 if not s: return RedirectResponse('/',303)
 routes=all('SELECT * FROM proxy_routes ORDER BY path_prefix')
 aclrows=all('SELECT route_id,cidr FROM route_acl ORDER BY cidr'); route_acls={}
 for r in aclrows: route_acls.setdefault(r['route_id'],[]).append(r['cidr'])
 peer,xff,ip,trusted=client_info(request)
 return templates.TemplateResponse(request,'dashboard.html',{'user':s['u'],'csrf':s['c'],'routes':routes,'route_acls':route_acls,'mgmt':all('SELECT * FROM management_acl ORDER BY cidr'),'trusted':all('SELECT * FROM trusted_proxies ORDER BY cidr'),'peer':peer,'xff':xff,'effective_ip':ip})

def require_post(request,csrf):
 return auth(request) and csrf_ok(request,csrf)

@app.post('/routes/save')
def route_save(request:Request,csrf:str=Form(...),route_id:str=Form(''),name:str=Form(...),path_prefix:str=Form(...),upstream:str=Form(...),enabled:str|None=Form(None),acls:str=Form('')):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 try:
  prefix=normalize_prefix(path_prefix); upstream=validate_upstream(upstream)
  if prefix=='/': raise ValueError('Il path / è riservato; usa un prefisso specifico')
  cidrs=[valid_cidr(x) for x in acls.replace(',', '\n').splitlines() if x.strip()]
 except ValueError as e: return JSONResponse({'detail':str(e)},400)
 try:
  with connect() as db:
   if route_id:
    db.execute('UPDATE proxy_routes SET name=?,path_prefix=?,upstream=?,enabled=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(name.strip(),prefix,upstream,1 if enabled else 0,int(route_id))); rid=int(route_id); db.execute('DELETE FROM route_acl WHERE route_id=?',(rid,))
   else:
    cur=db.execute('INSERT INTO proxy_routes(name,path_prefix,upstream,enabled) VALUES(?,?,?,?)',(name.strip(),prefix,upstream,1 if enabled else 0)); rid=cur.lastrowid
   for c in cidrs: db.execute('INSERT INTO route_acl(route_id,cidr) VALUES(?,?)',(rid,c))
 except Exception as e: return JSONResponse({'detail':'Path già usato o dati non validi'},400)
 return RedirectResponse('/dashboard',303)

@app.post('/routes/delete')
def route_delete(request:Request,csrf:str=Form(...),route_id:int=Form(...)):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 with connect() as db: db.execute('DELETE FROM proxy_routes WHERE id=?',(route_id,))
 return RedirectResponse('/dashboard',303)

@app.post('/settings/acl/add')
def acl_add(request:Request,csrf:str=Form(...),cidr:str=Form(...),description:str=Form('')):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 try: c=valid_cidr(cidr)
 except ValueError as e: return JSONResponse({'detail':str(e)},400)
 with connect() as db: db.execute('INSERT OR IGNORE INTO management_acl(cidr,description) VALUES(?,?)',(c,description.strip()))
 return RedirectResponse('/dashboard#settings',303)

@app.post('/settings/acl/delete')
def acl_delete(request:Request,csrf:str=Form(...),item_id:int=Form(...)):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 rows=all('SELECT id FROM management_acl')
 if len(rows)<=1: return JSONResponse({'detail':'Non puoi eliminare l’ultima ACL dalla UI. Usa recovery clear-acl se necessario.'},400)
 with connect() as db: db.execute('DELETE FROM management_acl WHERE id=?',(item_id,))
 return RedirectResponse('/dashboard#settings',303)

@app.post('/settings/trusted/add')
def trusted_add(request:Request,csrf:str=Form(...),cidr:str=Form(...),description:str=Form('')):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 try: c=valid_cidr(cidr)
 except ValueError as e: return JSONResponse({'detail':str(e)},400)
 with connect() as db: db.execute('INSERT OR IGNORE INTO trusted_proxies(cidr,description) VALUES(?,?)',(c,description.strip()))
 return RedirectResponse('/dashboard#settings',303)

@app.post('/settings/trusted/delete')
def trusted_delete(request:Request,csrf:str=Form(...),item_id:int=Form(...)):
 if not require_post(request,csrf): return JSONResponse({'detail':'Unauthorized'},403)
 with connect() as db: db.execute('DELETE FROM trusted_proxies WHERE id=?',(item_id,))
 return RedirectResponse('/dashboard#settings',303)
