from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/project/(?P<project_id>\w+)/$', consumers.ProjectConsumer.as_asgi()),
    re_path(r'ws/story/(?P<story_id>\w+)/$', consumers.StoryConsumer.as_asgi()),
]
