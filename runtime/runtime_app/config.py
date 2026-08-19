import ipaddress, os, sqlite3
from pathlib import Path
DB_PATH=Path(os.getenv('DATA_DIR','/data'))/'revproxy.db'

def db():
 if not DB_PATH.exists(): return None
 c=sqlite3.connect(f'file:{DB_PATH}?mode=ro',uri=True); c.row_factory=sqlite3.Row; c.execute('PRAGMA busy_timeout=3000'); return c

def routes():
 c=db()
 if not c:return []
 try:return c.execute('SELECT * FROM proxy_routes WHERE enabled=1 ORDER BY length(path_prefix) DESC').fetchall()
 finally:c.close()

def route_acls(route_id):
 c=db()
 if not c:return []
 try:return [r['cidr'] for r in c.execute('SELECT cidr FROM route_acl WHERE route_id=?',(route_id,)).fetchall()]
 finally:c.close()

def trusted():
 c=db()
 if not c:return []
 try:return [r['cidr'] for r in c.execute('SELECT cidr FROM trusted_proxies').fetchall()]
 finally:c.close()

def in_any(ip,cidrs):
 try:a=ipaddress.ip_address(ip)
 except ValueError:return False
 for x in cidrs:
  try:
   if a in ipaddress.ip_network(x,strict=False):return True
  except ValueError:pass
 return False

def effective_ip(peer,xff):
 t=trusted()
 if not xff or not in_any(peer,t):return peer
 chain=[x.strip() for x in xff.split(',') if x.strip()]+[peer]
 for candidate in reversed(chain):
  if not in_any(candidate,t):
   try:ipaddress.ip_address(candidate);return candidate
   except ValueError:pass
 return peer
