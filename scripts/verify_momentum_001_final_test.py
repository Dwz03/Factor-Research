"""Verify final-test freeze and validation lineage; never load market outcomes."""
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_momentum_001_validation import digest


def check_environment(environment):
    for name, expected in environment.items():
        actual = platform.python_version() if name == 'python' else version(name)
        if actual != expected:
            raise ValueError(f'Environment mismatch: {name}')


def verify_validation_history(root=ROOT):
    """Audit the unchanged parent seal, with its authorized report append explicitly accounted for."""
    root = Path(root).resolve()
    count = 0

    def check(relative, expected):
        nonlocal count
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError(f'Validation lineage hash mismatch: {relative}')
        count += 1

    parent = json.loads((root/'config/momentum_001_validation.json').read_text(encoding='utf-8'))
    seal = json.loads((root/'config/momentum_001_validation.lock.json').read_text(encoding='utf-8'))
    for relative, expected in seal['sha256'].items():
        check(relative, expected)
    base = Path('data/validation/momentum_001_v1')
    artifacts = json.loads((root/base/'artifacts.json').read_text(encoding='utf-8'))
    for relative, expected in artifacts['sha256'].items():
        check(base/relative.replace('\\', '/'), expected)
    check('reports/01_momentum.md', artifacts['report_sha256'])
    archive = (root/base/'exploration_report_frozen.md').read_bytes()
    report = (root/'reports/01_momentum.md').read_bytes()
    if report[:artifacts['report_prefix_bytes']] != archive:
        raise ValueError('Frozen exploration report prefix changed')
    for relative, record in parent['frozen_files'].items():
        actual = base/'exploration_report_frozen.md' if relative == 'reports/01_momentum.md' else relative
        check(actual, record['sha256'])
        if record.get('snapshot'):
            check(record['snapshot'], record['sha256'])
    check_environment(parent['environment'])
    result = json.loads((root/base/'result.json').read_text(encoding='utf-8'))
    if result['primary']['decision'] != 'Pass':
        raise ValueError('Required successful validation record is absent')
    return dict(files_checked=count, validation_decision='Pass',
                report_append='archive and original prefix verified; parent seal unchanged')


def verify(root=ROOT):
    root = Path(root).resolve()
    lock = json.loads((root/'config/momentum_001_final_test.lock.json').read_text(encoding='utf-8'))
    count = 0

    def check(relative, expected):
        nonlocal count
        path = (root/relative).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError(f'Final-test integrity mismatch: {relative}')
        count += 1

    for relative, expected in lock['sha256'].items():
        check(relative, expected)
    protocol = json.loads((root/'config/momentum_001_final_test.json').read_text(encoding='utf-8'))
    for relative, record in protocol['frozen_files'].items():
        check(relative, record['sha256'])
        if record.get('snapshot'):
            check(record['snapshot'], record['sha256'])
    check_environment(protocol['environment'])
    lineage = verify_validation_history(root)
    return dict(protocol_id=protocol['protocol_id'], final_freeze_file_checks=count,
                validation_lineage=lineage, status='frozen integrity verified; final test not executed')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
