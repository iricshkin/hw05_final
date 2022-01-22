from http import HTTPStatus

from django.test import Client, TestCase
from django.urls.base import reverse_lazy


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    # Проверяем доступность страниц
    def test_about_author_and_tech_url_exists_at_desired_location(self):
        """Страницы /author/ и /tech/ доступны любому пользователю."""
        url_names = (
            reverse_lazy("about:author"),
            reverse_lazy("about:author"),
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            "about/author.html": reverse_lazy("about:author"),
            "about/tech.html": reverse_lazy("about:tech"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
