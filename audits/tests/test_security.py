from django.test import SimpleTestCase

from audits.services.security import URLSecurityError, validate_url


class ValidateUrlTests(SimpleTestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(URLSecurityError):
            validate_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(URLSecurityError):
            validate_url("http://localhost:8000/")

    def test_rejects_loopback_ip(self):
        with self.assertRaises(URLSecurityError):
            validate_url("http://127.0.0.1/")

    def test_rejects_link_local_metadata_ip(self):
        with self.assertRaises(URLSecurityError):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_private_range(self):
        with self.assertRaises(URLSecurityError):
            validate_url("http://10.0.0.5/")

    def test_rejects_missing_hostname(self):
        with self.assertRaises(URLSecurityError):
            validate_url("https:///path")
