import azure.functions as func
import logging
import requests
import traceback
import validators
import os
import json
import hashlib
import asyncio
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configuration from environment variables
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "stbtpdocmon17600004")
COSMOS_DB_ENDPOINT = os.environ.get("COSMOS_DB_ENDPOINT")
COSMOS_DB_NAME = os.environ.get("COSMOS_DB_NAME", "DocumentMonitor")
COSMOS_CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER_NAME", "DocumentMetadata")
MANAGED_IDENTITY_CLIENT_ID = os.environ.get("MANAGED_IDENTITY_CLIENT_ID")

# Initialize Azure clients
credential = DefaultAzureCredential(managed_identity_client_id=MANAGED_IDENTITY_CLIENT_ID)
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=credential
)

# Initialize Cosmos DB client
cosmos_client = None
database = None
metadata_container = None
config_container = None

if COSMOS_DB_ENDPOINT:
    cosmos_client = CosmosClient(COSMOS_DB_ENDPOINT, credential=credential)
    database = cosmos_client.get_database_client(COSMOS_DB_NAME)
    metadata_container = database.get_container_client(COSMOS_CONTAINER_NAME)
    config_container = database.get_container_client("WebsiteConfigs")

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started.')
    
    try:
        # Get website configurations from Cosmos DB or environment
        websites_to_crawl = get_websites_config()
        
        for website_config in websites_to_crawl:
            url = website_config.get('url')
            if url and validators.url(url):
                logging.info(f'Processing website: {url}')
                process_website(url, website_config)
            else:
                logging.warning(f'Invalid URL in configuration: {url}')
                
    except Exception as e:
        logging.error(f'Error in scheduled crawler: {str(e)}')
        logging.error(traceback.format_exc())

