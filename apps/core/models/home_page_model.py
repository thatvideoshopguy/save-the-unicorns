from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from apps.blog.models import BlogIndexPage


class HomePage(Page):
    about_text = RichTextField()
    content_panels = [
        *Page.content_panels,
        FieldPanel("about_text"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)

        try:
            blog_index = self.get_children().type(BlogIndexPage).live().specific().first()
            context["latest_blogs"] = blog_index.get_latest_blogs(3) if blog_index else []
        except (AttributeError, BlogIndexPage.DoesNotExist):
            context["latest_blogs"] = []

        return context

    class Meta:
        verbose_name = "Home Page"
