from core.models import Workspace, ProjectUser

def sidebar_workspaces(request):
    """Build sidebar workspace tree respecting cross-role access.
    
    Rules:
    - Show workspaces where user is a workspace member (all projects visible).
    - Show workspaces where user has project-level membership (only those projects visible).
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user
    sidebar_items = []
    seen_workspace_ids = set()

    # 1. Workspaces where user is a direct member → show all projects
    for ws_user in user.workspaces.select_related('workspace').all():
        ws = ws_user.workspace
        seen_workspace_ids.add(ws.id)
        sidebar_items.append({
            'workspace': ws,
            'projects': list(ws.projects.all()),
            'role': ws_user.role,
        })

    # 2. Workspaces where user has project-level access but NO workspace membership
    project_memberships = ProjectUser.objects.filter(user=user).select_related(
        'project', 'project__workspace'
    ).exclude(project__workspace_id__in=seen_workspace_ids)

    # Group by workspace
    ws_project_map = {}
    for pm in project_memberships:
        ws = pm.project.workspace
        if ws.id not in ws_project_map:
            ws_project_map[ws.id] = {'workspace': ws, 'projects': [], 'role': None}
        ws_project_map[ws.id]['projects'].append(pm.project)

    sidebar_items.extend(ws_project_map.values())

    return {'sidebar_workspaces': sidebar_items}