@app.route(route="search_site", methods=["POST"])
def search_site(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Checks for a URL JSON property in the HTTP Request body.
    url = req.params.get('url')
    if not url:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            url = req_body.get('url')

    # Check URL validity.
    if url and validators.url(url):
        try:
            # Search the website for documents
            documents = search_website_for_documents(url)
            
            # Return the results as JSON
            return func.HttpResponse(
                json.dumps({"documents": documents, "count": len(documents)}),
                status_code=200,
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=500,
                mimetype="application/json"
            )
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a valid URL in the query string or request body.",
            status_code=400
        )

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered.')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url') if req_body else None
        
        if not url:
            return func.HttpResponse(
                json.dumps({"error": "URL is required"}),
                status_code=400,
                mimetype="application/json"
            )
            
        if not validators.url(url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL"}),
                status_code=400,
                mimetype="application/json"
            )
            
        # Use default configuration for manual crawl
        website_config = {
            "url": url,
            "container_name": "documents",
            "file_patterns": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"],
            "max_depth": 3
        }
        
        process_website(url, website_config)
        
        return func.HttpResponse(
            json.dumps({"message": f"Successfully processed website: {url}"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in manual crawl: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

def get_websites_config() -> List[Dict[str, Any]]:
    """Get website configurations for crawling"""
    try:
        # Default websites configuration if Cosmos DB is not available
        default_websites = [
            {
                "url": "https://example.com",
                "container_name": "documents",
                "file_patterns": [".pdf", ".doc", ".docx", ".txt"],
                "max_depth": 3
            }
        ]
        
        if not cosmos_client:
            logging.warning("Cosmos DB not configured, using default website config")
            return default_websites
            
        # Try to get configurations from Cosmos DB
        try:
            query = "SELECT * FROM c"
            items = list(config_container.query_items(query=query, enable_cross_partition_query=True))
            if items:
                logging.info(f"Found {len(items)} website configurations in Cosmos DB")
                return items
            else:
                logging.info("No website configurations found in Cosmos DB, using defaults")
                return default_websites
        except Exception as e:
            logging.warning(f"Error querying Cosmos DB for website configs: {str(e)}, using defaults")
            return default_websites
            
    except Exception as e:
        logging.error(f"Error getting website configurations: {str(e)}")
        return []

def process_website(url: str, website_config: Dict[str, Any]) -> None:
    """Process a single website for document crawling"""
    try:
        logging.info(f"Starting to process website: {url}")
        
        # Get the website ID for tracking
        website_id = hashlib.md5(url.encode()).hexdigest()
        
        # Search for documents on the website
        documents = search_website_for_documents(url, website_config)
        
        if not documents:
            logging.info(f"No documents found on {url}")
            return
            
        logging.info(f"Found {len(documents)} documents on {url}")
        
        # Process each document
        for doc in documents:
            try:
                # Check if document has changed
                existing_metadata = get_document_metadata(doc['url'], website_id)
                
                if should_download_document(doc, existing_metadata):
                    # Download and store the document
                    success = download_and_store_document(doc, website_config.get('container_name', 'documents'))
                    
                    if success:
                        # Update metadata
                        save_document_metadata(doc, website_id)
                        logging.info(f"Successfully processed document: {doc['url']}")
                    else:
                        logging.error(f"Failed to download document: {doc['url']}")
                else:
                    logging.info(f"Document unchanged, skipping: {doc['url']}")
                    
            except Exception as e:
                logging.error(f"Error processing document {doc.get('url', 'unknown')}: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error processing website {url}: {str(e)}")

def should_download_document(doc: Dict[str, Any], existing_metadata: Dict[str, Any]) -> bool:
    """Determine if a document should be downloaded based on changes"""
    if not existing_metadata:
        # New document, download it
        return True
        
    # Compare file size if available
    if 'size' in doc and 'size' in existing_metadata:
        if doc['size'] != existing_metadata['size']:
            return True
            
    # Compare last modified date if available
    if 'last_modified' in doc and 'last_modified' in existing_metadata:
        if doc['last_modified'] != existing_metadata['last_modified']:
            return True
            
    # Compare hash if available
    if 'hash' in doc and 'hash' in existing_metadata:
        if doc['hash'] != existing_metadata['hash']:
            return True
            
    return False

def search_website_for_documents(base_url: str, config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Search a website for downloadable documents"""
    try:
        if config is None:
            config = {
                "file_patterns": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"],
                "max_depth": 3
            }
            
        documents = []
        visited_urls = set()
        urls_to_visit = [(base_url, 0)]  # (url, depth)
        
        file_patterns = config.get('file_patterns', ['.pdf', '.doc', '.docx'])
        max_depth = config.get('max_depth', 2)
        
        while urls_to_visit:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in visited_urls or depth > max_depth:
                continue
                
            visited_urls.add(current_url)
            
            try:
                response = requests.get(current_url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Check if this URL itself is a document
                if any(pattern in current_url.lower() for pattern in file_patterns):
                    doc_info = {
                        'url': current_url,
                        'title': current_url.split('/')[-1],
                        'size': len(response.content),
                        'content_type': response.headers.get('content-type', ''),
                        'last_modified': response.headers.get('last-modified', ''),
                        'found_at': datetime.now(timezone.utc).isoformat()
                    }
                    documents.append(doc_info)
                    continue
                
                # Parse HTML content for links to documents
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    # Check if it's a document link
                    if any(pattern in href.lower() for pattern in file_patterns):
                        doc_info = {
                            'url': full_url,
                            'title': link.get_text(strip=True) or href.split('/')[-1],
                            'found_at': datetime.now(timezone.utc).isoformat(),
                            'source_page': current_url
                        }
                        
                        # Get additional metadata if possible
                        try:
                            head_response = requests.head(full_url, timeout=10)
                            doc_info['size'] = head_response.headers.get('content-length')
                            doc_info['content_type'] = head_response.headers.get('content-type', '')
                            doc_info['last_modified'] = head_response.headers.get('last-modified', '')
                        except:
                            pass  # Continue without metadata if HEAD request fails
                            
                        documents.append(doc_info)
                    
                    # Add internal links to visit (if within same domain and not too deep)
                    elif urlparse(full_url).netloc == urlparse(base_url).netloc and depth < max_depth:
                        if full_url not in visited_urls:
                            urls_to_visit.append((full_url, depth + 1))
                            
            except Exception as e:
                logging.warning(f"Error processing URL {current_url}: {str(e)}")
                continue
                
        logging.info(f"Found {len(documents)} documents on {base_url}")
        return documents
        
    except Exception as e:
        logging.error(f"Error searching website {base_url}: {str(e)}")
        return []

def download_and_store_document(doc_info: Dict[str, Any], container_name: str = "documents") -> bool:
    """Download a document and store it in Azure Blob Storage"""
    try:
        url = doc_info['url']
        logging.info(f"Downloading document: {url}")
        
        # Download the document
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Generate blob name
        parsed_url = urlparse(url)
        file_name = parsed_url.path.split('/')[-1]
        if not file_name:
            file_name = f"document_{hashlib.md5(url.encode()).hexdigest()}"
        
        blob_name = f"{parsed_url.netloc}/{file_name}"
        
        # Store in blob storage
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Upload with metadata
        metadata = {
            'source_url': url,
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
            'original_title': doc_info.get('title', ''),
            'content_type': doc_info.get('content_type', '')
        }
        
        blob_client.upload_blob(
            response.content,
            overwrite=True,
            metadata=metadata
        )
        
        logging.info(f"Successfully stored document: {blob_name}")
        return True
        
    except Exception as e:
        logging.error(f"Error downloading/storing document {doc_info.get('url', 'unknown')}: {str(e)}")
        return False

def save_document_metadata(doc_info: Dict[str, Any], website_id: str) -> bool:
    """Save document metadata to storage"""
    try:
        if not cosmos_client:
            logging.error("Cosmos DB not configured")
            return False
            
        # Create unique ID for the document
        doc_id = hashlib.md5(doc_info['url'].encode()).hexdigest()
        doc_info['id'] = doc_id
        doc_info['website_id'] = website_id
        doc_info['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        metadata_container.upsert_item(doc_info)
        logging.info(f"Successfully saved document metadata: {doc_info['url']}")
        return True
    except Exception as e:
        logging.error(f"Error saving document metadata: {str(e)}")
        return False

def get_document_metadata(doc_url: str, website_id: str) -> Dict[str, Any]:
    """Get metadata for a specific document"""
    try:
        if not cosmos_client:
            logging.warning("Cosmos DB not configured")
            return None
            
        doc_id = hashlib.md5(doc_url.encode()).hexdigest()
        
        try:
            item = metadata_container.read_item(item=doc_id, partition_key=website_id)
            return item
        except Exception:
            # Document not found
            return None
            
    except Exception as e:
        logging.error(f"Error getting document metadata: {str(e)}")
        return None