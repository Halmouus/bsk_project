from django.urls import path
from .views import CheckPrinterView

urlpatterns = [
    path('', CheckPrinterView.as_view(), name='check_printer'),
]