from django.core.management import call_command


def test_saas_info_all(capsys):
    call_command('saas_info')
    captured = capsys.readouterr()

    assert 'Permissions:' in captured.out
    assert 'org.info.view' in captured.out
    assert 'Roles:' in captured.out
    assert 'ADMIN' in captured.out
    assert 'Scopes:' in captured.out
    assert 'user:read' in captured.out


def test_saas_info_permissions_only(capsys):
    call_command('saas_info', '--permissions')
    captured = capsys.readouterr()

    assert 'Permissions:' in captured.out
    assert 'iam.member.view' in captured.out
    assert 'Roles:' not in captured.out
    assert 'Scopes:' not in captured.out


def test_saas_info_roles_only(capsys):
    call_command('saas_info', '--roles')
    captured = capsys.readouterr()

    assert 'Roles:' in captured.out
    assert 'ADMIN' in captured.out
    assert 'Scopes:' not in captured.out


def test_saas_info_scopes_only(capsys):
    call_command('saas_info', '--scopes')
    captured = capsys.readouterr()

    assert 'Roles:' not in captured.out
    assert 'Scopes:' in captured.out
    assert 'user:read' in captured.out
