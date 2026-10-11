import unittest
from unittest.mock import patch, MagicMock
import requests

class TestUsernameTracker(unittest.TestCase):
    def test_import_module(self):
        # Must be able to import the module and functions
        import username_tracker
        self.assertTrue(hasattr(username_tracker, 'check_site'))
        self.assertTrue(hasattr(username_tracker, 'search_username'))
        self.assertTrue(hasattr(username_tracker, 'DEFAULT_SITES'))

    @patch('requests.get')
    def test_check_site_found(self, mock_get):
        import username_tracker
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        site = {"url": "https://example.com/{}", "name": "Example"}
        res = username_tracker.check_site(site, "testuser", timeout=2)

        self.assertEqual(res['name'], 'Example')
        self.assertEqual(res['status'], 'FOUND')
        self.assertEqual(res['url'], 'https://example.com/testuser')
        self.assertIn('Found', res['message'])

    @patch('requests.get')
    def test_check_site_not_found(self, mock_get):
        import username_tracker
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        site = {"url": "https://example.com/{}", "name": "Example"}
        res = username_tracker.check_site(site, "testuser", timeout=2)

        self.assertEqual(res['name'], 'Example')
        self.assertEqual(res['status'], 'NOT_FOUND')
        self.assertIn('not found', res['message'].lower())

    @patch('requests.get')
    def test_check_site_timeout(self, mock_get):
        import username_tracker
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        site = {"url": "https://example.com/{}", "name": "Example"}
        # Must not raise an exception
        res = username_tracker.check_site(site, "testuser", timeout=2)

        self.assertEqual(res['name'], 'Example')
        self.assertEqual(res['status'], 'TIMEOUT')
        self.assertIn('timed out', res['message'].lower())

    @patch('requests.get')
    def test_check_site_connection_error(self, mock_get):
        import username_tracker
        mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")

        site = {"url": "https://example.com/{}", "name": "Example"}
        # Must not raise an exception
        res = username_tracker.check_site(site, "testuser", timeout=2)

        self.assertEqual(res['name'], 'Example')
        self.assertEqual(res['status'], 'ERROR')
        self.assertIn('connection error', res['message'].lower())

    @patch('requests.get')
    def test_check_site_blocked_or_rate_limited(self, mock_get):
        import username_tracker
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        site = {"url": "https://example.com/{}", "name": "Example"}
        res = username_tracker.check_site(site, "testuser", timeout=2)

        self.assertEqual(res['name'], 'Example')
        self.assertEqual(res['status'], 'BLOCKED')

    @patch('requests.get')
    def test_search_username_resilience(self, mock_get):
        """Test that when one site fails/times out, other sites still return their result."""
        import username_tracker

        def side_effect(url, **kwargs):
            if 'site1' in url:
                raise requests.exceptions.Timeout("Site 1 unresponsive")
            elif 'site2' in url:
                resp = MagicMock()
                resp.status_code = 200
                return resp
            else:
                resp = MagicMock()
                resp.status_code = 404
                return resp

        mock_get.side_effect = side_effect

        test_sites = [
            {"url": "https://site1.com/{}", "name": "Site1"},
            {"url": "https://site2.com/{}", "name": "Site2"},
            {"url": "https://site3.com/{}", "name": "Site3"}
        ]

        results = username_tracker.search_username("target", sites=test_sites)

        # All 3 sites must have results returned
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['status'], 'TIMEOUT')
        self.assertEqual(results[1]['status'], 'FOUND')
        self.assertEqual(results[2]['status'], 'NOT_FOUND')

if __name__ == '__main__':
    unittest.main()
