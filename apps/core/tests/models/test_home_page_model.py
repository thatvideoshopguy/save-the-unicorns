from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.utils import timezone
from wagtail.models import Site

from apps.core.models.home_page_model import HomePage
from apps.blogs.models import BlogIndexPage, BlogDetailPage



class HomePageModelTestCase(TestCase):
    def setUp(self):
        self.root_page = Site.objects.get(is_default_site=True).root_page
        self.factory = RequestFactory()

        # Create home page
        self.home_page = HomePage(
            title="Home",
            slug="home",
            about_text="<p>Welcome to our site</p>"
        )
        self.root_page.add_child(instance=self.home_page)
        self.home_page.save_revision().publish()

    def test_get_context_with_blog_index_and_posts(self):
        """Test get_context includes latest blogs when blog index exists with posts"""
        # Create blog index as child of home page
        blog_index = BlogIndexPage(
            title="Blog",
            slug="blog",
            intro="<p>Our blog</p>"
        )
        self.home_page.add_child(instance=blog_index)
        blog_index.save_revision().publish()

        # Create blog posts
        blog_post_1 = BlogDetailPage(
            title="First Post",
            slug="first-post",
            date=timezone.now().date(),
            intro="First intro",
            body="<p>First content</p>"
        )
        blog_index.add_child(instance=blog_post_1)
        blog_post_1.save_revision().publish()

        blog_post_2 = BlogDetailPage(
            title="Second Post",
            slug="second-post",
            date=timezone.now().date(),
            intro="Second intro",
            body="<p>Second content</p>"
        )
        blog_index.add_child(instance=blog_post_2)
        blog_post_2.save_revision().publish()

        request = self.factory.get('/')
        context = self.home_page.get_context(request)

        self.assertIn('latest_blogs', context)
        self.assertEqual(len(context['latest_blogs']), 2)

    def test_get_context_with_blog_index_no_posts(self):
        """Test get_context with blog index but no posts"""
        # Create empty blog index
        blog_index = BlogIndexPage(
            title="Blog",
            slug="blog",
            intro="<p>Our blog</p>"
        )
        self.home_page.add_child(instance=blog_index)
        blog_index.save_revision().publish()

        request = self.factory.get('/')
        context = self.home_page.get_context(request)

        self.assertIn('latest_blogs', context)
        self.assertEqual(len(context['latest_blogs']), 0)

    def test_get_context_without_blog_index(self):
        """Test get_context when no blog index exists"""
        request = self.factory.get('/')
        context = self.home_page.get_context(request)

        self.assertIn('latest_blogs', context)
        self.assertEqual(context['latest_blogs'], [])

    def test_get_context_with_exception_handling(self):
        """Test get_context handles exceptions gracefully"""
        # This tests the except block (lines 21-22)
        with patch.object(self.home_page, 'get_children') as mock_get_children:
            mock_get_children.side_effect = AttributeError("Test error")

            request = self.factory.get('/')
            context = self.home_page.get_context(request)

            self.assertIn('latest_blogs', context)
            self.assertEqual(context['latest_blogs'], [])

