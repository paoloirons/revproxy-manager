import importlib.util, pathlib, sys
ROOT=pathlib.Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'manager'))
from security import valid_cidr, effective_client_ip, hash_password, verify_password

def test_cidr_normalization(): assert valid_cidr('192.168.1.10/24')=='192.168.1.0/24'
def test_password():
 h=hash_password('verystrongpass'); assert verify_password('verystrongpass',h); assert not verify_password('wrong',h)
def test_xff_untrusted_peer_ignored(): assert effective_client_ip('203.0.113.2','192.168.1.5',['10.0.0.0/8'])=='203.0.113.2'
def test_xff_trusted_peer(): assert effective_client_ip('10.0.0.2','198.51.100.7',['10.0.0.0/8'])=='198.51.100.7'
def test_xff_chain_skips_trusted_hops(): assert effective_client_ip('10.0.0.2','198.51.100.7, 10.0.0.3',['10.0.0.0/8'])=='198.51.100.7'

def test_persistent_generated_secret(tmp_path, monkeypatch):
    import importlib, os
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    monkeypatch.setenv('MANAGER_SECRET', '')
    import security
    value = security._manager_secret()
    path = tmp_path / 'manager.secret'
    assert len(value) >= 32
    assert path.read_text() == value
    assert (path.stat().st_mode & 0o777) == 0o600
    assert security._manager_secret() == value
