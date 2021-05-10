from django.urls import path
from .views import ScrapeView, ListView, TestView, DeleteView

urlpatterns = [
    path('scrape/', ScrapeView.as_view(), name='scrape'),
    path('list/', ListView.as_view(), name='list'),
    path('delete/', DeleteView.as_view(), name='delete'),
    path('', TestView.as_view(), name='test')
]