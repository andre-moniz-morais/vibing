from django.urls import path
from . import api_views

urlpatterns = [
    path('api/story/<int:story_id>/state/', api_views.update_story_state, name='update_story_state'),
    path('api/story/<int:story_id>/points/', api_views.update_story_points, name='update_story_points'),
    path('api/story/<int:story_id>/assignees/', api_views.update_story_assignees, name='update_story_assignees'),
    path('api/story/<int:story_id>/title/', api_views.update_story_title, name='update_story_title'),
    path('api/project/<int:project_id>/story-order/', api_views.update_story_order, name='update_story_order'),
    path('api/upload/image/', api_views.upload_image, name='upload_image'),
    path('api/github/repos/', api_views.get_github_repos, name='get_github_repos'),
]
