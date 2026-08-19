import sys
from db import init_db, connect
from security import valid_cidr, hash_password

def main():
 init_db()
 if len(sys.argv)<2: raise SystemExit('usage: recovery.py allow CIDR | clear-acl | reset-password USER PASS')
 cmd=sys.argv[1]
 with connect() as db:
  if cmd=='allow' and len(sys.argv)==3:
   cidr=valid_cidr(sys.argv[2]); db.execute('INSERT OR IGNORE INTO management_acl(cidr,description) VALUES(?,?)',(cidr,'recovery')); print('allowed',cidr)
  elif cmd=='clear-acl': db.execute('DELETE FROM management_acl'); print('management ACL cleared')
  elif cmd=='reset-password' and len(sys.argv)==4:
   cur=db.execute('UPDATE users SET password_hash=? WHERE username=?',(hash_password(sys.argv[3]),sys.argv[2]));
   if not cur.rowcount: raise SystemExit('user not found')
   print('password reset')
  else: raise SystemExit('invalid command')
if __name__=='__main__': main()
