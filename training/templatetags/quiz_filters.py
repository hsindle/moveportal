# training/templatetags/quiz_filters.py
from django import template

register = template.Library()

@register.filter
def get_available_options(question_object):
    """
    Returns a list of non-empty option text strings from a Question object
    for rendering radio buttons in the quiz template.
    """
    options = []
    
    if question_object.option_a:
        options.append(question_object.option_a)
    if question_object.option_b:
        options.append(question_object.option_b)
    if question_object.option_c:
        options.append(question_object.option_c)
    if question_object.option_d:
        options.append(question_object.option_d)
        
    return options