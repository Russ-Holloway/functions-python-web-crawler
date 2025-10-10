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

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Configuration from environment variables
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "stbtpdocmon17600004")
COSMOS_DB_ENDPOINT = os.environ.get("COSMOS_DB_ENDPOINT")
COSMOS_DB_NAME = os.environ.get("COSMOS_DB_NAME", "DocumentMonitor")
COSMOS_CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER_NAME", "DocumentMetadata")
MANAGED_IDENTITY_CLIENT_ID = os.environ.get("MANAGED_IDENTITY_CLIENT_ID", "stbtpdocmon17600004")

# Initialize Azure clients
credential = DefaultAzureCredential(managed_identity_client_id=MANAGED_IDENTITY_CLIENT_ID)
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=credential
)

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

    if url:
        if validators.url(url):
            response = orchestrator_function(url)
            return func.HttpResponse(f"{response}",
                                 status_code=200)
        else:
            return func.HttpResponse(
                "The URL was invalid.",
                status_code=400
            )
    else:
        return func.HttpResponse(
            "No URL was passed. Please input a URL.",
            status_code=400
        )


@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def document_monitor_timer(myTimer: func.TimerRequest) -> None:
    """Timer function that runs every 4 hours to check for document updates"""
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Document monitor timer trigger function executed.')
    
    try:
        # Get list of websites to monitor from configuration
        websites_to_monitor = get_websites_config()
        
        for website_config in websites_to_monitor:
            asyncio.run(monitor_website_documents(website_config))
            
        logging.info('Document monitoring completed successfully.')
    except Exception as e:
        logging.error(f"Error in document monitor timer: {str(e)}")
        logging.error(traceback.format_exc())


