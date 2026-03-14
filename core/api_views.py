from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Story, StoryUser, User
from .tasks import run_gemini_cli_develop, run_gemini_cli_review
import uuid
import os

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_story_state(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    new_state = request.data.get('state')
    
    # Needs to be a valid state
    valid_states = dict(Story.STATE_CHOICES).keys()
    if new_state not in valid_states:
        return Response({'success': False, 'error': 'Invalid state'}, status=400)
    
    story.state = new_state
    story.save()
    
    # Trigger AI workflows based on state
    if new_state == 'Develop':
        run_gemini_cli_develop.delay(story.id, request.user.id)
    elif new_state == 'In review':
        run_gemini_cli_review.delay(story.id, request.user.id)
        
    return Response({'success': True, 'state': new_state})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_story_points(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    points = request.data.get('story_points', 0)
    try:
        story.story_points = int(points)
        story.save()
        return Response({'success': True, 'story_points': story.story_points})
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid points value'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_story_assignees(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    user_ids = request.data.get('user_ids', [])
    
    # Clear existing assignees and set new ones
    StoryUser.objects.filter(story=story).delete()
    for user_id in user_ids:
        user = User.objects.filter(id=user_id).first()
        if user:
            StoryUser.objects.get_or_create(story=story, user=user)
    
    assignees = [{'id': a.user.id, 'username': a.user.username} for a in story.assignees.all()]
    return Response({'success': True, 'assignees': assignees})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_story_title(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    title = request.data.get('title', '').strip()
    if title:
        content = story.content or {}
        content['title'] = title
        story.content = content
        story.save()
        return Response({'success': True, 'title': title})
    return Response({'success': False, 'error': 'Title cannot be empty'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """Handle image uploads for Editor.js. Saves to S3 or local filesystem based on settings."""
    image = request.FILES.get('image')
    if not image:
        return Response({'success': 0}, status=400)

    # Generate unique filename
    ext = os.path.splitext(image.name)[1] or '.png'
    filename = f"uploads/editor/{uuid.uuid4().hex}{ext}"
    
    # Save using Django's default storage (S3 or local based on settings)
    saved_path = default_storage.save(filename, image)
    
    file_url = default_storage.url(saved_path)
    
    return Response({
        'success': 1,
        'file': {
            'url': file_url
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_story_order(request, project_id):
    from core.models import Project
    project = get_object_or_404(Project, id=project_id)
    ordered_ids = request.data.get('ordered_ids', [])
    
    for index, story_id in enumerate(ordered_ids):
        story = Story.objects.filter(id=story_id, project=project).first()
        if story:
            story.order = index * 10
            story.save()
            
    return Response({'success': True})

import requests

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_github_repos(request):
    token = request.user.github_token
    if not token:
        return Response({'success': False, 'error': 'No GitHub token found. Please re-authenticate.'}, status=400)
        
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get('https://api.github.com/user/repos?per_page=100&sort=updated', headers=headers)
    
    if response.status_code == 200:
        repos = [{'id': repo['id'], 'name': repo['full_name']} for repo in response.json()]
        return Response({'success': True, 'repos': repos})
    else:
        return Response({'success': False, 'error': 'Failed to fetch repositories from GitHub.'}, status=response.status_code)

