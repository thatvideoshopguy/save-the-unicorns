from django.test import TestCase
from django.utils import timezone
from wagtail.models import Site

from apps.blogs.models.blog_index_page import BlogIndexPage
from apps.blogs.models.blog_detail_page import BlogDetailPage


class BlogDetailPageTestCase(TestCase):
    def setUp(self):
        self.root_page = Site.objects.get(is_default_site=True).root_page

        # Create blog index and detail page
        self.blog_index = BlogIndexPage(
            title="Blog Index",
            slug="blog"
        )
        self.root_page.add_child(instance=self.blog_index)

        self.blog_detail = BlogDetailPage(
            title="Test Blog Post",
            slug="test-post",
            date=timezone.now().date(),
            intro="Test intro",
            body="<p>Test content</p>"
        )
        self.blog_index.add_child(instance=self.blog_detail)

    def test_blog_detail_creation(self):
        """Test basic blog detail page creation"""
        self.assertEqual(self.blog_detail.title, "Test Blog Post")
        self.assertEqual(self.blog_detail.intro, "Test intro")
        self.assertIn("Test content", self.blog_detail.body)

    def test_blog_detail_template(self):
        """Test correct template is used"""
        self.assertEqual(self.blog_detail.template, "blogs/blog_detail.html")
