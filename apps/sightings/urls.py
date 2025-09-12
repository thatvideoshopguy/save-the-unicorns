from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    # GeoJSON API endpoints
    path('api/locations.geojson', views.LocationsGeoJSONView.as_view(), name='locations_geojson'),
    path('api/nearby/', views.NearbyLocationsView.as_view(), name='nearby_locations'),
    path('api/bounds/', views.LocationsWithinBoundsView.as_view(), name='locations_within_bounds'),

    # Alternative map page view
    path('map/', views.MapPageView.as_view(), name='map_view'),
]
