from django.test import TestCase


class ViewTestClass(TestCase):
    """
    Проверка использования корректного шаблона
    при неизвестной странице
    """
    def test_error_page_404(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, 404)
