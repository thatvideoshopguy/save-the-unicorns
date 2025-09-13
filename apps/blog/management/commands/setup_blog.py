import os
import tempfile
from datetime import date, datetime
import frontmatter
import markdown
from PIL import Image as PILImage
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.models import Page
from apps.blog.models import BlogIndexPage, BlogPage
from apps.core.management import WagtailSetupUtils
from apps.core.models import CustomImage


class Command(BaseCommand):
    help = "Create blog structure and import posts from markdown files"

    def add_arguments(self, parser):
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
        content_dir = options["content_dir"]
        images_dir = options["images_dir"]
        force = options["force"]
        utils = WagtailSetupUtils(self)

        # Check if tables exist before trying to delete
        if not utils.check_model_tables_exist([BlogPage, BlogIndexPage]):
            utils.styled_output(
                "Blog tables don't exist. Please run 'python manage.py makemigrations blog' and 'python manage.py migrate' first.",
                "WARNING",
            )
            return

        parent_page = utils.get_parent_page
        if not parent_page:
            return

        # Clean up existing blog content
        utils.styled_output("Cleaning up existing blog content...")
        utils.cleanup_pages_by_type([BlogPage, BlogIndexPage])

        # Check slug availability
        if not utils.check_slug_availability(parent_page, "blog", force):
            return

        # Create blog index
        blog_index = self._create_blog_index(utils, parent_page)
        if not blog_index:
            return

        # Import markdown files
        self._import_markdown_files(utils, blog_index, content_dir, images_dir)

        utils.styled_output(f"Successfully imported {BlogPage.objects.count()} blog posts")
        utils.styled_output(f"Blog available at: /blog/")
        utils.styled_output(f"Admin available at: /admin/")



    @staticmethod
    def _create_blog_index(utils: WagtailSetupUtils, parent_page: Page) -> Page | None:
        """Create the blog index page"""
        utils.styled_output("Creating blog index page...")

        blog_index = BlogIndexPage(
            title="Blog",
            slug="blog",
            intro="<p>Latest news and insights about unicorn conservation efforts and sightings.</p>",
        )

        try:
            utils.create_and_publish_page(parent_page, blog_index)
            return blog_index
        except Exception as e:
            utils.styled_output(f"Failed to create blog index: {e}", "ERROR")
            return None

    def _import_markdown_files(
        self, utils: WagtailSetupUtils, blog_index: Page, content_dir: str, images_dir: str
    ) -> None:
        """Import markdown files as blog posts"""
        if not os.path.exists(content_dir):
            utils.styled_output(f"Content directory not found: {content_dir}", "WARNING")
            return

        markdown_files = [f for f in os.listdir(content_dir) if f.endswith(".md")]

        if not markdown_files:
            utils.styled_output(f"No markdown files found in {content_dir}", "WARNING")
            return

        utils.styled_output(f"Found {len(markdown_files)} markdown files")

        for filename in markdown_files:
            file_path = os.path.join(content_dir, filename)
            self._import_single_post(utils, blog_index, file_path, filename, images_dir)

    def _import_single_post(self, utils, blog_index, file_path, filename, images_dir):
        """Import a single markdown file as a blog post"""
        try:
            # Parse the markdown file with frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
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

            # Parse date
            date_obj = self._parse_date(date_str)

            # Convert markdown to HTML
            md = markdown.Markdown(extensions=["extra", "codehilite"])
            body_html = md.convert(post.content)

            # Handle featured image with alt text
            featured_image = None
            if featured_image_name and os.path.exists(images_dir):
                featured_image = self._import_image(
                    utils,
                    featured_image_name,
                    images_dir,
                    featured_image_alt,
                    featured_image_caption,
                )

            # Create blog post
            blog_post = BlogPage(
                title=title,
                slug=slug,
                date=date_obj,
                intro=intro,
                body=body_html,
                featured_image=featured_image,
            )

            # Create and publish the post
            utils.create_and_publish_page(blog_index, blog_post)
            utils.styled_output(f"  - Imported: {title}")
            utils.styled_output(f"Debug - Alt text for {filename}: '{featured_image_alt}'")

        except Exception as e:
            utils.styled_output(f"Failed to import {filename}: {e}", "ERROR")

    @staticmethod
    def _parse_date(date_str: str | date | None) -> date:
        """Parse date from various formats"""
        if date_str:
            if isinstance(date_str, str):
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
                    except ValueError:
                        return datetime.now().date()
            else:
                return date_str
        return datetime.now().date()

    def _import_image(
        self,
        utils: WagtailSetupUtils,
        image_name: str,
        images_dir: str,
        alt_text: str = "",
        caption: str = "",
    ) -> "CustomImage | None":
        """Import and compress an image file into Wagtail's image library"""
        image_path = os.path.join(images_dir, image_name)

        if not os.path.exists(image_path):
            utils.styled_output(f"Image not found: {image_path}", "WARNING")
            return None

        try:
            # Check if image already exists
            existing_image = CustomImage.objects.filter(title=image_name).first()
            if existing_image:
                # Update alt text if provided and not already set
                if alt_text and not existing_image.alt_text:
                    existing_image.alt_text = alt_text
                    existing_image.caption = caption
                    existing_image.save()
                    utils.styled_output(
                        f"    - Updated existing image with alt: '{existing_image.alt_text}'"
                    )
                return existing_image

            # Compress image before importing
            compressed_image_path = self._compress_image(utils, image_path)

            # Create new image with alt text
            with open(compressed_image_path or image_path, "rb") as f:
                image_file = ImageFile(f, name=image_name)
                wagtail_image = CustomImage(
                    title=image_name,
                    file=image_file,
                    alt_text=alt_text,
                    description=caption,
                )
                wagtail_image.save()
                utils.styled_output(f"    - Saved image with alt: '{wagtail_image.alt_text}'")

            # Clean up temporary compressed file if created
            if compressed_image_path and compressed_image_path != image_path:
                os.remove(compressed_image_path)

            utils.styled_output(f"    - Imported and compressed image: {image_name}")
            return wagtail_image

        except Exception as e:
            utils.styled_output(f"Failed to import image {image_name}: {e}", "ERROR")
            # Print the full traceback for debugging
            import traceback

            utils.styled_output(f"Full error: {traceback.format_exc()}", "ERROR")
            return None

    @staticmethod
    def _compress_image(utils: WagtailSetupUtils, image_path: str) -> str | None:
        """Compress an image using Pillow"""
        try:
            # Open the image
            with PILImage.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Calculate new dimensions (max 1920px width, maintain aspect ratio)
                max_width = 1920
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)

                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(temp_fd)

                # Save with compression
                img.save(temp_path, "PNG", quality=85, optimize=True)

                return temp_path

        except Exception as e:
            utils.styled_output(f"Image compression failed for {image_path}: {e}", "WARNING")
            return None