@app.route(route="add_website", methods=["POST"])
def add_website_to_monitor(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP function to add a new website to the monitoring list"""
    logging.info('Add website function processed a request.')

    try:
        req_body = req.get_json()
        
        # Validate required fields
        required_fields = ['url', 'name', 'file_patterns']
        for field in required_fields:
            if field not in req_body:
                return func.HttpResponse(
                    f"Missing required field: {field}",
                    status_code=400
                )

        # Store website configuration
        website_config = {
            'id': hashlib.md5(req_body['url'].encode()).hexdigest(),
            'url': req_body['url'],
            'name': req_body['name'],
            'file_patterns': req_body['file_patterns'],  # List of file extensions or patterns
            'last_checked': None,
            'active': True,
            'created_date': datetime.now(timezone.utc).isoformat()
        }
        
        # Save to Cosmos DB
        save_website_config(website_config)
        
        return func.HttpResponse(
            json.dumps({"message": "Website added successfully", "id": website_config['id']}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error adding website: {str(e)}")
        return func.HttpResponse(
            f"Error adding website: {str(e)}",
            status_code=500
        )


@app.route(route="manual_scan", methods=["POST"])
def manual_document_scan(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP function to manually trigger document scanning for a specific website"""
    logging.info('Manual scan function processed a request.')

    try:
        req_body = req.get_json()
        
        if 'website_id' not in req_body:
            return func.HttpResponse(
                "Missing website_id parameter",
                status_code=400
            )

        website_config = get_website_config(req_body['website_id'])
        if not website_config:
            return func.HttpResponse(
                "Website configuration not found",
                status_code=404
            )
        
        # Run the scan
        result = asyncio.run(monitor_website_documents(website_config))
        
        return func.HttpResponse(
            json.dumps({"message": "Scan completed", "result": result}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in manual scan: {str(e)}")
        return func.HttpResponse(
            f"Error in manual scan: {str(e)}",
            status_code=500
        )


@app.route(route="list_websites", methods=["GET"])
def list_monitored_websites(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP function to list all monitored websites"""
    try:
        websites = get_all_website_configs()
        return func.HttpResponse(
            json.dumps(websites, default=str),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error listing websites: {str(e)}")
        return func.HttpResponse(
            f"Error listing websites: {str(e)}",
            status_code=500
        )


# Function to orchestrate all of the function calls and store the needed data. 
def orchestrator_function(url):
    try:
        data = crawl_site(url)

        site_data = []
        site_data.append(get_page_title(data))
        site_data.append(get_all_urls(data))
        site_data.append(get_meta_tag(data))

        return site_data
    except Exception as error:
        logging.error(f"Error while making a request to the site: {error.__cause__}")
        logging.error(traceback.format_exc())


# Submits the HTTP request to the user-inputted URL.
def crawl_site(url):
    response = requests.get(url, allow_redirects=False)
    return BeautifulSoup(response.text, "lxml")


# Extracts the page title.
def get_page_title(data):
    try:
        return data.title.string
    except Exception as error:
        logging.error(f"Error retrieving the site title: {error.__cause__}")
        logging.error(traceback.format_exc())


# Gets all of the URLs from the webpage.
def get_all_urls(data):
    try:
        urls = []

        url_elements = data.select("a[href]")
        for url_element in url_elements:
            url = url_element['href']
            if "https://" in url or "http://" in url:
                urls.append(url)

        return urls
    
    except Exception as error:
        logging.error(f"Error retrieving the URLs in the site: {error.__cause__}")
        logging.error(traceback.format_exc())


# Extracts a specific meta tag from the URL.
def get_meta_tag(data):
    try:
        meta_tag = data.find("meta", attrs={'name': 'description'})
        return meta_tag["content"]
    except Exception as error:
        logging.error(f"Error retrieving the URLs in the site: {error.__cause__}")
        logging.error(traceback.format_exc())


# ===== DOCUMENT MONITORING FUNCTIONS =====

async def monitor_website_documents(website_config: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor a website for document changes and update storage accordingly"""
    logging.info(f"Monitoring website: {website_config['name']} - {website_config['url']}")
    
    try:
        # Get current documents from the website
        current_documents = await discover_documents_on_website(website_config)
        
        # Get previously stored document metadata
        stored_documents = get_stored_document_metadata(website_config['id'])
        
        # Compare and identify changes
        changes = compare_document_lists(current_documents, stored_documents)
        
        results = {
            'website_id': website_config['id'],
            'website_name': website_config['name'],
            'scan_time': datetime.now(timezone.utc).isoformat(),
            'documents_found': len(current_documents),
            'new_documents': 0,
            'updated_documents': 0,
            'removed_documents': 0,
            'errors': []
        }
        
        # Process new and updated documents
        for doc_url in changes['new'] + changes['updated']:
            try:
                doc_info = next(doc for doc in current_documents if doc['url'] == doc_url)
                await download_and_store_document(doc_info, website_config['id'])
                
                if doc_url in changes['new']:
                    results['new_documents'] += 1
                else:
                    results['updated_documents'] += 1
                    
            except Exception as e:
                error_msg = f"Error processing document {doc_url}: {str(e)}"
                logging.error(error_msg)
                results['errors'].append(error_msg)
        
        # Process removed documents
        for doc_url in changes['removed']:
            try:
                remove_document_from_storage(doc_url, website_config['id'])
                results['removed_documents'] += 1
            except Exception as e:
                error_msg = f"Error removing document {doc_url}: {str(e)}"
                logging.error(error_msg)
                results['errors'].append(error_msg)
        
        # Update website last checked time
        website_config['last_checked'] = datetime.now(timezone.utc).isoformat()
        save_website_config(website_config)
        
        # Update document metadata in Cosmos DB
        for doc in current_documents:
            save_document_metadata(doc, website_config['id'])
        
        logging.info(f"Monitoring completed for {website_config['name']}: {results}")
        return results
        
    except Exception as e:
        logging.error(f"Error monitoring website {website_config['name']}: {str(e)}")
        raise


async def discover_documents_on_website(website_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover all documents on a website that match the configured patterns"""
    base_url = website_config['url']
    file_patterns = website_config['file_patterns']
    
    documents = []
    
    try:
        # Get the main page
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Check if the link matches any of the file patterns
            if any(pattern.lower() in absolute_url.lower() for pattern in file_patterns):
                try:
                    # Get document metadata
                    doc_info = await get_document_info(absolute_url)
                    if doc_info:
                        doc_info['source_website'] = website_config['id']
                        doc_info['discovered_date'] = datetime.now(timezone.utc).isoformat()
                        documents.append(doc_info)
                        
                except Exception as e:
                    logging.warning(f"Could not get info for document {absolute_url}: {str(e)}")
                    continue
        
        logging.info(f"Discovered {len(documents)} documents on {website_config['name']}")
        return documents
        
    except Exception as e:
        logging.error(f"Error discovering documents on {base_url}: {str(e)}")
        return []


async def get_document_info(url: str) -> Dict[str, Any]:
    """Get metadata information about a document without downloading it"""
    try:
        # Make a HEAD request to get metadata
        response = requests.head(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Extract relevant information
        doc_info = {
            'url': url,
            'filename': os.path.basename(urlparse(url).path) or 'unknown',
            'content_type': response.headers.get('content-type', ''),
            'content_length': int(response.headers.get('content-length', 0)),
            'last_modified': response.headers.get('last-modified', ''),
            'etag': response.headers.get('etag', ''),
            'last_checked': datetime.now(timezone.utc).isoformat()
        }
        
        # Generate a content hash for comparison (if possible)
        doc_info['content_hash'] = f"{doc_info['content_length']}_{doc_info['last_modified']}_{doc_info['etag']}"
        
        return doc_info
        
    except Exception as e:
        logging.error(f"Error getting document info for {url}: {str(e)}")
        return None


async def download_and_store_document(doc_info: Dict[str, Any], website_id: str) -> bool:
    """Download a document and store it in Azure Blob Storage"""
    try:
        # Download the document
        response = requests.get(doc_info['url'], timeout=60)
        response.raise_for_status()
        
        # Generate blob name
        blob_name = f"{website_id}/{doc_info['filename']}"
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container="documents", 
            blob=blob_name
        )
        
        # Upload to blob storage
        blob_client.upload_blob(
            data=response.content,
            overwrite=True,
            metadata={
                'source_url': doc_info['url'],
                'website_id': website_id,
                'content_type': doc_info['content_type'],
                'download_date': datetime.now(timezone.utc).isoformat(),
                'original_filename': doc_info['filename']
            }
        )
        
        logging.info(f"Successfully uploaded {doc_info['filename']} to blob storage")
        return True
        
    except Exception as e:
        logging.error(f"Error downloading and storing document {doc_info['url']}: {str(e)}")
        return False


def compare_document_lists(current_docs: List[Dict], stored_docs: List[Dict]) -> Dict[str, List[str]]:
    """Compare current documents with stored documents to identify changes"""
    
    current_urls = {doc['url']: doc for doc in current_docs}
    stored_urls = {doc['url']: doc for doc in stored_docs}
    
    new_docs = []
    updated_docs = []
    removed_docs = []
    
    # Find new and updated documents
    for url, current_doc in current_urls.items():
        if url not in stored_urls:
            new_docs.append(url)
        else:
            stored_doc = stored_urls[url]
            # Compare content hashes to detect changes
            if current_doc.get('content_hash') != stored_doc.get('content_hash'):
                updated_docs.append(url)
    
    # Find removed documents
    for url in stored_urls:
        if url not in current_urls:
            removed_docs.append(url)
    
    return {
        'new': new_docs,
        'updated': updated_docs,
        'removed': removed_docs
    }


def remove_document_from_storage(doc_url: str, website_id: str) -> bool:
    """Remove a document from blob storage and metadata"""
    try:
        # Get document metadata to find blob name
        doc_metadata = get_document_metadata(doc_url, website_id)
        
        if doc_metadata:
            blob_name = f"{website_id}/{doc_metadata['filename']}"
            
            # Delete from blob storage
            blob_client = blob_service_client.get_blob_client(
                container="documents", 
                blob=blob_name
            )
            blob_client.delete_blob(delete_snapshots="include")
            
            # Remove metadata
            delete_document_metadata(doc_url, website_id)
            
            logging.info(f"Successfully removed document {doc_url} from storage")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error removing document {doc_url}: {str(e)}")
        return False


# ===== CONFIGURATION AND METADATA FUNCTIONS =====

def get_websites_config() -> List[Dict[str, Any]]:
    """Get all website configurations from storage"""
    try:
        # For now, return a default configuration
        # In production, this should read from Cosmos DB or configuration storage
        return [
            {
                'id': 'default_website',
                'url': 'https://example.com',
                'name': 'Example Website',
                'file_patterns': ['.pdf', '.docx', '.xlsx', '.pptx'],
                'active': True
            }
        ]
    except Exception as e:
        logging.error(f"Error getting website configurations: {str(e)}")
        return []


def save_website_config(website_config: Dict[str, Any]) -> bool:
    """Save website configuration to storage"""
    try:
        # For now, just log the configuration
        # In production, this should save to Cosmos DB
        logging.info(f"Saving website config: {website_config}")
        return True
    except Exception as e:
        logging.error(f"Error saving website config: {str(e)}")
        return False


def get_website_config(website_id: str) -> Dict[str, Any]:
    """Get a specific website configuration"""
    try:
        # For now, return a default configuration
        # In production, this should read from Cosmos DB
        return {
            'id': website_id,
            'url': 'https://example.com',
            'name': 'Example Website',
            'file_patterns': ['.pdf', '.docx', '.xlsx', '.pptx'],
            'active': True
        }
    except Exception as e:
        logging.error(f"Error getting website config {website_id}: {str(e)}")
        return None


def get_all_website_configs() -> List[Dict[str, Any]]:
    """Get all website configurations"""
    return get_websites_config()


def get_stored_document_metadata(website_id: str) -> List[Dict[str, Any]]:
    """Get metadata for all documents stored for a website"""
    try:
        # For now, return empty list
        # In production, this should query Cosmos DB
        logging.info(f"Getting stored document metadata for website {website_id}")
        return []
    except Exception as e:
        logging.error(f"Error getting stored document metadata: {str(e)}")
        return []


def save_document_metadata(doc_info: Dict[str, Any], website_id: str) -> bool:
    """Save document metadata to storage"""
    try:
        # For now, just log the metadata
        # In production, this should save to Cosmos DB
        logging.info(f"Saving document metadata: {doc_info}")
        return True
    except Exception as e:
        logging.error(f"Error saving document metadata: {str(e)}")
        return False


def get_document_metadata(doc_url: str, website_id: str) -> Dict[str, Any]:
    """Get metadata for a specific document"""
    try:
        # For now, return None
        # In production, this should query Cosmos DB
        logging.info(f"Getting document metadata for {doc_url}")
        return None
    except Exception as e:
        logging.error(f"Error getting document metadata: {str(e)}")
        return None


def delete_document_metadata(doc_url: str, website_id: str) -> bool:
    """Delete document metadata from storage"""
    try:
        # For now, just log the deletion
        # In production, this should delete from Cosmos DB
        logging.info(f"Deleting document metadata for {doc_url}")
        return True
    except Exception as e:
        logging.error(f"Error deleting document metadata: {str(e)}")
        return False