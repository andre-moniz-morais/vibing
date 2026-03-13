from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    github_token = models.CharField(max_length=255, blank=True, null=True)
    google_token = models.CharField(max_length=255, blank=True, null=True)

class AuthorizedAccount(models.Model):
    github_nickname = models.CharField(max_length=150, unique=True)
    
    def __str__(self):
        return self.github_nickname

class Workspace(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class WorkspaceUser(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Editor', 'Editor'),
        ('Reader', 'Reader'),
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspaces')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ('workspace', 'user')

class Project(models.Model):
    name = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    content = models.JSONField(default=dict, blank=True, help_text="JSON from editor.js")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    
    def __str__(self):
        return self.name

class ProjectRepository(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='repositories')
    repository = models.CharField(max_length=255)

class ProjectUser(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Editor', 'Editor'),
        ('Reader', 'Reader'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ('project', 'user')

class ProjectEnvironment(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments')
    server_path = models.CharField(max_length=1024, help_text="Path to local directory for CLI")
    variables = models.JSONField(default=dict, blank=True)

class Story(models.Model):
    STATE_CHOICES = (
        ('TODO', 'TODO'),
        ('Develop', 'Develop'),
        ('In review', 'In review'),
        ('Request changes', 'Request changes'),
        ('Done', 'Done'),
    )
    user_story_id = models.CharField(max_length=50, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stories')
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default='TODO')
    changes_requested = models.TextField(blank=True)
    story_points = models.IntegerField(default=0)
    content = models.JSONField(default=dict, blank=True, help_text="JSON from editor.js")
    repository = models.ForeignKey(ProjectRepository, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_stories')
    order = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.user_story_id:
            # automatic “US” + (number of user stories in the project + 1)
            count = Story.objects.filter(project=self.project).count()
            self.user_story_id = f"US{count + 1}"
        if not self.pk and self.order == 0:
            # New story gets added to the bottom
            max_order = getattr(Story.objects.filter(project=self.project).order_by('-order').first(), 'order', 0)
            self.order = max_order + 10
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_story_id}: {self.content.get('title', 'Story') if isinstance(self.content, dict) else 'Story'}"

class StoryUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_stories')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='assignees')

class AITaskStatus(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Running', 'Running'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='ai_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    logs = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
