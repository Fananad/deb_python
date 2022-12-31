from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'About/author.html'


class AboutTechView(TemplateView):
    template_name = 'About/tech.html'
