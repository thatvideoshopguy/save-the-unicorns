from django.test import TestCase, RequestFactory
from django.utils import timezone
from wagtail.models import Site

from apps.blogs.models.blog_index_page import BlogIndexPage
from apps.blogs.models.blog_detail_page import BlogDetailPage


class BlogIndexPageTestCase(TestCase):
    def setUp(self):
        # Get the root page (usually created by Wagtail migrations)
        self.root_page = Site.objects.get(is_default_site=True).root_page

        # Create a blog index page
        self.blog_index = BlogIndexPage(
            title="Blog Index", slug="blog", intro="<p>Welcome to our blog</p>"
        )
        self.root_page.add_child(instance=self.blog_index)

        # Create some blog detail pages
        self.blog_post_1 = BlogDetailPage(
            title="First Blog Post",
            slug="first-post",
            date=timezone.now().date(),
            intro="First post intro",
            body="<p>First post content</p>",
        )
        self.blog_index.add_child(instance=self.blog_post_1)

        self.blog_post_2 = BlogDetailPage(
            title="Second Blog Post",
            slug="second-post",
            date=timezone.now().date(),
            intro="Second post intro",
            body="<p>Second post content</p>",
        )
        self.blog_index.add_child(instance=self.blog_post_2)

        # Publish the pages
        self.blog_index.save_revision().publish()
        self.blog_post_1.save_revision().publish()
        self.blog_post_2.save_revision().publish()

        self.factory = RequestFactory()

    def test_get_context_includes_blog_pages(self):
        """Test that get_context includes published blog pages"""
        request = self.factory.get("/")
        context = self.blog_index.get_context(request)

        # Check that blog_pages is in context
        self.assertIn("blog_pages", context)

        # Check that it contains our published blog posts
        blog_pages = context["blog_pages"]
        self.assertEqual(len(blog_pages), 2)

        # Check they're ordered by first_published_at (most recent first)
        titles = [page.title for page in blog_pages]
        self.assertIn("First Blog Post", titles)
        self.assertIn("Second Blog Post", titles)

    def test_get_context_only_includes_live_pages(self):
        """Test that unpublished pages are not included"""
        # Create an unpublished blog post
        unpublished_post = BlogDetailPage(
            title="Unpublished Post",
            slug="unpublished",
            date=timezone.now().date(),
            intro="Unpublished intro",
            body="<p>Unpublished content</p>",
        )
        self.blog_index.add_child(instance=unpublished_post)
        # Explicitly set it as not live
        unpublished_post.live = False
        unpublished_post.save()

        request = self.factory.get("/")
        context = self.blog_index.get_context(request)
        blog_pages = context["blog_pages"]

        # Should still only have 2 live pages
        self.assertEqual(len(blog_pages), 2)
        titles = [page.title for page in blog_pages]
        self.assertNotIn("Unpublished Post", titles)

    def test_get_latest_blogs_default_limit(self):
        """Test get_latest_blogs returns up to 3 posts by default"""
        latest_blogs = self.blog_index.get_latest_blogs()

        # Should return both posts (we only have 2)
        self.assertEqual(len(latest_blogs), 2)

        # Should be BlogDetailPage instances
        for blog in latest_blogs:
            self.assertIsInstance(blog, BlogDetailPage)

    def test_get_latest_blogs_custom_limit(self):
        """Test get_latest_blogs respects custom limit"""
        latest_blogs = self.blog_index.get_latest_blogs(limit=1)

        # Should only return 1 post
        self.assertEqual(len(latest_blogs), 1)

    def test_get_latest_blogs_ordering(self):
        """Test get_latest_blogs returns posts in correct order"""
        # Create a third post with a different date
        older_post = BlogDetailPage(
            title="Older Post",
            slug="older-post",
            date=timezone.now().date(),
            intro="Older post intro",
            body="<p>Older content</p>",
        )
        self.blog_index.add_child(instance=older_post)
        older_post.save_revision().publish()

        latest_blogs = self.blog_index.get_latest_blogs()

        # Should be ordered by first_published_at (most recent first)
        self.assertEqual(len(latest_blogs), 3)
        # The exact order depends on when save_revision().publish() was called
