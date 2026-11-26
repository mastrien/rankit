"""URL routes for Rankit user profiles and follow graph."""

from django.urls import path

from .views import (
    FollowersListView,
    FollowingListView,
    FollowSuggestionsView,
    FollowUserView,
    ProfileDetailView,
    ProfilePresetsView,
    UpdateOwnProfileView,
)

urlpatterns = [
    path("presets/", ProfilePresetsView.as_view(), name="profile-presets"),
    path("me/", UpdateOwnProfileView.as_view(), name="profile-update-me"),
    path("<str:username>/", ProfileDetailView.as_view(), name="profile-detail"),
    path("<str:username>/follow/", FollowUserView.as_view(), name="profile-follow"),
    path("<str:username>/followers/", FollowersListView.as_view(), name="profile-followers"),
    path("<str:username>/following/", FollowingListView.as_view(), name="profile-following"),
    path(
        "<str:username>/suggestions/",
        FollowSuggestionsView.as_view(),
        name="profile-suggestions",
    ),
]
