from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check whether Cloudflare Turnstile settings are loaded without printing secrets.'

    def handle(self, *args, **options):
        for name in ('TURNSTILE_SITE_KEY', 'TURNSTILE_SECRET_KEY'):
            value = getattr(settings, name, '') or ''
            value = str(value).strip()
            if value:
                preview = f'{value[:6]}...{value[-4:]}' if len(value) > 10 else 'set'
                self.stdout.write(self.style.SUCCESS(f'{name}: set ({len(value)} chars, {preview})'))
            else:
                self.stdout.write(self.style.ERROR(f'{name}: missing'))
        self.stdout.write(f'DJANGO_SETTINGS_MODULE: {getattr(settings, "SETTINGS_MODULE", "unknown")}')
