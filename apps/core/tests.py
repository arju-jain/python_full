from django.test import TestCase
from django.urls import reverse
from .models import NewsletterSubscriber

class CoreViewsTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aura Luxe')

    def test_newsletter_subscription(self):
        response = self.client.post(reverse('core:newsletter_subscribe'), {'email': 'luxurybuyer@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='luxurybuyer@example.com').exists())
