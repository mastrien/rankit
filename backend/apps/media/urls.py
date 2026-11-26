"""URL routing for Rankit media catalog endpoints."""

from django.urls import path

from .views import MediaCategoriesView, MediaDetailView, MediaSearchView

urlpatterns = [
    path("categories/", MediaCategoriesView.as_view(), name="media-categories"),
    path("search/", MediaSearchView.as_view(), name="media-search"),
    path("<str:category>/<str:external_id>/", MediaDetailView.as_view(), name="media-detail"),
]
