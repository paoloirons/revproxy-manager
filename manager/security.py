import base64, hashlib, hmac, ipaddress, os, secrets, time
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

ITERATIONS=390000

def hash_password(password):
 salt=secrets.token_bytes(16)
 digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,ITERATIONS)
 return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

def verify_password(password, encoded):
 try:
  algo,iters,salt,digest=encoded.split('$',3)
  if algo!='pbkdf2_sha256': return False
  got=hashlib.pbkdf2_hmac('sha256',password.encode(),base64.b64decode(salt),int(iters))
  return hmac.compare_digest(got,base64.b64decode(digest))
 except Exception: return False

def _manager_secret():
 env=os.getenv('MANAGER_SECRET','').strip()
 if len(env)>=32: return env
 data_dir=os.getenv('DATA_DIR','/data')
 path=os.path.join(data_dir,'manager.secret')
 os.makedirs(data_dir,exist_ok=True)
 try:
  with open(path,'r',encoding='utf-8') as f:
   value=f.read().strip()
   if len(value)>=32:return value
 except FileNotFoundError:pass
 value=secrets.token_urlsafe(48)
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(value)
 return value

def serializer():
 return URLSafeTimedSerializer(_manager_secret(),salt='revproxy-manager-session')

def make_session(username, csrf): return serializer().dumps({'u':username,'c':csrf})
def read_session(value,max_age=43200):
 try: return serializer().loads(value,max_age=max_age)
 except (BadSignature,SignatureExpired): return None

def valid_cidr(value):
 try: return str(ipaddress.ip_network(value.strip(),strict=False))
 except ValueError: raise ValueError('CIDR/IP non valido')

def ip_in_any(ip, cidrs):
 try: addr=ipaddress.ip_address(ip)
 except ValueError: return False
 for c in cidrs:
  try:
   if addr in ipaddress.ip_network(c,strict=False): return True
  except ValueError: pass
 return False

def effective_client_ip(peer, xff, trusted_cidrs):
 """Trust XFF only when the immediate peer is trusted. Pick nearest untrusted hop from right to left."""
 if not ip_in_any(peer,trusted_cidrs) or not xff: return peer
 chain=[x.strip() for x in xff.split(',') if x.strip()]
 chain.append(peer)
 for candidate in reversed(chain):
  if not ip_in_any(candidate,trusted_cidrs):
   try: ipaddress.ip_address(candidate); return candidate
   except ValueError: continue
 return chain[0] if chain else peer
