from django.urls import path
from ratestask import views

urlpatterns = [
    path('', views.average_price_list, name="average_price_list"),
]