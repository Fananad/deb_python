from django.core.paginator import Paginator


def post_paginator(posts, MAX_POSTS, request):
    paginator = Paginator(posts, MAX_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
