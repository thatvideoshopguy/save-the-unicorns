from django.core.management.base import BaseCommand
from django.core import management
from wagtail.models import Page
from apps.sightings.models import Location
from apps.sightings.models.sighting_page import MapPage
from apps.core.management import WagtailSetupUtils

FIXTURES_FILE = "apps/sightings/fixtures/sightings.json"


class Command(BaseCommand):
    help = "Set up the sightings map page with initial location data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion of existing sightings pages and recreate them",
        )
        parser.add_argument(
            "--load-fixtures",
            action="store_true",
            help="Load location fixtures data",
        )

    def handle(self, *args, **options):
        force = options["force"]
        load_fixtures = options["load_fixtures"]
        utils = WagtailSetupUtils(self)

        utils.styled_output("Setting up sightings map page...")

        # Check if tables exist before trying to delete
        if not utils.check_model_tables_exist([MapPage, Location]):
            utils.styled_output(
                "Sightings tables don't exist. Please run 'python manage.py makemigrations sightings' and 'python manage.py migrate' first.",
                "WARNING",
            )
            return

        parent_page = utils.get_parent_page()
        if not parent_page:
            return

        # Clean up existing sightings content if force is used
        if force:
            utils.styled_output("Cleaning up existing sightings content...")
            utils.cleanup_pages_by_type([MapPage])

            if Location.objects.exists():
                Location.objects.all().delete()
                utils.styled_output("  - Deleted all existing locations")

        if not utils.check_slug_availability(parent_page, "sightings", force):
            return

        map_page = self._create_map_page(utils, parent_page)
        if not map_page:
            return

        if load_fixtures or Location.objects.count() == 0:
            self._load_location_fixtures(utils, FIXTURES_FILE)

        location_count = Location.objects.count()
        utils.styled_output(f"Successfully set up sightings page with {location_count} locations")
        utils.styled_output(f"Sightings map available at: /sightings/")
        utils.styled_output(f"Admin available at: /admin/")

    @staticmethod
    def _create_map_page(utils: WagtailSetupUtils, parent_page: Page) -> Page | None:
        """Create the sightings map page"""
        utils.styled_output("Creating sightings map page...")

        map_page = MapPage(
            title="Sightings",
            slug="sightings",
            intro="""
            <p>Explore confirmed unicorn sightings across the UK. Our dedicated team of researchers
            has documented these magical encounters over the years.</p>
            """,
            zoom_level=6,
        )

        try:
            utils.create_and_publish_page(parent_page, map_page)
            return map_page
        except Exception as e:
            utils.styled_output(f"Failed to create map page: {e}", "ERROR")
            return None

    @staticmethod
    def _load_location_fixtures(utils: WagtailSetupUtils, fixtures_file) -> None:
        """Load location fixtures"""
        utils.styled_output("Loading location fixtures...")

        try:
            management.call_command("loaddata", fixtures_file, app_label="sightings")
            utils.styled_output(f"  - Successfully loaded location fixtures")

        except Exception as e:
            utils.styled_output(f"Failed to load fixtures: {e}", "WARNING")
            utils.styled_output("Creating sample locations manually...", "WARNING")
