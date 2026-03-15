import os
import subprocess
from celery import shared_task
from core.models import Story, User

@shared_task
def run_gemini_cli_develop(story_id, user_id):
    """
    Task to execute when a Story transitions to 'Develop'
    Runs Gemini CLI implementation tasks and git commit.
    """
    user = User.objects.get(id=user_id)
    story = Story.objects.get(id=story_id)
    
    # Environment config for subprocess
    env = os.environ.copy()
    if user.google_token:
        env["GEMINI_API_TOKEN"] = user.google_token
    if user.github_token:
        env["GITHUB_TOKEN"] = user.github_token

    project_dir = f"/tmp/vibing_projects/{story.project.id}/"
    os.makedirs(project_dir, exist_ok=True)
    
    try:
        # Pseudo-code for interacting with git and gemini CLI
        subprocess.run(["git", "clone", getattr(story.repository, 'repository', "https://github.com/example/repo.git"), "."], cwd=project_dir, env=env, check=False)
        
        print(f"Executing Gemini CLI (Develop) for Story {story_id}")
        prompt = f"Implement the following story: {story.content.get('title', 'feature')}"
        subprocess.run(["gemini", "cli", "generate", "--prompt", prompt], cwd=project_dir, env=env, check=False)
        
        subprocess.run(["git", "add", "."], cwd=project_dir, env=env, check=False)
        subprocess.run(["git", "commit", "-m", f"Implemented {story.user_story_id}"], cwd=project_dir, env=env, check=False)
        subprocess.run(["git", "push"], cwd=project_dir, env=env, check=False)
        
        story.state = 'In review'
        story.save()
    except Exception as e:
        print(f"Error executing Gemini CLI: {e}")

@shared_task
def run_gemini_cli_review(story_id, user_id):
    """
    Task to execute when a Story transitions to 'In review'
    Runs Gemini CLI for auditing, finding bugs, and fixing them.
    """
    user = User.objects.get(id=user_id)
    story = Story.objects.get(id=story_id)
    
    env = os.environ.copy()
    if user.google_token:
        env["GEMINI_API_TOKEN"] = user.google_token
        
    project_dir = f"/tmp/vibing_projects/{story.project.id}/"
    os.makedirs(project_dir, exist_ok=True)
    
    try:
        print(f"Executing Gemini CLI (Review) for Story {story_id}")
        subprocess.run(["gemini", "cli", "review", "--fix-bugs"], cwd=project_dir, env=env, check=False)
        subprocess.run(["git", "commit", "-am", f"Fixes for {story.user_story_id}"], cwd=project_dir, env=env, check=False)
        subprocess.run(["git", "push"], cwd=project_dir, env=env, check=False)
    except Exception as e:
        print(f"Error executing Gemini Review: {e}")
