"""Guard executable code against reintroducing a sibling checkout dependency."""
import ast
from pathlib import Path


def test_no_external_checkout_dependency():
    root = Path(__file__).resolve().parents[1]
    for folder in ('src', 'scripts', 'tests'):
        for path in (root / folder).rglob('*.py'):
            if path == Path(__file__):
                continue
            text = path.read_text()
            assert 'NGINX_QA_SOURCE' not in text, path
            assert 'nginx-qa-reference' not in text, path
            assert '../nginx-qa' not in text, path
            assert '/nginx-qa/' not in text, path
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert node.module not in ('main', 'nginx_qa'), path
                if isinstance(node, ast.Call):
                    name = ast.unparse(node.func)
                    assert name not in ('importlib.import_module', 'sys.path.insert', 'sys.path.append', 'os.chdir', 'monkeypatch.chdir'), path
