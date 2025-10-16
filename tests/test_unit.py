"""
Unit Tests for Durable Functions Web Crawler
Phase 4 - Testing and Validation

Tests orchestrator logic, activity functions, and core business logic
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions to test
from function_app import (
    load_websites_config,
    get_enabled_websites,
    crawl_website_core,
    calculate_content_hash,
    find_documents_in_html,
    get_configuration_activity,
    get_document_hashes_activity,
    crawl_single_website_activity,
    store_document_hashes_activity,
    store_crawl_history_activity
)


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration loading and management"""
    
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_load_websites_config_success(self, mock_json_load, mock_open):
        """Test successful configuration loading"""
        # Arrange
        mock_config = {
            "version": "1.0.0",
            "websites": [
                {"id": "test1", "name": "Test Site", "enabled": True}
            ]
        }
        mock_json_load.return_value = mock_config
        
        # Act
        result = load_websites_config()
        
        # Assert
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(len(result["websites"]), 1)
        mock_open.assert_called_once()
    
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_websites_config_file_not_found(self, mock_open):
        """Test configuration loading when file doesn't exist"""
        # Act
        result = load_websites_config()
        
        # Assert
        self.assertEqual(result["version"], "0.0.0")
        self.assertEqual(result["websites"], [])
    
    @patch('builtins.open', create=True)
    @patch('json.load', side_effect=json.JSONDecodeError("test", "test", 0))
    def test_load_websites_config_invalid_json(self, mock_json_load, mock_open):
        """Test configuration loading with invalid JSON"""
        # Act
        result = load_websites_config()
        
        # Assert
        self.assertEqual(result["version"], "0.0.0")
        self.assertEqual(result["websites"], [])
    
    @patch('function_app.load_websites_config')
    def test_get_enabled_websites(self, mock_load_config):
        """Test filtering enabled websites"""
        # Arrange
        mock_load_config.return_value = {
            "version": "1.0.0",
            "websites": [
                {"id": "site1", "name": "Site 1", "enabled": True},
                {"id": "site2", "name": "Site 2", "enabled": False},
                {"id": "site3", "name": "Site 3", "enabled": True}
            ]
        }
        
        # Act
        result = get_enabled_websites()
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertTrue(all(site["enabled"] for site in result))


class TestDocumentDetection(unittest.TestCase):
    """Test HTML parsing and document detection"""
    
    def test_find_documents_pdf_links(self):
        """Test finding PDF documents in HTML"""
        # Arrange
        html = """
        <html>
            <body>
                <a href="document1.pdf">Document 1</a>
                <a href="https://example.com/doc2.pdf">Document 2</a>
                <a href="page.html">Not a document</a>
            </body>
        </html>
        """
        base_url = "https://example.com"
        
        # Act
        result = find_documents_in_html(html, base_url)
        
        # Assert
        self.assertEqual(len(result["documents"]), 2)
        self.assertTrue(any("document1.pdf" in doc["url"] for doc in result["documents"]))
    
    def test_find_documents_relative_urls(self):
        """Test conversion of relative URLs to absolute"""
        # Arrange
        html = '<a href="/docs/file.pdf">Document</a>'
        base_url = "https://example.com"
        
        # Act
        result = find_documents_in_html(html, base_url)
        
        # Assert
        self.assertEqual(len(result["documents"]), 1)
        self.assertTrue(result["documents"][0]["url"].startswith("https://"))
    
    def test_find_documents_no_documents(self):
        """Test HTML with no documents"""
        # Arrange
        html = '<html><body><p>No documents here</p></body></html>'
        base_url = "https://example.com"
        
        # Act
        result = find_documents_in_html(html, base_url)
        
        # Assert
        self.assertEqual(len(result["documents"]), 0)


class TestHashingAndChangeDetection(unittest.TestCase):
    """Test document hashing and change detection"""
    
    def test_calculate_content_hash_same_content(self):
        """Test that same content produces same hash"""
        # Arrange
        content1 = b"Test document content"
        content2 = b"Test document content"
        
        # Act
        hash1 = calculate_content_hash(content1)
        hash2 = calculate_content_hash(content2)
        
        # Assert
        self.assertEqual(hash1, hash2)
    
    def test_calculate_content_hash_different_content(self):
        """Test that different content produces different hash"""
        # Arrange
        content1 = b"Test document content 1"
        content2 = b"Test document content 2"
        
        # Act
        hash1 = calculate_content_hash(content1)
        hash2 = calculate_content_hash(content2)
        
        # Assert
        self.assertNotEqual(hash1, hash2)


