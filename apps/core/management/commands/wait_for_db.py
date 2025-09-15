import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database to be available"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Maximum time to wait for database (seconds)",
        )

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for database...")

        timeout = options["timeout"]
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Get the default database connection
                db_conn = connections["default"]
                # Try to connect to the database
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS("Database available!"))
                return
            except OperationalError:
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.ERROR(f"Database still unavailable after {timeout} seconds"))
        raise OperationalError("Database connection timeout")
