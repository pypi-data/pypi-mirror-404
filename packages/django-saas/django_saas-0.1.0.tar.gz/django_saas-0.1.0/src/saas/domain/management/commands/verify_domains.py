import typing as t

from django.core.management.base import BaseCommand

from saas.domain.models import Domain
from saas.domain.providers import get_domain_provider


class Command(BaseCommand):
    help = 'Verify pending domains against their providers'

    def handle(self, *args: t.Any, **options: t.Any) -> t.Optional[str]:
        # Filter domains that are not verified yet
        domains = Domain.objects.filter(verified=False)
        count = domains.count()

        if count == 0:
            self.stdout.write('No pending domains to verify.')
            return

        self.stdout.write(f'Found {count} pending domains. Starting verification...')

        for domain in domains:
            provider = get_domain_provider(domain.provider)
            if not provider:
                self.stdout.write(
                    self.style.WARNING(f"Skipping {domain.hostname}: Provider '{domain.provider}' not found.")
                )
                continue

            try:
                # verify_domain updates the domain instance in place if successful (and saves it)
                provider.verify_domain(domain)

                # Check if it became verified
                if domain.verified:
                    self.stdout.write(self.style.SUCCESS(f'Successfully verified {domain.hostname}'))
                else:
                    self.stdout.write(f'checked {domain.hostname}: Still pending')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error verifying {domain.hostname}: {e}'))

        self.stdout.write(self.style.SUCCESS('Verification process complete.'))
