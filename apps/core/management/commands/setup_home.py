from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from wagtail.models import Page, Site

from apps.core.utils import WagtailSetupUtils
from apps.core.models import HomePage


class Command(BaseCommand):
    help = "Set up the home page with initial content"

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-file",
            type=str,
            default="apps/core/content/home.yaml",
            help="The file containing the home index content",
        )

    def handle(self, *args, **options):
        content_file = Path(options["content_file"])
        utils = WagtailSetupUtils(self)

        utils.styled_output("Setting up homepage...")

        # Clean up existing content
        utils.styled_output("Cleaning up existing content...")
        Site.objects.all().delete()
        Page.objects.all().delete()

        root_page = utils.ensure_page_tree_health()

        existing_children = root_page.get_children()
        existing_homepage = existing_children.type(HomePage).first()
        existing_home_slug = existing_children.filter(slug="home").first()

        if existing_homepage:
            utils.styled_output(f"Deleting existing homepage: {existing_homepage.title}")
            existing_homepage.delete()
        if existing_home_slug and existing_home_slug != existing_homepage:
            utils.styled_output(
                f"Deleting existing page with slug 'home': {existing_home_slug.title}"
            )
            existing_home_slug.delete()

        utils.styled_output("Creating new homepage...")

        homepage_data = utils.load_page_content(content_file, "homepage")
        homepage = HomePage(**homepage_data)

        try:
            utils.create_and_publish_page(root_page, homepage)
        except (ValidationError, IntegrityError) as e:
            utils.styled_output(f"Failed to create homepage: {e}", "ERROR")
            return

        self._setup_site_for_homepage(utils, homepage)

        utils.styled_output(
            "\nHomepage setup complete!\n"
            "   Homepage: http://localhost:8000/\n"
            "   Admin: http://localhost:8000/admin/\n"
        )

    @staticmethod
    def _setup_site_for_homepage(utils: WagtailSetupUtils, homepage: Page) -> None:
        """Set up the site for the homepage"""
        utils.setup_default_site(
            root_page=homepage, site_name="Save The Unicorns", hostname="localhost", port=8000
        )
