from django.core.management.base import BaseCommand
from django.core import management
from wagtail.models import Page
from apps.sightings.models import MapPage, Location
from apps.core.models import HomePage
from apps.core.management import WagtailSetupUtils


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

        parent_page = self._get_parent_page(utils)
        if not parent_page:
            return

        # Clean up existing sightings content if force is used
        if force:
            utils.styled_output("Cleaning up existing sightings content...")
            utils.cleanup_pages_by_type([MapPage])
            # Optionally clean up locations too when forcing recreation
            if Location.objects.exists():
                Location.objects.all().delete()
                utils.styled_output("  - Deleted all existing locations")

        # Check slug availability
        if not utils.check_slug_availability(parent_page, "sightings", force):
            return

        # Create sightings map page
        map_page = self._create_map_page(utils, parent_page)
        if not map_page:
            return

        # Load fixtures if requested
        if load_fixtures or Location.objects.count() == 0:
            self._load_location_fixtures(utils)

        location_count = Location.objects.count()
        utils.styled_output(f"Successfully set up sightings page with {location_count} locations")
        utils.styled_output(f"Sightings map available at: /sightings/")
        utils.styled_output(f"Admin available at: /admin/")

    @staticmethod
    def _get_parent_page(utils: WagtailSetupUtils) -> Page | None:
        """Get the parent page for the sightings map (homepage or root)"""
        try:
            homepage = HomePage.objects.live().first()
            if homepage:
                utils.styled_output(f"Using homepage as parent: {homepage.title}")
                return homepage
        except Exception:
            pass

        # Fallback to root page
        root_page = Page.get_first_root_node()
        if not root_page:
            utils.styled_output("No root page found", "ERROR")
            return None

        utils.styled_output(f"Using root page as parent: {root_page.title}")
        return root_page

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

            <p>Click on the markers to learn more about each sighting, or use your location to find
            nearby unicorn activity in your area.</p>
            """,
            zoom_level=6,
        )

        try:
            utils.create_and_publish_page(parent_page, map_page)
            return map_page
        except Exception as e:
            utils.styled_output(f"Failed to create map page: {e}", "ERROR")
            # List existing children to help debug
            children = parent_page.get_children()
            utils.styled_output("Existing child pages:")
            for child in children:
                utils.styled_output(
                    f"  - {child.title} (slug: {child.slug}, type: {type(child).__name__})"
                )
            return None

    @staticmethod
    def _load_location_fixtures(utils: WagtailSetupUtils) -> None:
        """Load location fixtures"""
        utils.styled_output("Loading location fixtures...")

        try:
            # Check if fixtures file exists
            fixtures_file = "apps/sightings/fixtures/sightings.json"

            # Try to load the fixtures
            management.call_command("loaddata", "sightings.json", app_label="sightings")
            utils.styled_output(f"  - Successfully loaded location fixtures")

        except Exception as e:
            utils.styled_output(f"Failed to load fixtures: {e}", "WARNING")
            utils.styled_output("Creating sample locations manually...", "WARNING")
