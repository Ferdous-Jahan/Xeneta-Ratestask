from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ratestask.models import Regions, Ports, Prices
from datetime import datetime, timedelta

class AveragePriceListTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.region1 = Regions.objects.create(name='Region 1', slug='region-1', parent_slug=None)
        self.region2 = Regions.objects.create(name='Region 2', slug='region-2', parent_slug=None)
        self.port1 = Ports.objects.create(name='Port 1', code='port1', parent_slug=self.region1)
        self.port2 = Ports.objects.create(name='Port 2', code='port2', parent_slug=self.region2)
        self.prices = [
            Prices.objects.create(day=datetime(2022, 1, 1), orig_code=self.port1, dest_code=self.port2, price=10),
            Prices.objects.create(day=datetime(2022, 1, 1), orig_code=self.port1, dest_code=self.port2, price=20),
            Prices.objects.create(day=datetime(2022, 1, 1), orig_code=self.port1, dest_code=self.port2, price=10),
            Prices.objects.create(day=datetime(2022, 1, 1), orig_code=self.port1, dest_code=self.port2, price=20),
            Prices.objects.create(day=datetime(2022, 1, 2), orig_code=self.port1, dest_code=self.port2, price=15),
            Prices.objects.create(day=datetime(2022, 1, 2), orig_code=self.port1, dest_code=self.port2, price=25),
            Prices.objects.create(day=datetime(2022, 1, 2), orig_code=self.port1, dest_code=self.port2, price=15),
            Prices.objects.create(day=datetime(2022, 1, 2), orig_code=self.port1, dest_code=self.port2, price=25),
            Prices.objects.create(day=datetime(2022, 1, 3), orig_code=self.port1, dest_code=self.port2, price=20),
            Prices.objects.create(day=datetime(2022, 1, 3), orig_code=self.port1, dest_code=self.port2, price=30),
        ]

    def test_average_price_list_successful(self):
        """
        Test case for successful request
        """
        url = reverse('average_price_list')
        data = {
            'date_from': '2022-01-01',
            'date_to': '2022-01-03',
            'origin': 'port1',
            'destination': 'port2'
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = [
            {'day': '2022-01-01', 'average_price': 15.0},
            {'day': '2022-01-02', 'average_price': 20.0},
            {'day': '2022-01-03', 'average_price': None},
        ]
        self.assertEqual(response.data, expected_result)

    def test_average_price_list_missing_params(self):
        """
        Test case for request with missing params
        """
        url = reverse('average_price_list')
        data = {}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_result = {'message': 'One or more parameters are missing'}
        self.assertEqual(response.data, expected_result)

    def test_average_price_list_invalid_port_or_region(self):
        """
        Test case for request with port or region that does not exist in DB
        """
        url = reverse('average_price_list')
        data = {
            'date_from': '2022-01-01',
            'date_to': '2022-01-03',
            'origin': 'invalid-origin',
            'destination': 'invalid-destination'
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        expected_result = {'error': 'destination or origin port does not exist'}
        self.assertEqual(response.data, expected_result)
