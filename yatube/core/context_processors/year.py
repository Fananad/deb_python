from datetime import date


def year(request):
    a = date.today().year
    return {
        'year': a
    }
