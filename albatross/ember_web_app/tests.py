from django.test import Client, TestCase

class EmberWebAppTestCase(TestCase):
    def test_emberwebapp(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Albatross | Smarter Project Estimates</title>', response.content)

    def test_html_tag(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertEqual('<!DOCTYPE html>', content[:15])

    def test_emberwebapp_404(self):
        client = Client()
        response = client.get('/', {'revision': 'non-existent'})
        self.assertEqual(response.status_code, 404)