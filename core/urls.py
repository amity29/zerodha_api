from django.urls import path
from .views import ScrapeView, ListView

urlpatterns = [
    path('scrape/', ScrapeView.as_view()),
    path('list/', ListView.as_view())
]