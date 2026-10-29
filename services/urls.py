from django.urls import path
from .views import CategoryDetailView, ContactView, InformationView, MovingView, ServiceDetailView, ServiceListView

app_name = "services"
urlpatterns = [
    path("", ServiceListView.as_view(), name="list"),
    path("moving-shifting/", MovingView.as_view(), name="moving"),
    path("about/", InformationView.as_view(page="about"), name="about"),
    path("areas/", InformationView.as_view(page="areas"), name="areas"),
    path("faq/", InformationView.as_view(page="faq"), name="faq"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("category/<slug:slug>/", CategoryDetailView.as_view(), name="category"),
    path("<slug:slug>/", ServiceDetailView.as_view(), name="detail"),
]
