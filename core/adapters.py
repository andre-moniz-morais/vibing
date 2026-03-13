from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import AuthorizedAccount

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider == 'github':
            username = sociallogin.account.extra_data.get('login')
            if not username:
                raise PermissionDenied("Could not retrieve GitHub username.")
                
            if not AuthorizedAccount.objects.filter(github_nickname=username).exists():
                messages.error(request, f"GitHub account '{username}' is not a whitelisted user.")
                raise PermissionDenied(f"GitHub account '{username}' is not authorized.")
                
        elif sociallogin.account.provider == 'google':
            if not request.user.is_authenticated:
                raise PermissionDenied("You must be logged in via GitHub to connect a Google account.")

        # Update tokens on every login if available
        if sociallogin.token and sociallogin.user.pk:
            if sociallogin.account.provider == 'github':
                sociallogin.user.github_token = sociallogin.token.token
            elif sociallogin.account.provider == 'google':
                sociallogin.user.google_token = sociallogin.token.token
            sociallogin.user.save()

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        # Save tokens directly to the user model on signup
        if sociallogin.token:
            if sociallogin.account.provider == 'github':
                user.github_token = sociallogin.token.token
            elif sociallogin.account.provider == 'google':
                user.google_token = sociallogin.token.token
            user.save()
            
        return user
