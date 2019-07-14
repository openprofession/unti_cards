from django import template

register = template.Library()


@register.filter
def count_comments(appeal, user):
    return appeal.get_count_comments(user)


@register.filter
def count_new_comments(appeal, user):
    return appeal.get_count_new_comments(user)



