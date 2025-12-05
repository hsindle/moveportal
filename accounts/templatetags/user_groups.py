from django import template

register = template.Library()

@register.filter
def has_group(user, group_names):
    """
    Usage: {% if request.user|has_group:"Manager,Supervisor" %}
    """
    if not user.is_authenticated:
        return False
    groups = [name.strip() for name in group_names.split(',')]
    return user.groups.filter(name__in=groups).exists()
