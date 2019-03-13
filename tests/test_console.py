import io

from pykube.console import main


def test_main_hello_world(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO('print("Hello World!")'))
    main([])
    captured = capsys.readouterr()
    assert 'Hello World!' in captured.out


def test_main_script(monkeypatch, capsys):
    monkeypatch.setattr('pykube.HTTPClient.version', ('1', '13'))
    main(['-c', 'api.version'])
    captured = capsys.readouterr()
    assert "('1', '13')\n" == captured.out
