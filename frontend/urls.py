from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/disconnect-google/', views.disconnect_google, name='disconnect_google'),
    path('workspace/create/', views.create_workspace, name='create_workspace'),
    path('workspace/<int:workspace_id>/', views.workspace_view, name='workspace_view'),
    path('workspace/<int:workspace_id>/settings/', views.workspace_settings, name='workspace_settings'),
    path('workspace/<int:workspace_id>/rename/', views.rename_workspace, name='rename_workspace'),
    path('workspace/<int:workspace_id>/delete/', views.delete_workspace, name='delete_workspace'),
    path('workspace/<int:workspace_id>/remove-member/<int:user_id>/', views.remove_workspace_member, name='remove_workspace_member'),
    path('workspace/<int:workspace_id>/project/create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/', views.project_view, name='project_view'),
    path('project/<int:project_id>/settings/', views.project_settings, name='project_settings'),
    path('project/<int:project_id>/associate-repository/', views.associate_repository, name='associate_repository'),
    path('project/<int:project_id>/rename/', views.rename_project, name='rename_project'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/remove-member/<int:user_id>/', views.remove_project_member, name='remove_project_member'),
    path('project/<int:project_id>/story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.story_view, name='story_view'),
]
