from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Runs setup commands in sequence: setup_home, setup_blog, setup_sightings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-on-error",
            action="store_true",
            help="Continue running remaining commands even if one fails",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output from each command",
        )

    def handle(self, *args, **options):
        commands = ["setup_home", "setup_blogs", "setup_sightings"]
        skip_on_error = options.get("skip_on_error", False)
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.SUCCESS("Starting setup process..."))

        for i, command_name in enumerate(commands, 1):
            try:
                self.stdout.write(
                    self.style.WARNING(f"[{i}/{len(commands)}] Running {command_name}...")
                )

                call_command(command_name, verbosity=2 if verbose else 1)

                self.stdout.write(self.style.SUCCESS(f"{command_name} completed successfully"))

            except CommandError as e:
                error_msg = f"{command_name} failed: {e!s}"
                self.stdout.write(self.style.ERROR(error_msg))

                if not skip_on_error:
                    self.stdout.write(
                        self.style.ERROR(
                            "Setup process aborted. Use --skip-on-error to continue on failures."
                        )
                    )
                    setup_error_msg = f"Setup failed at {command_name}"
                    raise CommandError(setup_error_msg) from e
                self.stdout.write(self.style.WARNING(f"Skipping {command_name} and continuing..."))

            except (ImportError, AttributeError, ValueError, TypeError) as e:
                error_msg = f"Unexpected error in {command_name}: {e!s}"
                self.stdout.write(self.style.ERROR(error_msg))

                if not skip_on_error:
                    setup_error_msg = f"Setup failed at {command_name}"
                    raise CommandError(setup_error_msg) from e

        self.stdout.write(self.style.SUCCESS("\nSetup process completed!"))
