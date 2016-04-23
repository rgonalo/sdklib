import unittest

from sdklib.mail import GmailPOPlSdk, GmailIMAPlSdk


class TestGmailPOPSdk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = GmailPOPlSdk('sdklib.test', 'sdklib12345678')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_read_all_mails(self):
        messages = self.api.read_all_mails()
        print messages
        for m in messages:
            print dir(m)


class TestGmailIMAPSdk(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = GmailIMAPlSdk('sdklib.test', 'sdklib12345678')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_read_all_mails(self):
        messages = self.api.read_all_mails()
        for m in messages:
            print m