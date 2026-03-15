from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, AuthorizedAccount, Workspace, WorkspaceUser, 
    Project, ProjectRepository, ProjectEnvironment, 
    Story, StoryUser, AITaskStatus
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('OAuth Tokens', {'fields': ('github_token', 'google_token')}),
    )

admin.site.register(AuthorizedAccount)
admin.site.register(Workspace)
admin.site.register(WorkspaceUser)
admin.site.register(Project)
admin.site.register(ProjectRepository)
admin.site.register(ProjectEnvironment)
admin.site.register(Story)
admin.site.register(StoryUser)
admin.site.register(AITaskStatus)
