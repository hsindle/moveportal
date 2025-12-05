# checklists/templatetags/user_groups.py
from django import template

register = template.Library()

@register.filter
def has_group(user, group_names):
    """
    Usage: {% if request.user|has_group:"Manager,Supervisor" %}
    """
    group_list = [name.strip() for name in group_names.split(",")]
    return user.groups.filter(name__in=group_list).exists()
