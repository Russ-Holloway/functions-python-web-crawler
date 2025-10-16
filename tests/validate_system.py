"""
Validation Scripts for Durable Functions Web Crawler
Phase 4 - Testing and Validation

Scripts to validate configuration, deployment, and system health
"""

import json
import os
import sys
from typing import Dict, List, Tuple

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def validate_configuration() -> Tuple[bool, List[str]]:
    """
    Validate websites.json configuration file
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    print_section("Configuration Validation")
    
    issues = []
    
    # Check if websites.json exists
    config_path = os.path.join(os.path.dirname(__file__), "..", "websites.json")
    
    if not os.path.exists(config_path):
        issues.append("websites.json file not found")
        print_error("websites.json file not found")
        return False, issues
    
    print_success("websites.json file exists")
    
    # Load and validate JSON structure
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print_success("websites.json is valid JSON")
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {str(e)}")
        print_error(f"Invalid JSON: {str(e)}")
        return False, issues
    
    # Validate required fields
    if "version" not in config:
        issues.append("Missing 'version' field")
        print_error("Missing 'version' field")
    else:
        print_success(f"Version: {config['version']}")
    
    if "websites" not in config:
        issues.append("Missing 'websites' field")
        print_error("Missing 'websites' field")
        return False, issues
    
    if not isinstance(config["websites"], list):
        issues.append("'websites' must be an array")
        print_error("'websites' must be an array")
        return False, issues
    
    print_success(f"Found {len(config['websites'])} website configurations")
    
    # Validate each website configuration
    required_fields = ["id", "name", "url", "enabled"]
    enabled_count = 0
    
    for idx, site in enumerate(config["websites"]):
        site_issues = []
        
        for field in required_fields:
            if field not in site:
                site_issues.append(f"Missing required field '{field}'")
        
        # Validate URL format
        if "url" in site and not site["url"].startswith(("http://", "https://")):
            site_issues.append(f"Invalid URL format: {site['url']}")
        
        # Validate enabled is boolean
        if "enabled" in site and not isinstance(site["enabled"], bool):
            site_issues.append(f"'enabled' must be boolean, got {type(site['enabled']).__name__}")
        
        if site_issues:
            site_name = site.get("name", f"Site #{idx + 1}")
            for issue in site_issues:
                issues.append(f"{site_name}: {issue}")
                print_error(f"{site_name}: {issue}")
        else:
            site_name = site.get("name", f"Site #{idx + 1}")
            if site.get("enabled", False):
                enabled_count += 1
                print_success(f"{site_name}: ✓ Valid (enabled)")
            else:
                print_warning(f"{site_name}: ✓ Valid (disabled)")
    
    print(f"\n{BLUE}Summary: {enabled_count} enabled, {len(config['websites']) - enabled_count} disabled{RESET}")
    
    return len(issues) == 0, issues


def validate_requirements() -> Tuple[bool, List[str]]:
    """
    Validate requirements.txt has all necessary dependencies
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    print_section("Requirements Validation")
    
    issues = []
    
    # Check if requirements.txt exists
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    
    if not os.path.exists(req_path):
        issues.append("requirements.txt file not found")
        print_error("requirements.txt file not found")
        return False, issues
    
    print_success("requirements.txt file exists")
    
    # Read requirements
    with open(req_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print_success(f"Found {len(requirements)} package requirements")
    
    # Check for essential packages
    essential_packages = {
        "azure-functions": "Core Azure Functions package",
        "azure-functions-durable": "Durable Functions orchestration",
        "azure-storage-blob": "Blob Storage integration",
        "beautifulsoup4": "HTML parsing"
    }
    
    for package, description in essential_packages.items():
        found = any(package in req.lower() for req in requirements)
        if found:
            print_success(f"{package}: {description}")
        else:
            issues.append(f"Missing essential package: {package}")
            print_error(f"Missing: {package} - {description}")
    
    return len(issues) == 0, issues


def validate_host_configuration() -> Tuple[bool, List[str]]:
    """
    Validate host.json configuration
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    print_section("Host Configuration Validation")
    
    issues = []
    
    # Check if host.json exists
    host_path = os.path.join(os.path.dirname(__file__), "..", "host.json")
    
    if not os.path.exists(host_path):
        issues.append("host.json file not found")
        print_error("host.json file not found")
        return False, issues
    
    print_success("host.json file exists")
    
    # Load and validate JSON
    try:
        with open(host_path, 'r') as f:
            host_config = json.load(f)
        print_success("host.json is valid JSON")
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {str(e)}")
        print_error(f"Invalid JSON: {str(e)}")
        return False, issues
    
    # Check for Durable Functions configuration
    if "extensions" not in host_config:
        issues.append("Missing 'extensions' section")
        print_error("Missing 'extensions' section")
    elif "durableTask" not in host_config["extensions"]:
        issues.append("Missing 'durableTask' configuration")
        print_error("Missing 'durableTask' configuration in extensions")
    else:
        print_success("Durable Functions configuration present")
        
        durable_config = host_config["extensions"]["durableTask"]
        if "hubName" in durable_config:
            print_success(f"Hub Name: {durable_config['hubName']}")
        
        if "maxConcurrentActivityFunctions" in durable_config:
            print_success(f"Max Concurrent Activity Functions: {durable_config['maxConcurrentActivityFunctions']}")
        
        if "maxConcurrentOrchestratorFunctions" in durable_config:
            print_success(f"Max Concurrent Orchestrator Functions: {durable_config['maxConcurrentOrchestratorFunctions']}")
    
    # Check extension bundle
    if "extensionBundle" not in host_config:
        issues.append("Missing 'extensionBundle' configuration")
        print_error("Missing 'extensionBundle' configuration")
    else:
        bundle = host_config["extensionBundle"]
        print_success(f"Extension Bundle: {bundle.get('id', 'unknown')} version {bundle.get('version', 'unknown')}")
    
    return len(issues) == 0, issues


def validate_function_app_structure() -> Tuple[bool, List[str]]:
    """
    Validate function_app.py structure and key functions
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    print_section("Function App Structure Validation")
    
    issues = []
    
    # Check if function_app.py exists
    app_path = os.path.join(os.path.dirname(__file__), "..", "function_app.py")
    
    if not os.path.exists(app_path):
        issues.append("function_app.py file not found")
        print_error("function_app.py file not found")
        return False, issues
    
    print_success("function_app.py file exists")
    
    # Read function app code
    with open(app_path, 'r') as f:
        code = f.read()
    
    # Check for essential imports
    essential_imports = {
        "azure.functions": "Azure Functions SDK",
        "azure.durable_functions": "Durable Functions SDK",
        "azure.storage.blob": "Blob Storage SDK"
    }
    
    for import_name, description in essential_imports.items():
        if import_name in code:
            print_success(f"Import: {import_name} ({description})")
        else:
            issues.append(f"Missing import: {import_name}")
            print_warning(f"Missing import: {import_name} - {description}")
    
    # Check for orchestrator
    if "def web_crawler_orchestrator(" in code:
        print_success("Orchestrator function: web_crawler_orchestrator")
    else:
        issues.append("Missing orchestrator function")
        print_error("Missing orchestrator function: web_crawler_orchestrator")
    
    # Check for activity functions
    activity_functions = [
        "get_configuration_activity",
        "get_document_hashes_activity",
        "crawl_single_website_activity",
        "store_document_hashes_activity",
        "store_crawl_history_activity"
    ]
    
    for func in activity_functions:
        if f"def {func}(" in code:
            print_success(f"Activity function: {func}")
        else:
            issues.append(f"Missing activity function: {func}")
            print_error(f"Missing activity function: {func}")
    
    # Check for HTTP triggers
    http_triggers = [
        "start_web_crawler_orchestration",
        "get_orchestration_status",
        "terminate_orchestration"
    ]
    
    for trigger in http_triggers:
        if f"def {trigger}(" in code:
            print_success(f"HTTP trigger: {trigger}")
        else:
            issues.append(f"Missing HTTP trigger: {trigger}")
            print_warning(f"Missing HTTP trigger: {trigger}")
    
    # Check for timer trigger
    if "scheduled_crawler_orchestrated" in code:
        print_success("Timer trigger: scheduled_crawler_orchestrated")
    else:
        print_warning("Missing timer trigger: scheduled_crawler_orchestrated")
    
    return len(issues) == 0, issues


def validate_environment_variables() -> Tuple[bool, List[str]]:
    """
    Validate required environment variables
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    print_section("Environment Variables Validation")
    
    issues = []
    
    # Check local.settings.json
    settings_path = os.path.join(os.path.dirname(__file__), "..", "local.settings.json")
    
    if not os.path.exists(settings_path):
        print_warning("local.settings.json not found (OK for production)")
        return True, []
    
    print_success("local.settings.json file exists")
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        print_success("local.settings.json is valid JSON")
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {str(e)}")
        print_error(f"Invalid JSON: {str(e)}")
        return False, issues
    
    # Check for required settings
    if "Values" not in settings:
        issues.append("Missing 'Values' section")
        print_error("Missing 'Values' section")
        return False, issues
    
    values = settings["Values"]
    
    # Check essential settings
    required_settings = {
        "AzureWebJobsStorage": "Required for Durable Functions state storage",
        "WEBSITES_CONFIG_LOCATION": "Location of websites.json configuration"
    }
    
    for setting, description in required_settings.items():
        if setting in values:
            print_success(f"{setting}: {description}")
        else:
            issues.append(f"Missing setting: {setting}")
            print_warning(f"Missing: {setting} - {description}")
    
    return len(issues) == 0, issues


def run_all_validations():
    """Run all validation checks and print summary"""
    print(f"\n{BLUE}{'*' * 60}{RESET}")
    print(f"{BLUE}DURABLE FUNCTIONS WEB CRAWLER - VALIDATION SUITE{RESET}")
    print(f"{BLUE}{'*' * 60}{RESET}")
    
    all_results = []
    
    # Run each validation
    validations = [
        ("Configuration", validate_configuration),
        ("Requirements", validate_requirements),
        ("Host Configuration", validate_host_configuration),
        ("Function App Structure", validate_function_app_structure),
        ("Environment Variables", validate_environment_variables)
    ]
    
    for name, validation_func in validations:
        is_valid, issues = validation_func()
        all_results.append((name, is_valid, issues))
    
    # Print final summary
    print_section("Validation Summary")
    
    total_issues = 0
    for name, is_valid, issues in all_results:
        if is_valid:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED ({len(issues)} issues)")
            total_issues += len(issues)
    
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if total_issues == 0:
        print(f"{GREEN}✓ All validations passed! System ready for deployment.{RESET}")
        return 0
    else:
        print(f"{RED}✗ Found {total_issues} issue(s). Please fix before deployment.{RESET}")
        return 1


if __name__ == "__main__":
    exit_code = run_all_validations()
    sys.exit(exit_code)
