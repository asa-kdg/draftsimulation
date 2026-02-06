from django.urls import path
from . import views

app_name = 'draft'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>/', views.detail, name='detail'),
    path('simulation/', views.simulation_play, name='simulation_play'),
    path('simulation/start/', views.simulation_start, name='simulation_start'),
    path('simulation/pick/', views.pick_player, name='pick_player'),
    path('simulation/skip/', views.skip_team, name='skip_team'),
    path('simulation/result/', views.simulation_result, name='simulation_result'),
   



]