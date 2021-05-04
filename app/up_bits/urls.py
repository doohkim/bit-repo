from django.contrib import admin
from django.urls import path, include

from up_bits.views import analytics_view

urlpatterns = [

    path('', analytics_view, )
]
