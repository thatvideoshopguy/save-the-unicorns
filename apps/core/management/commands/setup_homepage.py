from django.core.management.base import BaseCommand
from wagtail.models import Page, Site
from apps.core.models import HomePage
from apps.core.management import WagtailSetupUtils


class Command(BaseCommand):
    help = "Set up the homepage with initial content"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion of existing homepage and recreate it",
        )

    def handle(self, *args, **options):
        force = options["force"]
        utils = WagtailSetupUtils(self)

        utils.styled_output("Setting up homepage...")

        # Clean up existing content if force flag is used
        if force:
            utils.styled_output("Cleaning up existing content...")
            Site.objects.all().delete()
            Page.objects.all().delete()

        # Ensure page tree is healthy and get root page
        root_page = utils.ensure_page_tree_health()

        # Check for existing homepage
        existing_children = root_page.get_children()
        existing_homepage = existing_children.type(HomePage).first()
        existing_home_slug = existing_children.filter(slug="home").first()

        if existing_homepage and not force:
            utils.styled_output(
                f"Homepage already exists: {existing_homepage.title}. Use --force to recreate.",
                "WARNING",
            )
            self._setup_site_for_homepage(utils, existing_homepage)
            return

        if existing_home_slug and not force:
            utils.styled_output(
                f"A page with slug 'home' already exists: {existing_home_slug.title}. Use --force to recreate.",
                "WARNING",
            )
            return

        # Delete existing pages if force is used
        if force and (existing_homepage or existing_home_slug):
            if existing_homepage:
                utils.styled_output(f"Deleting existing homepage: {existing_homepage.title}")
                existing_homepage.delete()
            if existing_home_slug and existing_home_slug != existing_homepage:
                utils.styled_output(
                    f"Deleting existing page with slug 'home': {existing_home_slug.title}"
                )
                existing_home_slug.delete()

        # Create homepage with content
        utils.styled_output("Creating new homepage...")

        homepage = HomePage(
            title="Save The Unicorns",
            slug="home",
            about_text="""
            <p>Since the Middle Ages, our organisation has been keeping a watchful eye over these majestic creatures
            across their natural habitat amongst the Scottish Highlands and along the Cornish Beaches.</p>

            <p>Sadly, with each century that passes their numbers grow fewer. Soon, these mythical land narwhals may
            disappear forever, jeopardizing the delicate rainbow ecosystem.</p>

            <p>Our mission is to raise awareness and funds to create a private sanctuary for all unicorns.</p>
            """,
        )

        # Create and publish the homepage
        try:
            utils.create_and_publish_page(root_page, homepage)
        except Exception as e:
            utils.styled_output(f"Failed to create homepage: {e}", "ERROR")
            return

        self._setup_site_for_homepage(utils, homepage)

        utils.styled_output(
            f"\nHomepage setup complete!\n"
            f"   Homepage: http://localhost:8000/\n"
            f"   Admin: http://localhost:8000/admin/\n"
        )

    @staticmethod
    def _setup_site_for_homepage(utils: WagtailSetupUtils, homepage: Page) -> None:
        """Set up the site for the homepage"""
        utils.setup_default_site(
            root_page=homepage, site_name="Save The Unicorns", hostname="localhost", port=8000
        )
