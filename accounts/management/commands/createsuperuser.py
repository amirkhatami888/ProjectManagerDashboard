"""
Custom createsuperuser that closes the DB connection before prompting.
Avoids "MySQL server has gone away" when the user takes time to type
(username/email/password) and the server closes the idle connection.
"""
from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.db import connection


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Close DB connection so it won't go stale while user types.
        # Django will open a fresh connection when saving the user.
        connection.close()
        return super().handle(*args, **options)
