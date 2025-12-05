from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    """
    Redirect users to password change page if must_change_password is True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Define URLs
            password_change_url = reverse("accounts:password_change")
            password_change_done_url = reverse("accounts:password_change_done")
            login_url = reverse("accounts:login")

            # Skip redirect if already on password change pages or login/logout
            if request.path not in [password_change_url, password_change_done_url, login_url]:
                if getattr(request.user, "must_change_password", False):
                    return redirect(password_change_url)

        response = self.get_response(request)
        return response
