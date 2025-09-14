from pathlib import Path

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, ProgrammingError

from wagtail.models import Page

from apps.core.management import WagtailSetupUtils
from apps.sightings.models import SightingModel, SightingPage


class Command(BaseCommand):
    help = "Set up the sightings map page with initial location data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-file",
            type=str,
            default="apps/blog/content/sighting_page.yaml",
            help="The file containing the sighting index content",
        )
        parser.add_argument(
            "--fixtures-file",
            type=str,
            default="apps/sightings/fixtures/sightings.json",
            help="The file containing the sighting fixtures",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion of existing sightings pages and recreate them",
        )
        parser.add_argument(
            "--fixtures-file",
            action="store_true",
            help="Load location fixtures data",
        )

    def handle(self, *args, **options):
        content_file = Path(options["content_file"])
        fixtures_file = Path(options["fixtures_file"])
        force = options["force"]
        load_fixtures = options["load_fixtures"]
        utils = WagtailSetupUtils(self)

        utils.styled_output("Setting up sightings map page...")

        # Check if tables exist before trying to delete
        if not utils.check_model_tables_exist([SightingPage, SightingModel]):
            utils.styled_output(
                "Sightings tables don't exist. "
                "Please run 'python manage.py makemigrations sightings' "
                "and 'python manage.py migrate' first.",
                "WARNING",
            )
            return

        parent_page = utils.get_parent_page()
        if not parent_page:
            return

        # Clean up existing sightings content if force is used
        if force:
            utils.styled_output("Cleaning up existing sightings content...")
            utils.cleanup_pages_by_type([SightingPage])

            if SightingModel.objects.exists():
                SightingModel.objects.all().delete()
                utils.styled_output("  - Deleted all existing locations")

        if not utils.check_slug_availability(parent_page, "sightings", force):
            return

        map_page = self._create_sighting_page(content_file, utils, parent_page)
        if not map_page:
            return

        if load_fixtures or SightingModel.objects.count() == 0:
            self._load_location_fixtures(utils, fixtures_file)

        location_count = SightingModel.objects.count()
        utils.styled_output(f"Successfully set up sightings page with {location_count} locations")
        utils.styled_output("Sightings map available at: /sightings/")
        utils.styled_output("Admin available at: /admin/")

    @staticmethod
    def _create_sighting_page(
        content_file: Path, utils: WagtailSetupUtils, parent_page: Page
    ) -> Page | None:
        """Create the sightings map page"""
        utils.styled_output("Creating sightings map page...")

        sighting_page_data = utils.load_page_content(content_file, "sighting_page")
        sighting_page = SightingPage(**sighting_page_data)

        try:
            utils.create_and_publish_page(parent_page, sighting_page)
        except (DatabaseError, ProgrammingError) as e:
            utils.styled_output(f"Failed to create map page: {e}", "ERROR")
            return None
        else:
            return sighting_page

    @staticmethod
    def _load_location_fixtures(utils: WagtailSetupUtils, fixtures_file: Path) -> None:
        """Load location fixtures"""
        utils.styled_output("Loading location fixtures...")

        try:
            management.call_command("loaddata", fixtures_file, app_label="sightings")
            utils.styled_output("  - Successfully loaded location fixtures")

        except (FileNotFoundError, CommandError) as e:
            utils.styled_output(f"Failed to load fixtures: {e}", "WARNING")
            utils.styled_output("Creating sample locations manually...", "WARNING")
