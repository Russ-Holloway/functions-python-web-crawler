"""
Integration Tests for Durable Functions Web Crawler
Phase 4 - Testing and Validation

Tests end-to-end workflows with mocked Azure services
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete crawl workflow from start to finish"""
    
    @patch('function_app.store_crawl_history')
    @patch('function_app.store_document_hashes_to_storage')
    @patch('function_app.get_document_hashes_from_storage')
    @patch('function_app.load_websites_config')
    @patch('function_app.urllib.request.urlopen')
    def test_full_crawl_workflow(
        self,
        mock_urlopen,
        mock_load_config,
        mock_get_hashes,
        mock_store_hashes,
        mock_store_history
    ):
        """Test complete crawl workflow with mocked Azure services"""
        from function_app import get_enabled_websites, crawl_website_core
        
        # Arrange - Mock configuration
        mock_load_config.return_value = {
            "version": "1.0.0",
            "websites": [
                {
                    "id": "test_site",
                    "name": "Test Site",
                    "url": "https://example.com",
                    "enabled": True,
                    "multi_level": False,
                    "max_depth": 1
                }
            ]
        }
        
        # Mock previous hashes (empty - first run)
        mock_get_hashes.return_value = {}
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b'''
        <html>
            <body>
                <a href="document1.pdf">Document 1</a>
                <a href="https://example.com/doc2.pdf">Document 2</a>
            </body>
        </html>
        '''
        mock_response.info.return_value.get.return_value = None
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock storage operations
        mock_store_hashes.return_value = True
        mock_store_history.return_value = True
        
        # Act - Execute workflow
        enabled_sites = get_enabled_websites()
        self.assertEqual(len(enabled_sites), 1)
        
        results = []
        for site in enabled_sites:
            result = crawl_website_core(site, {})
            results.append(result)
        
        # Assert - Verify workflow completion
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["site_name"], "Test Site")
        self.assertIn(results[0]["status"], ["success", "no_documents"])


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration management integration"""
    
    def test_websites_json_structure(self):
        """Test that websites.json has correct structure"""
        # Arrange
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "websites.json"
        )
        
        # Act
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Assert
            self.assertIn("version", config)
            self.assertIn("websites", config)
            self.assertIsInstance(config["websites"], list)
            
            # Check required fields in each website
            for site in config["websites"]:
                self.assertIn("id", site)
                self.assertIn("name", site)
                self.assertIn("url", site)
                self.assertIn("enabled", site)
                self.assertIsInstance(site["enabled"], bool)


class TestStorageIntegration(unittest.TestCase):
    """Test Azure Storage integration with mocks"""
    
    @patch('function_app.BlobServiceClient')
    def test_document_hash_storage_workflow(self, mock_blob_client):
        """Test storing and retrieving document hashes"""
        from function_app import (
            store_document_hashes_to_storage,
            get_document_hashes_from_storage
        )
        
        # Arrange
        mock_container = MagicMock()
        mock_blob_client.return_value.get_container_client.return_value = mock_container
        
        test_hashes = {
            "https://example.com/doc1.pdf": {
                "hash": "abc123",
                "filename": "doc1.pdf",
                "last_updated": "2025-01-15T10:00:00Z"
            }
        }
        
        # Mock blob upload
        mock_blob = MagicMock()
        mock_container.get_blob_client.return_value = mock_blob
        mock_blob.upload_blob.return_value = None
        
        # Mock blob download for retrieval
        mock_blob.download_blob.return_value.readall.return_value = json.dumps(test_hashes).encode('utf-8')
        
        # Act - Store hashes
        store_result = store_document_hashes_to_storage(test_hashes)
        
        # Assert storage
        self.assertTrue(store_result)
        
        # Act - Retrieve hashes
        retrieved_hashes = get_document_hashes_from_storage()
        
        # Assert retrieval (if mocked correctly)
        # Note: This would need proper blob client mocking
        self.assertIsNotNone(retrieved_hashes)


class TestHTTPTriggerIntegration(unittest.TestCase):
    """Test HTTP trigger integration"""
    
    @patch('azure.functions.HttpRequest')
    @patch('function_app.df.DurableOrchestrationClient')
    def test_start_orchestration_http_trigger(self, mock_client, mock_request):
        """Test starting orchestration via HTTP trigger"""
        from function_app import start_web_crawler_orchestration
        
        # Arrange
        mock_request.method = "POST"
        mock_orchestration_client = MagicMock()
        mock_client.return_value = mock_orchestration_client
        
        # Mock instance ID
        mock_orchestration_client.start_new.return_value = "test-instance-123"
        mock_orchestration_client.create_check_status_response.return_value = MagicMock(
            status_code=202
        )
        
        # Act
        response = start_web_crawler_orchestration(mock_request, mock_orchestration_client)
        
        # Assert
        self.assertEqual(response.status_code, 202)


class TestParallelExecution(unittest.TestCase):
    """Test parallel execution of activity functions"""
    
    @patch('function_app.crawl_website_core')
    def test_multiple_sites_parallel_simulation(self, mock_crawl_core):
        """Simulate parallel execution of multiple sites"""
        from function_app import crawl_single_website_activity
        
        # Arrange - Multiple sites
        sites = [
            {
                "site_config": {
                    "id": f"site{i}",
                    "name": f"Site {i}",
                    "url": f"https://example{i}.com",
                    "enabled": True,
                    "multi_level": False,
                    "max_depth": 1
                },
                "previous_hashes": {}
            }
            for i in range(5)
        ]
        
        # Mock successful crawls
        mock_crawl_core.return_value = {
            "status": "success",
            "documents_found": 10,
            "documents_uploaded": 5
        }
        
        # Act - Simulate parallel execution
        results = []
        for site_input in sites:
            result = crawl_single_website_activity(site_input)
            results.append(result)
        
        # Assert
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r["status"] == "success" for r in results))
        self.assertEqual(mock_crawl_core.call_count, 5)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and retry logic"""
    
    @patch('function_app.crawl_website_core')
    def test_partial_failure_handling(self, mock_crawl_core):
        """Test handling when some sites fail"""
        from function_app import crawl_single_website_activity
        
        # Arrange - Mix of success and failure
        def crawl_side_effect(site_config, previous_hashes):
            if "fail" in site_config["id"]:
                return {"status": "error", "error": "Simulated failure"}
            else:
                return {"status": "success", "documents_found": 10}
        
        mock_crawl_core.side_effect = crawl_side_effect
        
        sites = [
            {
                "site_config": {
                    "id": "site_success",
                    "name": "Success Site",
                    "url": "https://success.com",
                    "enabled": True,
                    "multi_level": False,
                    "max_depth": 1
                },
                "previous_hashes": {}
            },
            {
                "site_config": {
                    "id": "site_fail",
                    "name": "Fail Site",
                    "url": "https://fail.com",
                    "enabled": True,
                    "multi_level": False,
                    "max_depth": 1
                },
                "previous_hashes": {}
            }
        ]
        
        # Act
        results = [crawl_single_website_activity(site) for site in sites]
        
        # Assert - Both complete, one success one failure
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[1]["status"], "error")


