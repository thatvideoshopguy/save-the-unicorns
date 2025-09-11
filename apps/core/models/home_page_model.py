from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from apps.blog.models import BlogPage, BlogIndexPage


class HomePage(Page):
    """
    Homepage model that displays latest blog posts
    """

    about_text = RichTextField(
        default="Since the Middle Ages, our organisation has been keep a watchful eye over theses majestic creatures..."
    )
    content_panels = Page.content_panels + [
        FieldPanel("about_text"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        # Get latest blog posts from any BlogIndexPage that's a child of this page
        try:
            blog_index = self.get_children().type(BlogIndexPage).live().first()
            if blog_index:
                latest_blogs = (
                    BlogPage.objects.child_of(blog_index)
                    .live()
                    .order_by("-first_published_at")[:3]
                )
                context["latest_blogs"] = latest_blogs
            else:
                context["latest_blogs"] = []
        except:
            context["latest_blogs"] = []

        return context

    class Meta:
        verbose_name = "Home Page"
