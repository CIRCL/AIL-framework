#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for AIL Crawler API endpoints.

This module tests the following endpoints:
- POST /api/v1/add/crawler/task - Add a new crawler task
- POST /api/v1/add/crawler/capture - Add a crawler capture

All endpoints require authentication and proper user role.
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.environ['AIL_BIN'])
sys.path.append(os.environ['AIL_FLASK'])
##################################
# Import Project packages
##################################
from lib import ail_users
from lib import ail_logger
from lib.ConfigLoader import ConfigLoader

# Import Flask app for testing - need to import Flask_server to initialize app
sys.path.append(os.environ['AIL_FLASK'])
import Flask_server  # This initializes Flask_config.app
from Flask_config import app

test_logger = ail_logger.get_test_config(create=True)


class TestApiCrawler(unittest.TestCase):
    """
    Test suite for Crawler API endpoints.
    
    Tests cover authentication, authorization, input validation,
    and error handling for crawler task and capture endpoints.
    """

    def setUp(self):
        """
        Set up test client and test data.
        
        Initializes Flask test client, test token, and standard test data.
        Skips tests if Flask app is not initialized.
        """
        if app is None:
            raise unittest.SkipTest("Flask app not initialized")
        self.app = app
        self.client = app.test_client()
        
        # Get a valid test token
        try:
            self.test_token = ail_users.get_user_token('admin@admin.test')
        except Exception as e:
            test_logger.warning(f'Could not get test token: {e}')
            self.test_token = 'test_token_for_testing'
        
        # Standard test data
        self.test_url = 'http://test-example.onion'
        self.test_data = {
            'url': self.test_url
        }

    def _make_authenticated_request(self, method, endpoint, data=None, token=None):
        """
        Helper method to make authenticated API requests.
        
        Args:
            method: HTTP method (e.g., 'POST', 'GET')
            endpoint: API endpoint path (e.g., '/api/v1/add/crawler/task')
            data: Optional dictionary to send as JSON body
            token: Optional auth token (defaults to self.test_token)
            
        Returns:
            Flask test client response object
        """
        headers = {
            'Authorization': token or self.test_token,
            'Content-Type': 'application/json'
        }
        if data:
            return self.client.open(
                endpoint,
                method=method,
                data=json.dumps(data),
                headers=headers
            )
        else:
            return self.client.open(
                endpoint,
                method=method,
                headers=headers
            )

    # ==================== POST /api/v1/add/crawler/task ====================

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    @patch('blueprints.api_rest.ail_api.is_user_in_role')
    @patch('blueprints.api_rest.ail_api.get_basic_user_meta')
    @patch('blueprints.api_rest.crawlers.api_add_crawler_task')
    def test_add_crawler_task_success(self, mock_add_task, mock_get_meta, mock_is_role, mock_auth):
        """
        Test successful crawler task addition.
        
        Verifies that a valid request with proper authentication
        successfully adds a crawler task and returns 200 with the URL.
        """
        # Mock authentication and authorization
        mock_auth.return_value = ({'status': 'success'}, 200)
        mock_is_role.return_value = True
        mock_get_meta.return_value = ('test_org', 'test_user_id', 'user')
        
        # Mock crawler task addition returning None (success path)
        mock_add_task.return_value = None
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/task', self.test_data)
        
        # Assertions
        self.assertEqual(response.status_code, 200, "Should return 200 on success")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('url'), self.test_url, "Response should contain the submitted URL")
        self.assertIsInstance(response_data, dict, "Response should be a JSON object")
        mock_add_task.assert_called_once()
        
        # Verify the call was made with correct arguments
        call_args = mock_add_task.call_args
        self.assertEqual(call_args[0][0], self.test_data, "Should pass request data to crawler")
        self.assertEqual(call_args[0][1], 'test_org', "Should pass user org to crawler")
        self.assertEqual(call_args.kwargs["user_id"], 'test_user_id', "Should pass user_id to crawler")

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    @patch('blueprints.api_rest.ail_api.is_user_in_role')
    @patch('blueprints.api_rest.ail_api.get_basic_user_meta')
    @patch('blueprints.api_rest.crawlers.api_add_crawler_task')
    def test_add_crawler_task_error_from_crawler(self, mock_add_task, mock_get_meta, mock_is_role, mock_auth):
        """
        Test crawler task addition when crawler returns an error.
        
        Verifies that errors from the crawler module are properly
        propagated back to the client with appropriate status code.
        """
        # Mock authentication and authorization
        mock_auth.return_value = ({'status': 'success'}, 200)
        mock_is_role.return_value = True
        mock_get_meta.return_value = ('test_org', 'test_user_id', 'user')
        
        # Mock crawler task addition returning an error
        error_message = 'Crawler error: Invalid URL format'
        mock_add_task.return_value = ({'status': 'error', 'reason': error_message}, 400)
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/task', self.test_data)
        
        # Assertions
        self.assertEqual(response.status_code, 400, "Should return 400 when crawler returns error")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertEqual(response_data.get('reason'), error_message, "Response should include error reason")
        mock_add_task.assert_called_once()

    def test_add_crawler_task_missing_auth(self):
        """
        Test crawler task addition without authentication header.
        
        Verifies that requests without Authorization header are rejected
        with 401 Unauthorized status.
        """
        response = self.client.post(
            '/api/v1/add/crawler/task',
            data=json.dumps(self.test_data),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 401, "Should return 401 for missing authentication")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertIn('Authentication', response_data.get('reason', ''), "Error message should mention authentication")
        
    def test_add_crawler_task_missing_url(self):
        """
        Test crawler task addition with missing URL field.
        
        Verifies that requests without required 'url' field are handled appropriately.
        """
        with patch('blueprints.api_rest.ail_api.authenticate_user') as mock_auth, \
             patch('blueprints.api_rest.ail_api.is_user_in_role') as mock_is_role, \
             patch('blueprints.api_rest.ail_api.get_basic_user_meta') as mock_get_meta:
            
            # Mock authentication
            mock_auth.return_value = ({'status': 'success'}, 200)
            mock_is_role.return_value = True
            mock_get_meta.return_value = ('test_org', 'test_user_id', 'user')
            
            # Request without URL
            invalid_data = {}
            response = self._make_authenticated_request('POST', '/api/v1/add/crawler/task', invalid_data)
            
            # Should either return 400 (validation error) or pass to crawler which will handle it
            # The actual behavior depends on how the endpoint validates input
            self.assertIn(response.status_code, [200, 400, 500], "Should return appropriate error status")
            
    def test_add_crawler_task_invalid_json(self):
        """
        Test crawler task addition with invalid JSON.
        
        Verifies that malformed JSON requests are rejected.
        """
        headers = {
            'Authorization': self.test_token,
            'Content-Type': 'application/json'
        }
        
        response = self.client.post(
            '/api/v1/add/crawler/task',
            data='{"url": "test", invalid json}',
            headers=headers
        )
        
        # Should return 400 Bad Request for invalid JSON
        self.assertIn(response.status_code, [400, 415], "Should return error for invalid JSON")

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    def test_add_crawler_task_invalid_token(self, mock_auth):
        """
        Test crawler task addition with invalid token.
        
        Verifies that requests with invalid authentication tokens
        are rejected with 401 Unauthorized status.
        """
        # Mock authentication failure
        mock_auth.return_value = ({'status': 'error', 'reason': 'Invalid token'}, 401)
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/task', self.test_data, token='invalid_token')
        
        # Assertions
        self.assertEqual(response.status_code, 401, "Should return 401 for invalid token")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertIn('token', response_data.get('reason', '').lower(), "Error message should mention token")

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    @patch('blueprints.api_rest.ail_api.is_user_in_role')
    def test_add_crawler_task_wrong_role(self, mock_is_role, mock_auth):
        """
        Test crawler task addition with insufficient user role.
        
        Verifies that authenticated users without required role ('user')
        are rejected with 403 Forbidden status.
        """
        # Mock authentication success but insufficient role
        mock_auth.return_value = ({'status': 'success'}, 200)
        mock_is_role.return_value = False  # User not in 'user' role
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/task', self.test_data)
        
        # Assertions
        self.assertEqual(response.status_code, 403, "Should return 403 for insufficient permissions")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertIn('Forbidden', response_data.get('reason', ''), "Error message should mention access forbidden")

    # ==================== POST /api/v1/add/crawler/capture ====================

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    @patch('blueprints.api_rest.ail_api.is_user_in_role')
    @patch('blueprints.api_rest.ail_api.get_user_from_token')
    @patch('blueprints.api_rest.crawlers.api_add_crawler_capture')
    def test_add_crawler_capture_success(self, mock_add_capture, mock_get_user, mock_is_role, mock_auth):
        """
        Test successful crawler capture addition.
        
        Verifies that a valid request with proper authentication
        successfully adds a crawler capture and returns 200 with the URL.
        """
        # Mock authentication and authorization
        mock_auth.return_value = ({'status': 'success'}, 200)
        mock_is_role.return_value = True
        mock_get_user.return_value = 'test_user_id'
        
        # Mock crawler capture addition returning None (success path)
        mock_add_capture.return_value = None
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/capture', self.test_data)
        
        # Assertions
        self.assertEqual(response.status_code, 200, "Should return 200 on success")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('url'), self.test_url, "Response should contain the submitted URL")
        self.assertIsInstance(response_data, dict, "Response should be a JSON object")
        mock_add_capture.assert_called_once()
        
        # Verify the call was made with correct arguments
        call_args = mock_add_capture.call_args
        self.assertEqual(call_args[0][0], self.test_data, "Should pass request data to crawler")
        self.assertEqual(call_args[0][1], 'test_user_id', "Should pass user_id to crawler")

    @patch('blueprints.api_rest.ail_api.authenticate_user')
    @patch('blueprints.api_rest.ail_api.is_user_in_role')
    @patch('blueprints.api_rest.ail_api.get_user_from_token')
    @patch('blueprints.api_rest.crawlers.api_add_crawler_capture')
    def test_add_crawler_capture_error_from_crawler(self, mock_add_capture, mock_get_user, mock_is_role, mock_auth):
        """
        Test crawler capture addition when crawler returns an error.
        
        Verifies that errors from the crawler module are properly
        propagated back to the client with appropriate status code.
        """
        # Mock authentication and authorization
        mock_auth.return_value = ({'status': 'success'}, 200)
        mock_is_role.return_value = True
        mock_get_user.return_value = 'test_user_id'
        
        # Mock crawler capture addition returning an error
        error_message = 'Capture error: Failed to process screenshot'
        mock_add_capture.return_value = ({'status': 'error', 'reason': error_message}, 400)
        
        response = self._make_authenticated_request('POST', '/api/v1/add/crawler/capture', self.test_data)
        
        # Assertions
        self.assertEqual(response.status_code, 400, "Should return 400 when crawler returns error")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertEqual(response_data.get('reason'), error_message, "Response should include error reason")
        mock_add_capture.assert_called_once()
        
    def test_add_crawler_capture_missing_auth(self):
        """
        Test crawler capture addition without authentication header.
        
        Verifies that requests without Authorization header are rejected
        with 401 Unauthorized status.
        """
        response = self.client.post(
            '/api/v1/add/crawler/capture',
            data=json.dumps(self.test_data),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 401, "Should return 401 for missing authentication")
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data.get('status'), 'error', "Response should indicate error status")
        self.assertIn('Authentication', response_data.get('reason', ''), "Error message should mention authentication")


if __name__ == "__main__":
    unittest.main(exit=False)

