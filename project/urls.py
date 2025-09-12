from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.static import serve
from apps.core.views import server_error
from apps.donations.views import donation_view

admin.site.site_title = "Save The Unicorns"
admin.site.site_header = "Save The Unicorns"

handler500 = server_error

urlpatterns = [
    path(
        "robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")
    ),
    path("_health/", include("watchman.urls")),

    path('donate/', donation_view, name='donate'),

    path("admin/", include("wagtail.admin.urls")),
    path("documents/", include("wagtail.documents.urls")),
    # All pages route through Wagtail
    path("", include("wagtail.urls")),
]

# Make it easier to see a 404-page under debug
if settings.DEBUG:
    from django.views.defaults import page_not_found

    urlpatterns += [path("404/", page_not_found, {"exception": None})]

# Only enable debug toolbar if it's an installed app
if apps.is_installed("debug_toolbar"):
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

# Serving static/media under debug
urlpatterns += static(settings.STATIC_URL, never_cache(staticfiles_serve))
urlpatterns += static(settings.MEDIA_URL, never_cache(serve), document_root=settings.MEDIA_ROOT)
