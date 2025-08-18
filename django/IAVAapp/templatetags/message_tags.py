from django import template

register = template.Library()

@register.filter
def icon(message_tag):
    print("icon filter executed")
    icons = {
        'success': 'fa-circle-check',
        'error': 'fa-circle-xmark',
        'warning': 'fa-triangle-exclamation',
        'info': 'fa-circle-info',
    }
    return icons.get(message_tag, 'fa-circle-info')