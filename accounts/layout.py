# accounts/layout.py
from crispy_forms.layout import Field, Layout
from crispy_forms.bootstrap import StrictButton

class TailwindField(Field):
    """
    Custom field layout that applies Tailwind classes for visibility and structure.
    This overrides the default field rendering to apply specific classes.
    """
    template = 'accounts/custom_field.html'

# Define the standard fields from your form
MANAGER_ADD_USER_LAYOUT = Layout(
    TailwindField('username'),
    TailwindField('email'),
    TailwindField('first_name'),
    TailwindField('last_name'),
    TailwindField('roles'),
    TailwindField('password'), # The form will generate password fields automatically
    TailwindField('password2'), 
)