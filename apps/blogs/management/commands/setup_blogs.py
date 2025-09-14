import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import IntegrityError

import frontmatter
import markdown
from PIL import Image as PILImage
from wagtail.models import Page

from apps.blog.models import BlogIndexPage, BlogPage
from apps.core.utils import WagtailSetupUtils
from apps.core.models import CustomImage


class Command(BaseCommand):
    help = "Create blog structure and import posts from markdown files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-file",
            type=str,
            default="apps/blog/content/blog_index.yaml",
            help="The file containing the blog index content",
        )
        parser.add_argument(
            "--content-dir",
            type=str,
            default="apps/blog/content/posts",
            help="Directory containing markdown files",
        )
        parser.add_argument(
            "--images-dir",
            type=str,
            default="apps/blog/content/images",
            help="Directory containing images",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion of existing blog pages, even if they're not BlogIndexPage types",
        )

    def handle(self, *args, **options):
        content_file = Path(options["content_file"])
        content_dir = Path(options["content_dir"])
        images_dir = Path(options["images_dir"])
        force = options["force"]
        utils = WagtailSetupUtils(self)

        if not utils.check_model_tables_exist([BlogPage, BlogIndexPage]):
            utils.styled_output(
                "Blog tables don't exist. Please run 'python manage.py makemigrations blog' "
                "and 'python manage.py migrate' first.",
                "WARNING",
            )
            return

        parent_page = utils.get_parent_page()
        if not parent_page:
            return

        utils.styled_output("Cleaning up existing blog content...")
        utils.cleanup_pages_by_type([BlogPage, BlogIndexPage])

        if not utils.check_slug_availability(parent_page, "blog", force):
            return

        blog_index = self._create_blog_index(content_file, utils, parent_page)
        if not blog_index:
            return

        self._import_markdown_files(utils, blog_index, content_dir, images_dir)

        utils.styled_output(f"Successfully imported {BlogPage.objects.count()} blog posts")
        utils.styled_output("Blog available at: /blog/")
        utils.styled_output("Admin available at: /admin/")

    @staticmethod
    def _create_blog_index(
        content_file: Path, utils: WagtailSetupUtils, parent_page: Page
    ) -> Page | None:
        """Create the blog index page"""
        utils.styled_output("Creating blog index page...")

        blog_index_data = utils.load_page_content(content_file, "blog_index")
        blog_index = BlogIndexPage(**blog_index_data)

        try:
            utils.create_and_publish_page(parent_page, blog_index)
        except (ValidationError, IntegrityError, PermissionDenied) as e:
            utils.styled_output(f"Failed to create blog index: {e}", "ERROR")
            return None
        else:
            return blog_index

    def _import_markdown_files(
        self, utils: WagtailSetupUtils, blog_index: Page, content_dir: Path, images_dir: Path
    ) -> None:
        """Import markdown files as blog posts"""
        if not content_dir.exists():
            utils.styled_output(f"Content directory not found: {content_dir}", "WARNING")
            return

        markdown_files = [f.name for f in content_dir.iterdir() if f.suffix == ".md"]

        if not markdown_files:
            utils.styled_output(f"No markdown files found in {content_dir}", "WARNING")
            return

        utils.styled_output(f"Found {len(markdown_files)} markdown files")

        for filename in markdown_files:
            file_path = content_dir / filename
            self._import_single_post(utils, blog_index, file_path, filename, images_dir)

    def _import_single_post(
        self,
        utils: WagtailSetupUtils,
        blog_index: Page,
        file_path: Path,
        filename: str,
        images_dir: Path,
    ) -> None:
        """Import a single markdown file as a blog post"""
        try:
            with file_path.open(encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Extract metadata from frontmatter
            title = post.metadata.get(
                "title", filename.replace(".md", "").replace("-", " ").title()
            )
            slug = post.metadata.get("slug", filename.replace(".md", ""))
            date_str = post.metadata.get("date")
            intro = post.metadata.get("intro", "")
            featured_image_name = str(post.metadata.get("featured_image"))
            featured_image_alt = str(post.metadata.get("featured_image_alt", ""))
            featured_image_caption = str(post.metadata.get("featured_image_caption", ""))

            date_obj = self._parse_date(date_str)

            # Convert markdown to HTML
            md = markdown.Markdown(extensions=["extra", "codehilite"])
            body_html = md.convert(post.content)

            featured_image = None
            if featured_image_name and images_dir.exists():
                featured_image = self._import_image(
                    utils,
                    featured_image_name,
                    images_dir,
                    featured_image_alt,
                    featured_image_caption,
                )

            blog_post = BlogPage(
                title=title,
                slug=slug,
                date=date_obj,
                intro=intro,
                body=body_html,
                featured_image=featured_image,
            )

            utils.create_and_publish_page(blog_index, blog_post)
            utils.styled_output(f"\t- Imported: {title}")

        except (OSError, UnicodeDecodeError) as e:
            utils.styled_output(f"Failed to read file {filename}: {e}", "ERROR")
        except (ValidationError, IntegrityError) as e:
            utils.styled_output(f"Failed to create blog post from {filename}: {e}", "ERROR")
        except (ValueError, TypeError, AttributeError) as e:
            utils.styled_output(f"Failed to process content in {filename}: {e}", "ERROR")

    @staticmethod
    def _parse_date(date_str: str | None) -> date:
        """Parse date from various formats"""
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC).date()
            except ValueError:
                try:
                    return (
                        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).date()
                    )
                except ValueError:
                    return datetime.now(UTC).date()
        else:
            return datetime.now(UTC).date()

    def _import_image(
        self,
        utils: WagtailSetupUtils,
        image_name: str,
        images_dir: Path,
        alt_text: str = "",
        caption: str = "",
    ) -> "CustomImage | None":
        """Import and compress an image file into Wagtail's image library"""
        image_path = Path(images_dir) / image_name

        if not Path.exists(image_path):
            utils.styled_output(f"Image not found: {image_path}", "WARNING")
            return None

        try:
            # Check if image already exists
            existing_image = CustomImage.objects.filter(title=image_name).first()
            if existing_image:

                if alt_text and not existing_image.alt_text:
                    existing_image.alt_text = alt_text
                    existing_image.caption = caption
                    existing_image.save()
                    utils.styled_output(
                        f"\t- Updated existing image with alt: '{existing_image.alt_text}'"
                    )
                return existing_image

            compressed_image_path = self._compress_image(utils, image_path)

            file_path = compressed_image_path if compressed_image_path else image_path
            with file_path.open("rb") as f:
                image_file = ImageFile(f, name=image_name)
                wagtail_image = CustomImage(
                    title=image_name,
                    file=image_file,
                    alt_text=alt_text,
                    description=caption,
                )
                wagtail_image.save()
                utils.styled_output(f"\t- Saved image with alt: '{wagtail_image.alt_text}'")

            # Clean up temporary compressed file if created
            if compressed_image_path and compressed_image_path != image_path:
                Path.unlink(compressed_image_path)

            utils.styled_output(f"\t- Imported and compressed image: {image_name}")

        except OSError as e:
            utils.styled_output(f"Failed to read image file {image_name}: {e}", "ERROR")
            return None
        except (ValidationError, IntegrityError) as e:
            utils.styled_output(f"Failed to save image {image_name} to database: {e}", "ERROR")
            return None
        except (ValueError, TypeError) as e:
            utils.styled_output(f"Failed to process image {image_name}: {e}", "ERROR")
            return None
        else:
            return wagtail_image

    @staticmethod
    def _compress_image(utils: WagtailSetupUtils, image_path: Path) -> Path | None:
        """Compress an image using Pillow"""
        try:
            # Open the image
            with PILImage.open(image_path) as original_img:
                # Convert to RGB if necessary (for JPEG)
                processed_img = original_img
                if original_img.mode in ("RGBA", "LA", "P"):
                    processed_img = original_img.convert("RGB")

                # Calculate new dimensions (max 1920px width, maintain aspect ratio)
                max_width = 1920
                if processed_img.width > max_width:
                    ratio = max_width / processed_img.width
                    new_height = int(processed_img.height * ratio)
                    processed_img = processed_img.resize(
                        (max_width, new_height), PILImage.Resampling.LANCZOS
                    )

                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(temp_fd)

                # Save with compression
                processed_img.save(temp_path, "PNG", quality=85, optimize=True)

                return Path(temp_path)

        except OSError as e:
            utils.styled_output(f"Failed to open image file {image_path}: {e}", "WARNING")
            return None
        except (ValueError, TypeError) as e:
            utils.styled_output(f"Image processing failed for {image_path}: {e}", "WARNING")
            return None
