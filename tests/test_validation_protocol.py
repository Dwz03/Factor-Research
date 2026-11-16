from hashlib import sha256
import json

import pytest

from scripts.verify_momentum_001_validation import verify


def setup_protocol(root):
    (root / 'config').mkdir()
    (root / 'input.txt').write_text('frozen synthetic input')
    (root / 'snapshot.txt').write_bytes((root / 'input.txt').read_bytes())
    p = {'protocol_id': 'synthetic', 'environment': {}, 'frozen_files': {
        'input.txt': {'sha256': sha256((root / 'input.txt').read_bytes()).hexdigest(),
                      'snapshot': 'snapshot.txt'}}}
    path = root / 'config/momentum_001_validation.json'
    path.write_text(json.dumps(p))
    seal = {'sha256': {'config/momentum_001_validation.json': sha256(path.read_bytes()).hexdigest()}}
    (root / 'config/momentum_001_validation.lock.json').write_text(json.dumps(seal))


def test_verifier_accepts_unchanged_bytes(tmp_path):
    setup_protocol(tmp_path)
    assert verify(tmp_path)['status'] == 'integrity verified; validation not executed'


@pytest.mark.parametrize('relative', ['input.txt', 'snapshot.txt', 'config/momentum_001_validation.json'])
def test_verifier_detects_changes(tmp_path, relative):
    setup_protocol(tmp_path)
    with (tmp_path / relative).open('ab') as stream:
        stream.write(b' changed')
    with pytest.raises(ValueError):
        verify(tmp_path)
