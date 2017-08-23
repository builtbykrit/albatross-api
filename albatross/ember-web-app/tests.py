from django.test import Client, TestCase

class WebAppTestCase(TestCase):
    def test_webapp(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>AlbatrossWebApp</title>', response.content)

    def test_webapp_404(self):
        client = Client()
        response = client.get('/', {'revision': 'non-existent'})
        self.assertEqual(response.status_code, 404)