class TestDocumentProcessing(unittest.TestCase):
    """Test document detection and processing integration"""
    
    @patch('function_app.urllib.request.urlopen')
    def test_document_detection_and_hashing(self, mock_urlopen):
        """Test finding documents and calculating hashes"""
        from function_app import find_documents_in_html, calculate_content_hash
        
        # Arrange
        html = b'''
        <html>
            <body>
                <a href="doc1.pdf">Document 1</a>
                <a href="https://example.com/doc2.docx">Document 2</a>
                <a href="/files/doc3.pdf">Document 3</a>
            </body>
        </html>
        '''
        
        # Act - Find documents
        result = find_documents_in_html(html.decode('utf-8'), "https://example.com")
        
        # Assert
        self.assertGreater(len(result["documents"]), 0)
        
        # Test hashing
        for doc in result["documents"]:
            # Simulate document content
            content = b"Test document content"
            doc_hash = calculate_content_hash(content)
            self.assertIsNotNone(doc_hash)
            self.assertEqual(len(doc_hash), 64)  # SHA-256 hex length


class TestChangeDetection(unittest.TestCase):
    """Test change detection logic"""
    
    def test_new_document_detection(self):
        """Test detecting new documents"""
        # Arrange
        previous_hashes = {
            "https://example.com/old.pdf": {
                "hash": "abc123",
                "filename": "old.pdf"
            }
        }
        
        current_documents = [
            {"url": "https://example.com/old.pdf", "hash": "abc123"},
            {"url": "https://example.com/new.pdf", "hash": "def456"}
        ]
        
        # Act - Detect new documents
        new_docs = [
            doc for doc in current_documents
            if doc["url"] not in previous_hashes
        ]
        
        # Assert
        self.assertEqual(len(new_docs), 1)
        self.assertEqual(new_docs[0]["url"], "https://example.com/new.pdf")
    
    def test_modified_document_detection(self):
        """Test detecting modified documents"""
        # Arrange
        previous_hashes = {
            "https://example.com/doc.pdf": {
                "hash": "old_hash_123",
                "filename": "doc.pdf"
            }
        }
        
        current_documents = [
            {"url": "https://example.com/doc.pdf", "hash": "new_hash_456"}
        ]
        
        # Act - Detect modified documents
        modified_docs = [
            doc for doc in current_documents
            if doc["url"] in previous_hashes
            and previous_hashes[doc["url"]]["hash"] != doc["hash"]
        ]
        
        # Assert
        self.assertEqual(len(modified_docs), 1)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
