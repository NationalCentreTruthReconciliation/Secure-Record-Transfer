from django.urls import path

from . import views

app_name = 'mockup'
urlpatterns = [
    path('', views.index, name='index'),
    path('transfer/', views.transfer, name='transfer')
]
