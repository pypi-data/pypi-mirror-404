import getpass
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from saas.utils.secure import decrypt_data, encrypt_data


class Command(BaseCommand):
    help = 'Manage encrypted secrets'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subcommand', required=True)

        # list
        subparsers.add_parser('list', help='List all secrets')

        # add
        add_parser = subparsers.add_parser('add', help='Add a new secret')
        add_parser.add_argument('-k', '--key', help='Key name')
        add_parser.add_argument('-v', '--value', help='Value of the secret')

        # remove
        remove_parser = subparsers.add_parser('remove', help='Remove a secret')
        remove_parser.add_argument('-k', '--key', help='Key name')

    def handle(self, *args, **options):
        secrets_file = getattr(settings, 'SAAS_SECRETS_FILE', None)
        if not secrets_file:
            raise CommandError('SAAS_SECRETS_FILE setting is not set')

        subcommand = options['subcommand']

        if subcommand == 'list':
            self.handle_list(secrets_file)
        elif subcommand == 'add':
            self.handle_add(secrets_file, options.get('key'), options.get('value'))
        elif subcommand == 'remove':
            self.handle_remove(secrets_file, options.get('key'))

    def load_secrets(self, filepath):
        if not os.path.exists(filepath):
            return {}

        with open(filepath, 'r') as f:
            content = f.read().strip()

        if not content:
            return {}

        decrypted = decrypt_data(content)
        if decrypted is None:
            raise CommandError('Failed to decrypt secrets file')

        return json.loads(decrypted.decode('utf-8'))

    def save_secrets(self, filepath, data):
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted = encrypt_data(json_bytes)
        with open(filepath, 'w') as f:
            f.write(encrypted)

    def handle_list(self, filepath):
        data = self.load_secrets(filepath)
        if not data:
            self.stdout.write('No secrets found.')
            return

        max_key_len = max(len(k) for k in data.keys())
        max_key_len = max(max_key_len, 3)

        masked_data = {}
        for key, value in data.items():
            val_str = str(value)
            if len(val_str) > 4:
                masked_val = val_str[:4] + '******'
            else:
                masked_val = '******'
            masked_data[key] = masked_val

        max_val_len = max(len(v) for v in masked_data.values())
        max_val_len = max(max_val_len, 5)

        header = f'{"Key".ljust(max_key_len)} | {"Value".ljust(max_val_len)}'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        for key, value in masked_data.items():
            self.stdout.write(f'{key.ljust(max_key_len)} | {value.ljust(max_val_len)}')

    def handle_add(self, filepath, key, value):
        data = self.load_secrets(filepath)
        if not key:
            key = input('Enter key name: ')
        if value is None:
            value = getpass.getpass(f'Enter value for {key}: ')

        data[key] = value
        self.save_secrets(filepath, data)
        self.stdout.write(self.style.SUCCESS(f'Secret "{key}" added.'))

    def handle_remove(self, filepath, key):
        data = self.load_secrets(filepath)
        if not key:
            key = input('Enter key name: ')
        if key in data:
            del data[key]
            self.save_secrets(filepath, data)
            self.stdout.write(self.style.SUCCESS(f'Secret "{key}" removed.'))
        else:
            self.stdout.write(self.style.WARNING(f'Secret "{key}" not found.'))
