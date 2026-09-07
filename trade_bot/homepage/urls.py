from django.urls import path

from homepage.views import home_view

app_name = "homepage"

urlpatterns = [
    path("", home_view, name="homepage"),
]
