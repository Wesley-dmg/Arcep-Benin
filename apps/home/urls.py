# -*- encoding: utf-8 -*-
from django.urls import path
from apps.home import views

app_name = "home"

handler404 = 'apps.home.views.custom_page_not_found_view'
handler500 = 'apps.home.views.custom_error_view'

urlpatterns = [
    # index
    path('', views.index, name='home'),

    # Operateur URLs
    path('operateurs/', views.operateur_list, name='operateur_list'),
    path('operateur/create/', views.operateur_create, name='operateur_create'),
    path('operateur/<int:pk>/edit/', views.operateur_update, name='operateur_update'),    
    path('operateur/delete/<int:pk>/', views.operateur_delete, name='operateur_delete'),

    # Localite URLs
    path('get_communes/', views.get_communes, name='get_communes'),
    path('communes/', views.commune_list, name='commune_list'),
    path('communes/create/', views.commune_create, name='commune_create'),
    path('communes/<int:pk>/update/', views.commune_update, name='commune_update'),
    path('communes/<int:pk>/delete/', views.commune_delete, name='commune_delete'),

    path('localite/create/', views.localite_create, name='localite_create'),
    path('localite/update/<int:pk>/', views.localite_update, name='localite_update'),
    path('localite/delete/<int:pk>/', views.localite_delete, name='localite_delete'),
    
    # Emplacement URLs
    path('emplacements/ajouter/', views.emplacement_create, name='emplacement_create'),
    path('emplacement/update/<int:pk>/', views.emplacement_update, name='emplacement_update'),
    path('emplacements/supprimer/<int:pk>/', views.emplacement_delete, name='emplacement_delete_confirm'), 
    
    # URLs pour la gestion des technologies
    path('technologie/', views.technologie_list_create, name='technologie_list_create'),
    path('technologie/update/<int:pk>/', views.technologie_update, name='technologie_update'),
    path('technologie/delete/<int:pk>/', views.technologie_delete, name='technologie_delete'),

    # Site URLs
    path('site/', views.site_list, name='site_list'),
    path('site/<int:pk>/', views.site_detail, name='site_detail'),
    path('site/create/', views.site_create, name='site_create'),
    path('site/update/<int:pk>/', views.site_update, name='site_update'),
    path('site/delete/<int:pk>/', views.site_delete, name='site_delete'),
    path('delete-multiple-sites/', views.delete_multiple_sites, name='delete_multiple_sites'),

    # Conformité URLs
    path('conformite/add/<int:site_id>/', views.add_conformite, name='add_conformite'),
    path('conformite/update/<int:site_id>/', views.update_conformite, name='update_conformite'),
    path('conformite/delete/<int:site_id>/', views.delete_conformite, name='delete_conformite'),

    path('statistics/', views.statistics, name='statistics'),
    path('statistics/data/', views.get_statistics_data, name='get_statistics_data'),
    
    path('get_communes/', views.get_communes, name='get_communes'),     
    
    # File Upload URLs
    path('file-upload/', views.file_upload_view, name='file_upload'),

    #Cartographie daes  sites   
    path('maps/', views.map_view, name='map'),
    
    ]