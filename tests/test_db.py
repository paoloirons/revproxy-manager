import pathlib,sys,tempfile,os,importlib
ROOT=pathlib.Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'manager'))

def test_schema_creation(tmp_path,monkeypatch):
 monkeypatch.setenv('DATA_DIR',str(tmp_path))
 import db; importlib.reload(db); db.init_db()
 with db.connect() as c:
  names={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 assert {'users','management_acl','trusted_proxies','proxy_routes','route_acl'} <= names
