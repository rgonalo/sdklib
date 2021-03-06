import unittest

from tests.sample_sdk_https import SampleHttpsHttpSdk


class TestSampleSdk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # SampleHttpsHttpSdk.set_default_proxy("localhost:8080")
        cls.api = SampleHttpsHttpSdk()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_get_products(self):
        response = self.api.get_products()
        self.assertEqual(response.status, 200)
        self.assertTrue(isinstance(response.data, list))
