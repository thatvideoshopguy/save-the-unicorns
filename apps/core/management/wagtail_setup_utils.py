from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import DatabaseError, ProgrammingError, models

import yaml
from wagtail.models import Page, Site

from apps.core.models import HomePage


class WagtailSetupUtils:
    def __init__(self, command_instance):
        self.command = command_instance

    def styled_output(self, message: str, style: str = "SUCCESS") -> None:
        """Wrapper for consistent styled console output"""
        if style == "SUCCESS":
            self.command.stdout.write(self.command.style.SUCCESS(message))
        elif style == "ERROR":
            self.command.stdout.write(self.command.style.ERROR(message))
        elif style == "WARNING":
            self.command.stdout.write(self.command.style.WARNING(message))
        else:
            self.command.stdout.write(message)

    def ensure_page_tree_health(self) -> Page:
        """Ensure page tree structure is healthy and return root page"""
        self.styled_output("Fixing page tree structure...")

        try:
            call_command("fixtree")
            self.styled_output("Page tree fixed")
        except (
            DatabaseError,
            ProgrammingError,
        ) as e:
            self.styled_output(f"Warning: Could not fix tree: {e}", "WARNING")

        return self.get_or_create_root_page()

    def get_or_create_root_page(self) -> Page:
        """Get existing root page or create one if needed"""
        try:
            root_page = Page.get_first_root_node()
            if root_page:
                self.styled_output(f"Found existing root page: {root_page.title}")
                try:
                    children_count = root_page.get_children().count()
                    self.styled_output(f"Root page has {children_count} children")
                except (DatabaseError, ProgrammingError) as e:
                    self.styled_output(f"Root page tree structure is corrupted: {e}", "ERROR")
                else:
                    return root_page
            else:
                self.styled_output("No root page found")
        except (DatabaseError, ProgrammingError) as e:
            self.styled_output(f"Error getting root page: {e}", "ERROR")

        self.styled_output("Creating new root page...")
        try:
            Page.objects.all().delete()
            root_page = Page.add_root(title="Root", slug="root")
            self.styled_output(f"Created root page: {root_page}")
        except (DatabaseError, ProgrammingError) as e:
            self.styled_output(f"Failed to create root page: {e}", "ERROR")
            raise
        else:
            return root_page

    def cleanup_pages_by_type(self, page_types: list[type[models.Model]]) -> dict[str, int]:
        """Generic cleanup for pages by type"""
        deleted_counts = {}

        for page_type in page_types:
            count = page_type.objects.count()
            if count > 0:
                page_type.objects.all().delete()
                deleted_counts[page_type.__name__] = count
                self.styled_output(f"  - Deleted {count} {page_type.__name__} instances")

        return deleted_counts

    def check_slug_availability(self, parent_page: Page, slug: str, force: bool = False) -> bool:
        """Check if a slug is available under parent, handle conflicts"""
        existing_page = parent_page.get_children().filter(slug=slug).first()

        if existing_page:
            if force:
                self.styled_output(
                    f"  - Found existing page with slug '{slug}': {existing_page}. "
                    f"Deleting due to --force flag."
                )
                existing_page.delete()
                return True
            self.styled_output(
                f"A page with slug '{slug}' already exists: {existing_page}\n"
                f"Use --force flag to delete it, or delete it manually in the admin.",
                "ERROR",
            )
            return False

        return True

    def setup_default_site(
        self, root_page: Page, site_name: str, hostname: str, port: int
    ) -> Site:
        """Set up or update the default Wagtail site"""
        try:
            site, created = Site.objects.get_or_create(
                hostname=hostname,
                defaults={
                    "port": port,
                    "root_page": root_page,
                    "is_default_site": True,
                    "site_name": site_name,
                },
            )

            if not created:
                site.root_page = root_page
                site.is_default_site = True
                site.site_name = site_name
                site.save()

            action = "Created" if created else "Updated"
            self.styled_output(f"{action} site: {site}")
        except (DatabaseError, ProgrammingError) as e:
            self.styled_output(f"Failed to setup site: {e}", "ERROR")
            raise
        else:
            return site  # Fix: Moved to else block

    def debug_page_tree(self) -> None:
        """Debug the page tree structure"""
        try:
            all_pages = Page.objects.all().order_by("path")
            self.styled_output("All pages in database:")
            for page in all_pages:
                self.styled_output(
                    f"  ID: {page.id}, Title: {page.title}, Slug: {page.slug}, "
                    f"Depth: {page.depth}, Path: {page.path}, Type: {type(page).__name__}"
                )
        except (DatabaseError, ProgrammingError) as e:
            self.styled_output(f"Error debugging page tree: {e}", "ERROR")

    @staticmethod
    def check_model_tables_exist(django_models: list[type[models.Model]]) -> bool:
        """Check if database tables exist for given models"""
        try:
            for model in django_models:
                model.objects.count()
        except (DatabaseError, ProgrammingError, ImproperlyConfigured):
            return False
        else:
            return True

    def create_and_publish_page(
        self, parent_page: Page, page_instance: Page, alternative_method: bool = False
    ) -> Page:
        """Create and publish a page with error handling"""
        try:
            if alternative_method:
                page_instance.save()
                parent_page.add_child(instance=page_instance)
            else:
                parent_page.add_child(instance=page_instance)

            revision = page_instance.save_revision()
            revision.publish()

            self.styled_output(f"Created and published: {page_instance.title}")
        except (DatabaseError, ProgrammingError) as e:
            if not alternative_method:
                self.styled_output(
                    f"Standard method failed: {e}. Trying alternative...", "WARNING"
                )
                return self.create_and_publish_page(
                    parent_page, page_instance, alternative_method=True
                )
            self.styled_output(f"Alternative method also failed: {e}", "ERROR")
            self.debug_page_tree()
            raise
        else:
            return page_instance

    def get_parent_page(self) -> Page | None:
        """Get the parent page for the blog (homepage or root)"""
        try:
            homepage = HomePage.objects.live().first()
            if homepage:
                self.styled_output(f"Using homepage as parent: {homepage.title}")
                return homepage
        except ImportError:
            pass

        # Fallback to root page
        root_page = Page.get_first_root_node()
        if not root_page:
            self.styled_output("No root page found", "ERROR")
            return None

        self.styled_output(f"Using root page as parent: {root_page.title}")
        return root_page

    @staticmethod
    def load_page_content(content_file: Path, root_key: str) -> dict:
        """Load page contents of yaml file into memory"""
        with content_file.open() as f:
            return yaml.safe_load(f)[root_key]
