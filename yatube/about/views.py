from django.views.generic.base import TemplateView

# Create your views here.


class AboutAuthorView(TemplateView):
    # В переменной template_name обязательно указывается имя шаблона,
    # на основе которого будет создана возвращаемая страница
    template_name = 'About/author.html'


class AboutTechView(TemplateView):
    template_name = 'About/tech.html'
