from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from apps.blog.models.blog_page_model import BlogPage


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = [
        *Page.content_panels,
        FieldPanel("intro"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        blog_pages = self.get_children().live().order_by("-first_published_at").specific()
        context["blog_pages"] = blog_pages
        return context

    def get_latest_blogs(self, limit=3):
        return BlogPage.objects.child_of(self).live().order_by("-first_published_at")[:limit]
