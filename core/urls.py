from django.urls import path
from .views import ScrapeView, ListView, TestView

urlpatterns = [
    path('scrape/', ScrapeView.as_view()),
    path('list/', ListView.as_view()),
    path('', TestView.as_view())
]