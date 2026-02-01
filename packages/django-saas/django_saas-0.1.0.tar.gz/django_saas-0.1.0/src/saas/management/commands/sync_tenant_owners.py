from django.core.management.base import BaseCommand

from saas.identity.models import Membership
from saas.models import get_tenant_model


class Command(BaseCommand):
    help = 'Ensure all tenant owners have Member records'

    def handle(self, *args, **options):
        self.stdout.write('Checking tenant owner integrity...')
        tenants = get_tenant_model().objects.all()
        created_count = 0
        updated_count = 0

        for tenant in tenants:
            # Check if the owner has a member record in their own tenant
            member, created = Membership.objects.get_or_create(
                tenant=tenant, user=tenant.owner, defaults={'role': 'OWNER'}
            )

            if created:
                created_count += 1
            elif member.role != 'OWNER':
                # Force owner to have OWNER role if they have a different one
                member.role = 'OWNER'
                member.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Integrity check complete: Created {created_count} missing owner members, '
                f'Updated {updated_count} owner roles.'
            )
        )
