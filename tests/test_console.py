import io
import pytest

from pykube.console import main


@pytest.fixture
def kubeconfig(tmpdir):
    kubeconfig = tmpdir.join('kubeconfig')
    kubeconfig.write('''
apiVersion: v1
clusters:
- cluster: {server: 'https://localhost:9443'}
  name: test
contexts:
- context: {cluster: test}
  name: test-context
- context: {cluster: test}
  name: other
current-context: test-context
kind: Config
    ''')
    return kubeconfig


def test_main_current_context(monkeypatch, capsys, kubeconfig):
    monkeypatch.setattr('sys.stdin', io.StringIO('print(f"current context: {config.current_context}")'))
    main(['--kubeconfig', str(kubeconfig)])
    captured = capsys.readouterr()
    assert 'current context: test-context' in captured.out


def test_main_custom_context(monkeypatch, capsys, kubeconfig):
    monkeypatch.setattr('sys.stdin', io.StringIO('print(f"current context: {config.current_context}")'))
    main(['--kubeconfig', str(kubeconfig), '--context=other'])
    captured = capsys.readouterr()
    assert 'current context: other' in captured.out


def test_main_script(monkeypatch, capsys, kubeconfig):
    monkeypatch.setattr('pykube.HTTPClient.version', ('1', '13'))
    main(['--kubeconfig', str(kubeconfig), '-c', 'api.version'])
    captured = capsys.readouterr()
    assert "('1', '13')\n" == captured.out
