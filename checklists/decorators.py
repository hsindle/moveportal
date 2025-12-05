from django.contrib.auth.decorators import user_passes_test

def role_required(*role_names):
    """Require the user to be in at least one of the given roles (groups)."""
    def check(user):
        return user.is_authenticated and user.groups.filter(name__in=role_names).exists()
    return user_passes_test(check)