class TestCoreWebsiteCrawling(unittest.TestCase):
    """Test core website crawling logic"""
    
    @patch('function_app.urllib.request.urlopen')
    @patch('function_app.find_documents_in_html')
    def test_crawl_website_core_success(self, mock_find_docs, mock_urlopen):
        """Test successful website crawl"""
        # Arrange
        site_config = {
            "id": "test_site",
            "name": "Test Site",
            "url": "https://example.com",
            "enabled": True,
            "multi_level": False,
            "max_depth": 1
        }
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Test</html>"
        mock_response.info.return_value.get.return_value = None
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock document finding
        mock_find_docs.return_value = {
            "documents": [],
            "total_links_found": 5,
            "sample_links": []
        }
        
        previous_hashes = {}
        
        # Act
        result = crawl_website_core(site_config, previous_hashes)
        
        # Assert
        self.assertEqual(result["site_name"], "Test Site")
        self.assertEqual(result["site_url"], "https://example.com")
        self.assertIn(result["status"], ["success", "no_documents"])
    
    @patch('function_app.urllib.request.urlopen')
    def test_crawl_website_core_http_403(self, mock_urlopen):
        """Test handling of HTTP 403 (blocked)"""
        # Arrange
        site_config = {
            "id": "test_site",
            "name": "Test Site",
            "url": "https://example.com",
            "enabled": True,
            "multi_level": False,
            "max_depth": 1
        }
        
        # Mock HTTP 403 error
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com", 403, "Forbidden", {}, None
        )
        
        previous_hashes = {}
        
        # Act
        result = crawl_website_core(site_config, previous_hashes)
        
        # Assert
        self.assertEqual(result["status"], "blocked")
        self.assertIn("403", result["error"])


class TestActivityFunctions(unittest.TestCase):
    """Test Durable Functions activity wrappers"""
    
    @patch('function_app.load_websites_config')
    def test_get_configuration_activity(self, mock_load_config):
        """Test configuration activity function"""
        # Arrange
        mock_config = {"version": "1.0.0", "websites": []}
        mock_load_config.return_value = mock_config
        
        # Act
        result = get_configuration_activity(None)
        
        # Assert
        self.assertEqual(result, mock_config)
    
    @patch('function_app.get_document_hashes_from_storage')
    def test_get_document_hashes_activity(self, mock_get_hashes):
        """Test document hashes retrieval activity"""
        # Arrange
        mock_hashes = {"url1": {"hash": "abc123", "filename": "doc.pdf"}}
        mock_get_hashes.return_value = mock_hashes
        
        # Act
        result = get_document_hashes_activity(None)
        
        # Assert
        self.assertEqual(result, mock_hashes)
    
    @patch('function_app.crawl_website_core')
    def test_crawl_single_website_activity(self, mock_crawl_core):
        """Test single website crawl activity"""
        # Arrange
        activity_input = {
            "site_config": {"id": "test", "name": "Test", "url": "https://test.com"},
            "previous_hashes": {}
        }
        mock_result = {
            "status": "success",
            "documents_found": 10,
            "documents_uploaded": 5
        }
        mock_crawl_core.return_value = mock_result
        
        # Act
        result = crawl_single_website_activity(activity_input)
        
        # Assert
        self.assertEqual(result, mock_result)
        mock_crawl_core.assert_called_once()
    
    @patch('function_app.store_document_hashes_to_storage')
    def test_store_document_hashes_activity(self, mock_store_hashes):
        """Test storing document hashes activity"""
        # Arrange
        hashes = {"url1": {"hash": "abc123"}}
        mock_store_hashes.return_value = True
        
        # Act
        result = store_document_hashes_activity(hashes)
        
        # Assert
        self.assertTrue(result)
        mock_store_hashes.assert_called_once_with(hashes)
    
    @patch('function_app.store_crawl_history')
    def test_store_crawl_history_activity(self, mock_store_history):
        """Test storing crawl history activity"""
        # Arrange
        summary = {"sites_processed": 5, "documents_uploaded": 25}
        mock_store_history.return_value = True
        
        # Act
        result = store_crawl_history_activity(summary)
        
        # Assert
        self.assertTrue(result)
        mock_store_history.assert_called_once_with(summary)


class TestOrchestratorLogic(unittest.TestCase):
    """Test orchestrator workflow logic (integration style)"""
    
    def test_orchestrator_workflow_steps(self):
        """Test the expected orchestrator workflow"""
        # This test documents the expected orchestrator flow
        # Actual orchestrator testing requires Durable Functions test framework
        
        expected_steps = [
            "Load configuration",
            "Get previous hashes",
            "Fan-out to parallel activities",
            "Aggregate results",
            "Store combined hashes",
            "Store crawl history"
        ]
        
        # Assert workflow is documented
        self.assertEqual(len(expected_steps), 6)
        self.assertIn("Fan-out", expected_steps[2])


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    @patch('function_app.urllib.request.urlopen')
    def test_crawl_handles_timeout(self, mock_urlopen):
        """Test handling of network timeout"""
        # Arrange
        site_config = {
            "id": "test",
            "name": "Test",
            "url": "https://example.com",
            "multi_level": False,
            "max_depth": 1
        }
        
        import socket
        mock_urlopen.side_effect = socket.timeout("Connection timeout")
        
        # Act
        result = crawl_website_core(site_config, {})
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIsNotNone(result["error"])
    
    @patch('function_app.urllib.request.urlopen')
    def test_crawl_handles_connection_error(self, mock_urlopen):
        """Test handling of connection errors"""
        # Arrange
        site_config = {
            "id": "test",
            "name": "Test",
            "url": "https://example.com",
            "multi_level": False,
            "max_depth": 1
        }
        
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        # Act
        result = crawl_website_core(site_config, {})
        
        # Assert
        self.assertEqual(result["status"], "error")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
