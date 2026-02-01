from unittest.mock import Mock, mock_open, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from saas.management.commands.secrets import Command


@override_settings(SAAS_SECRETS_FILE=None)
def test_no_secrets_file():
    with pytest.raises(CommandError, match='SAAS_SECRETS_FILE setting is not set'):
        call_command('secrets', 'list')


@override_settings(SAAS_SECRETS_FILE='.not-exists-secrets')
def test_secrets_list_empty(capsys):
    call_command('secrets', 'list')
    captured = capsys.readouterr()
    assert 'No secrets found.' in captured.out


def test_list_default_secrets(capsys):
    call_command('secrets', 'list')
    captured = capsys.readouterr()
    assert 'turnstile' in captured.out


@override_settings(SAAS_SECRETS_FILE='secrets.enc')
def test_secrets_add(capsys):
    with patch('saas.management.commands.secrets.Command.load_secrets', return_value={}) as mock_load:
        with patch('saas.management.commands.secrets.Command.save_secrets') as mock_save:
            call_command('secrets', 'add', '--key', 'new_key', '--value', 'new_val')

            mock_save.assert_called_with('secrets.enc', {'new_key': 'new_val'})
            captured = capsys.readouterr()
            assert 'Secret "new_key" added.' in captured.out


@override_settings(SAAS_SECRETS_FILE='secrets.enc')
def test_secrets_add_interactive(capsys):
    with patch('saas.management.commands.secrets.Command.load_secrets', return_value={}) as mock_load:
        with patch('saas.management.commands.secrets.Command.save_secrets') as mock_save:
            with patch('builtins.input', return_value='interactive_key'):
                with patch('getpass.getpass', return_value='interactive_val'):
                    call_command('secrets', 'add')

            mock_save.assert_called_with('secrets.enc', {'interactive_key': 'interactive_val'})


@override_settings(SAAS_SECRETS_FILE='secrets.enc')
def test_secrets_remove(capsys):
    with patch('saas.management.commands.secrets.Command.load_secrets', return_value={'k': 'v'}) as mock_load:
        with patch('saas.management.commands.secrets.Command.save_secrets') as mock_save:
            call_command('secrets', 'remove', '--key', 'k')

            mock_save.assert_called_with('secrets.enc', {})
            captured = capsys.readouterr()
            assert 'Secret "k" removed.' in captured.out


@override_settings(SAAS_SECRETS_FILE='secrets.enc')
def test_secrets_remove_not_found(capsys):
    with patch('saas.management.commands.secrets.Command.load_secrets', return_value={'k': 'v'}):
        with patch('saas.management.commands.secrets.Command.save_secrets') as mock_save:
            call_command('secrets', 'remove', '--key', 'missing')

            mock_save.assert_not_called()
            captured = capsys.readouterr()
            assert 'Secret "missing" not found.' in captured.out


def test_load_secrets_decrypt_fail():
    cmd = Command()
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data='encrypted_data')):
            with patch('saas.management.commands.secrets.decrypt_data', return_value=None):
                with pytest.raises(CommandError, match='Failed to decrypt secrets file'):
                    cmd.load_secrets('dummy.enc')


def test_load_secrets_success():
    cmd = Command()
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data='encrypted_data')):
            with patch('saas.management.commands.secrets.decrypt_data', return_value=b'{"k": "v"}'):
                data = cmd.load_secrets('dummy.enc')
                assert data == {'k': 'v'}


def test_save_secrets():
    cmd = Command()
    with patch('builtins.open', mock_open()) as m:
        with patch('saas.management.commands.secrets.encrypt_data', return_value='encrypted_data'):
            cmd.save_secrets('dummy.enc', {'k': 'v'})
            m().write.assert_called_with('encrypted_data')


def test_list_masked_output(capsys):
    cmd = Command()
    cmd.stdout = Mock()
    cmd.stdout.write = Mock()

    with patch(
        'saas.management.commands.secrets.Command.load_secrets', return_value={'short': '123', 'long': '12345678'}
    ):
        cmd.handle_list('dummy.enc')

        # Check that mask logic works
        # short: 123 -> ******
        # long: 12345678 -> 1234******

        # We can't easily capture the formatted output without mocking stdout.write effectively.
        # But we can check if masked values are present in calls.
        calls = cmd.stdout.write.call_args_list
        output = ''.join([c[0][0] for c in calls])

        assert '******' in output
        assert '1234******' in output
