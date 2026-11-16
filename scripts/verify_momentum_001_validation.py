"""Verify the frozen protocol offline, using bytes/versions only, never outcomes."""
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def verify(root=ROOT):
    root = Path(root).resolve()

    def checked_path(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Frozen path escapes repository')
        return path

    lock = json.loads((root / 'config/momentum_001_validation.lock.json').read_text(encoding='utf-8'))
    count = 0
    for relative, expected in lock['sha256'].items():
        if digest(checked_path(relative)) != expected:
            raise ValueError(f'Seal mismatch: {relative}')
        count += 1
    protocol = json.loads((root / 'config/momentum_001_validation.json').read_text(encoding='utf-8'))
    for relative, record in protocol['frozen_files'].items():
        if digest(checked_path(relative)) != record['sha256']:
            raise ValueError(f'Frozen input changed: {relative}')
        count += 1
        if record.get('snapshot'):
            if digest(checked_path(record['snapshot'])) != record['sha256']:
                raise ValueError(f'Snapshot changed: {relative}')
            count += 1
    for name, expected in protocol['environment'].items():
        actual = platform.python_version() if name == 'python' else version(name)
        if actual != expected:
            raise ValueError(f'Environment mismatch: {name} expected {expected}, found {actual}')
    return dict(protocol_id=protocol['protocol_id'], files_checked=count,
                status='integrity verified; validation not executed')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
