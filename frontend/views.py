from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'home.html')
    
@login_required
def settings_view(request):
    return render(request, 'settings.html')

from django.shortcuts import redirect
from django.contrib import messages
from core.models import Workspace, WorkspaceUser

@login_required
def disconnect_google(request):
    if request.method == 'POST':
        request.user.google_token = ''
        request.user.save()
        messages.success(request, 'Google account disconnected successfully.')
    return redirect('settings')

@login_required
def create_workspace(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            workspace = Workspace.objects.create(name=name)
            WorkspaceUser.objects.create(
                workspace=workspace,
                user=request.user,
                role='Admin'
            )
            messages.success(request, f'Workspace "{name}" created successfully.')
    return redirect('home')

@login_required
def workspace_view(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    
    ws_member = workspace.members.filter(user=request.user).first()
    has_project_access = ProjectUser.objects.filter(
        user=request.user, project__workspace=workspace
    ).exists()
    
    if not ws_member and not has_project_access:
        raise PermissionDenied("You do not have access to this workspace.")
    
    if ws_member:
        # Workspace member → can see all projects
        projects = workspace.projects.all()
    else:
        # Project-only member → can see only projects they have access to
        accessible_project_ids = ProjectUser.objects.filter(
            user=request.user, project__workspace=workspace
        ).values_list('project_id', flat=True)
        projects = workspace.projects.filter(id__in=accessible_project_ids)
    
    is_workspace_admin = ws_member.role == 'Admin' if ws_member else False
    can_create_project = ws_member.role in ('Admin', 'Editor') if ws_member else False
    
    return render(request, 'workspace.html', {
        'workspace': workspace,
        'projects': projects,
        'is_workspace_admin': is_workspace_admin,
        'can_create_project': can_create_project,
    })

import os
import subprocess
import shutil
from django.conf import settings

def _clone_repository(user, project, repo_name):
    token = user.github_token
    if not token:
        return False, "GitHub token missing."
        
    target_dir = os.path.join(settings.BASE_DIR, 'workspaces', str(project.workspace.id), str(project.id))
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
        
    os.makedirs(os.path.dirname(target_dir), exist_ok=True)
    
    clone_url = f"https://oauth2:{token}@github.com/{repo_name}.git"
    
    try:
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', clone_url, target_dir],
            capture_output=True,
            text=True,
            timeout=3600
        )
        if result.returncode == 0:
            return True, "Repository cloned successfully."
        else:
            return False, f"Git clone failed: {result.stderr}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

@login_required
def create_project(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if not workspace.members.filter(user=request.user, role__in=['Admin', 'Editor']).exists():
        raise PermissionDenied("You do not have permission to create projects in this workspace.")
        
    if request.method == 'POST':
        name = request.POST.get('name')
        repo_action = request.POST.get('repo_action', 'none')
        existing_repo = request.POST.get('existing_repo')
        new_repo_name = request.POST.get('new_repo_name')
        
        if name:
            project = Project.objects.create(
                name=name,
                workspace=workspace,
                created_by=request.user
            )
            
            repo_name = None
            if repo_action == 'existing' and existing_repo:
                repo_name = existing_repo
            elif repo_action == 'new' and new_repo_name:
                # Create the repository via GitHub API
                token = request.user.github_token
                if token:
                    headers = {
                        'Authorization': f'token {token}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    data = {'name': new_repo_name, 'private': True, 'auto_init': True}
                    import requests
                    response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
                    if response.status_code == 201:
                        repo_name = response.json()['full_name']
                    else:
                        messages.error(request, f"Failed to create GitHub repository. Project created without repository.")
                else:
                    messages.error(request, "Please Re-authenticate with GitHub to create repositories.")
            
            if repo_name:
                from core.models import ProjectRepository
                ProjectRepository.objects.create(project=project, repository=repo_name)
                
                # Clone the repository locally
                success, msg = _clone_repository(request.user, project, repo_name)
                if not success:
                    messages.warning(request, f'Project created, but repo clone failed: {msg}')
                else:
                    messages.success(request, f'Project "{name}" created and repository cloned successfully.')
            else:
                messages.success(request, f'Project "{name}" created successfully.')
                
            return redirect('project_view', project_id=project.id)
            
    return redirect('workspace_view', workspace_id=workspace.id)
    
from django.shortcuts import get_object_or_404
from core.models import Project
from django.core.exceptions import PermissionDenied

from django.db.models import Q

@login_required
def project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    has_workspace_access = project.workspace.members.filter(user=request.user).exists()
    has_project_access = hasattr(project, 'members') and project.members.filter(user=request.user).exists()
    
    if not has_workspace_access and not has_project_access:
        raise PermissionDenied("You do not have access to this project.")
        
    stories = project.stories.all().order_by('order')
    default_states = ['TODO', 'Develop', 'In review', 'Request changes', 'Done']
    
    # Determine user role (highest privilege wins)
    ws_member = project.workspace.members.filter(user=request.user).first()
    pj_member = project.members.filter(user=request.user).first() if hasattr(project, 'members') else None
    
    ws_role = ws_member.role if ws_member else None
    pj_role = pj_member.role if pj_member else None
    
    role_priority = {'Admin': 3, 'Editor': 2, 'Reader': 1}
    user_role = max([ws_role, pj_role], key=lambda r: role_priority.get(r, 0) if r else 0)
    
    is_project_admin = user_role == 'Admin'
    can_edit = user_role in ('Admin', 'Editor')
        
    return render(request, 'project.html', {
        'project': project,
        'stories': stories,
        'default_states': default_states,
        'is_project_admin': is_project_admin,
        'can_edit': can_edit,
        'workspace_members': project.workspace.members.select_related('user').all()
    })

from core.models import Story

@login_required
def story_view(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    project = story.project
    has_workspace_access = project.workspace.members.filter(user=request.user).exists()
    has_project_access = hasattr(project, 'members') and project.members.filter(user=request.user).exists()
    
    if not has_workspace_access and not has_project_access:
        raise PermissionDenied("You do not have access to this story.")
    
    # Determine role
    ws_member = project.workspace.members.filter(user=request.user).first()
    pj_member = project.members.filter(user=request.user).first() if hasattr(project, 'members') else None
    ws_role = ws_member.role if ws_member else None
    pj_role = pj_member.role if pj_member else None
    role_priority = {'Admin': 3, 'Editor': 2, 'Reader': 1}
    user_role = max([ws_role, pj_role], key=lambda r: role_priority.get(r, 0) if r else 0)
    can_edit = user_role in ('Admin', 'Editor')
    
    return render(request, 'story.html', {'story': story, 'can_edit': can_edit})

@login_required
def create_story(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Check permissions
    has_workspace_access = project.workspace.members.filter(user=request.user).exists()
    has_project_access = hasattr(project, 'members') and project.members.filter(user=request.user).exists()
    
    if not has_workspace_access and not has_project_access:
        raise PermissionDenied("You do not have permission to create a story in this project.")
        
    if request.method == 'POST':
        story = Story.objects.create(
            project=project,
            created_by=request.user,
            content={'title': 'Untitled Story'}
        )
        from django.urls import reverse
        return redirect(f"{reverse('project_view', args=[project.id])}#tab-backlog")
    from django.urls import reverse
    return redirect(f"{reverse('project_view', args=[project.id])}#tab-backlog")

from core.models import User, ProjectUser

@login_required
def workspace_settings(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if not workspace.members.filter(user=request.user, role='Admin').exists():
        raise PermissionDenied("Only workspace admins can access settings.")
        
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role', 'Reader')
        user_to_add = User.objects.filter(username=username).first()
        if user_to_add:
            WorkspaceUser.objects.update_or_create(
                workspace=workspace, user=user_to_add, defaults={'role': role}
            )
            messages.success(request, f"Added {username} to workspace.")
        else:
            messages.error(request, f"User {username} not found.")
        return redirect('workspace_settings', workspace_id=workspace.id)
        
    return render(request, 'workspace_settings.html', {'workspace': workspace})

@login_required
def project_settings(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    has_workspace_admin = project.workspace.members.filter(user=request.user, role='Admin').exists()
    has_project_admin = hasattr(project, 'members') and project.members.filter(user=request.user, role='Admin').exists()
    if not has_workspace_admin and not has_project_admin:
        raise PermissionDenied("Only admins can access project settings.")
        
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role', 'Reader')
        user_to_add = User.objects.filter(username=username).first()
        if user_to_add:
            ProjectUser.objects.update_or_create(
                project=project, user=user_to_add, defaults={'role': role}
            )
            messages.success(request, f"Added {username} to project.")
        else:
            messages.error(request, f"User {username} not found.")
        return redirect('project_settings', project_id=project.id)
        
    return render(request, 'project_settings.html', {'project': project})

@login_required
def associate_repository(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    has_workspace_admin = project.workspace.members.filter(user=request.user, role='Admin').exists()
    has_project_admin = hasattr(project, 'members') and project.members.filter(user=request.user, role='Admin').exists()
    if not has_workspace_admin and not has_project_admin:
        raise PermissionDenied("Only admins can access project settings.")
        
    if request.method == 'POST':
        repo_action = request.POST.get('repo_action', 'none')
        existing_repo = request.POST.get('existing_repo')
        new_repo_name = request.POST.get('new_repo_name')
        
        repo_name = None
        if repo_action == 'existing' and existing_repo:
            repo_name = existing_repo
        elif repo_action == 'new' and new_repo_name:
            token = request.user.github_token
            if token:
                headers = {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                data = {'name': new_repo_name, 'private': True, 'auto_init': True}
                import requests
                response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
                if response.status_code == 201:
                    repo_name = response.json()['full_name']
                else:
                    messages.error(request, f"Failed to create GitHub repository.")
            else:
                messages.error(request, "Please Re-authenticate with GitHub to create repositories.")
        
        if repo_name:
            from core.models import ProjectRepository
            ProjectRepository.objects.filter(project=project).delete() # clear existing
            ProjectRepository.objects.create(project=project, repository=repo_name)
            
            # Clone the repository locally
            success, msg = _clone_repository(request.user, project, repo_name)
            if not success:
                messages.warning(request, f"Linked repository but clone failed: {msg}")
            else:
                messages.success(request, f"Successfully linked and cloned repository '{repo_name}' to project.")
            
    return redirect('project_settings', project_id=project.id)

@login_required
def remove_workspace_member(request, workspace_id, user_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if not workspace.members.filter(user=request.user, role='Admin').exists():
        raise PermissionDenied("Only workspace admins can remove members.")
    
    if request.method == 'POST':
        member = WorkspaceUser.objects.filter(workspace=workspace, user_id=user_id).first()
        if member and member.user != request.user:
            member.delete()
            messages.success(request, "Member removed.")
        elif member and member.user == request.user:
            messages.error(request, "You cannot remove yourself.")
    return redirect('workspace_settings', workspace_id=workspace.id)

@login_required
def remove_project_member(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    has_workspace_admin = project.workspace.members.filter(user=request.user, role='Admin').exists()
    has_project_admin = hasattr(project, 'members') and project.members.filter(user=request.user, role='Admin').exists()
    if not has_workspace_admin and not has_project_admin:
        raise PermissionDenied("Only admins can remove members.")
    
    if request.method == 'POST':
        member = ProjectUser.objects.filter(project=project, user_id=user_id).first()
        if member:
            member.delete()
            messages.success(request, "Member removed.")
    return redirect('project_settings', project_id=project.id)

@login_required
def rename_workspace(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if not workspace.members.filter(user=request.user, role='Admin').exists():
        raise PermissionDenied("Only workspace admins can rename the workspace.")
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            workspace.name = new_name
            workspace.save()
            messages.success(request, f'Workspace renamed to "{new_name}".')
        else:
            messages.error(request, "Name cannot be empty.")
    return redirect('workspace_settings', workspace_id=workspace.id)

@login_required
def delete_workspace(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if not workspace.members.filter(user=request.user, role='Admin').exists():
        raise PermissionDenied("Only workspace admins can delete the workspace.")
    if request.method == 'POST':
        name = workspace.name
        workspace.delete()
        messages.success(request, f'Workspace "{name}" deleted.')
        return redirect('home')
    return redirect('workspace_settings', workspace_id=workspace.id)

@login_required
def rename_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    has_workspace_admin = project.workspace.members.filter(user=request.user, role='Admin').exists()
    has_project_admin = hasattr(project, 'members') and project.members.filter(user=request.user, role='Admin').exists()
    if not has_workspace_admin and not has_project_admin:
        raise PermissionDenied("Only admins can rename the project.")
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            project.name = new_name
            project.save()
            messages.success(request, f'Project renamed to "{new_name}".')
        else:
            messages.error(request, "Name cannot be empty.")
    return redirect('project_settings', project_id=project.id)

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    has_workspace_admin = project.workspace.members.filter(user=request.user, role='Admin').exists()
    has_project_admin = hasattr(project, 'members') and project.members.filter(user=request.user, role='Admin').exists()
    if not has_workspace_admin and not has_project_admin:
        raise PermissionDenied("Only admins can delete the project.")
    if request.method == 'POST':
        ws_id = project.workspace.id
        name = project.name
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('workspace_view', workspace_id=ws_id)
    return redirect('project_settings', project_id=project.id)
