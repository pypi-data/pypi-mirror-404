#!/usr/bin/env python3
"""
Enumageddon - Web Fuzzer & Enumeration Tool
Simple yet powerful fuzzer for bug bounty hunters
"""

import sys
import os
import argparse
import requests
import time
from pathlib import Path
from threading import Thread, Lock
from queue import Queue
from datetime import datetime
import json
import re
import dns.resolver
import platform


# ANSI Color codes for cross-platform terminal output
class Colors:
    """ANSI color codes with automatic fallback for unsupported terminals"""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        
    def green(self, text):
        return f"\033[92m{text}\033[0m" if self.enabled else text
    
    def blue(self, text):
        return f"\033[94m{text}\033[0m" if self.enabled else text
    
    def yellow(self, text):
        return f"\033[93m{text}\033[0m" if self.enabled else text
    
    def red(self, text):
        return f"\033[91m{text}\033[0m" if self.enabled else text
    
    def white(self, text):
        return f"\033[97m{text}\033[0m" if self.enabled else text
    
    def bold(self, text):
        return f"\033[1m{text}\033[0m" if self.enabled else text


def should_use_color():
    """Detect if terminal supports ANSI colors (cross-platform)"""
    # Check environment variable to disable colors
    if os.getenv('NO_COLOR'):
        return False
    
    # Force color if requested
    if os.getenv('FORCE_COLOR'):
        return True
    
    # Check if stdout is TTY (interactive terminal)
    if not hasattr(sys.stdout, 'isatty'):
        return True  # Assume colors are fine if we can't detect
    
    # If not a TTY (piped output), disable colors
    if not sys.stdout.isatty():
        return False
    
    # All modern terminals support ANSI colors (Windows 10+, macOS, Linux)
    return True


# Global color instance (initialized later with correct setting)
colors = None

# Built-in wordlist for quick fuzzing without external files
BUILTIN_WORDLIST = [
    # Common directories
    'admin', 'api', 'test', 'config', 'backup', 'index', 'home', 'login', 'logout',
    'dashboard', 'panel', 'user', 'users', 'account', 'accounts', 'auth', 'profile',
    'settings', 'preferences', 'help', 'support', 'contact', 'about', 'faq', 'info',
    'news', 'blog', 'posts', 'articles', 'media', 'assets', 'static', 'resources',
    'download', 'downloads', 'files', 'file', 'documents', 'document', 'reports',
    'report', 'data', 'database', 'db', 'search', 'query', 'results', 'list',
    
    # API endpoints
    'api/v1', 'api/v2', 'api/v3', 'api/v4', 'api/latest', 'api/rest', 'rest',
    'graphql', 'gql', 'rpc', 'endpoints', 'endpoint', 'methods', 'services',
    'service', 'swagger', 'api-docs', 'docs', 'documentation', 'reference',
    
    # Admin/Management
    'admin.php', 'admin.asp', 'admin.html', 'administrator', 'wp-admin', 'manage',
    'management', 'console', 'control', 'backend', 'staff', 'moderator', 'operator',
    'superuser', 'root', 'master', 'privileged',
    
    # Authentication
    'login', 'login.php', 'login.asp', 'login.html', 'signin', 'auth', 'authenticate',
    'authorization', 'logout', 'register', 'signup', 'join', 'verify', 'confirmation',
    'activate', 'reset', 'forgot', 'password', 'recovery', '2fa', 'otp', 'token',
    
    # Payment/Commerce
    'payment', 'payments', 'checkout', 'cart', 'order', 'orders', 'invoice', 'receipt',
    'billing', 'purchase', 'shop', 'store', 'product', 'products', 'category',
    'categories', 'price', 'pricing', 'discount', 'coupon', 'subscription',
    
    # Development/Debug
    'debug', 'debugbar', 'profiler', 'console', 'error', 'exception', 'log', 'logs',
    'status', 'health', 'version', 'info', 'metrics', 'monitoring', 'analytics',
    'trace', 'stack', 'dump', 'test', 'testing', 'dev', 'development', 'staging',
    'production', 'prod', 'qa', 'sandbox', 'demo', 'sample',
    
    # Configuration
    'config', 'configuration', 'settings', 'options', 'env', 'environment', 'vars',
    'constants', 'properties', 'config.php', 'config.xml', 'config.json', '.env',
    'setup', 'install', 'installer', 'wizard', 'migration', 'upgrade',
    
    # Backup/Archive
    'backup', 'backup.sql', 'backup.zip', 'backup.tar', 'archive', 'restore',
    'export', 'import', 'download', 'upload', 'sync', 'clone', 'copy',
    
    # System Files
    'robots.txt', 'sitemap.xml', 'sitemap', '.htaccess', '.htpasswd', 'web.config',
    '.git', '.svn', '.env', '.config', 'composer.json', 'package.json', 'Dockerfile',
    'requirements.txt', 'Gemfile', 'pom.xml',
    
    # Resources
    'css', 'js', 'javascript', 'images', 'img', 'photos', 'pictures', 'media',
    'fonts', 'audio', 'video', 'downloads', 'uploads', 'temp', 'cache', 'public',
    'private', 'protected', 'secure',
    
    # Social/Community
    'user', 'users', 'profile', 'profiles', 'avatar', 'avatars', 'comment',
    'comments', 'like', 'likes', 'follow', 'follower', 'followers', 'friend',
    'friends', 'message', 'messages', 'notification', 'notifications', 'feed',
    
    # Content Management
    'post', 'posts', 'page', 'pages', 'article', 'articles', 'content', 'category',
    'categories', 'tag', 'tags', 'archive', 'author', 'authors', 'taxonomy',
    'hierarchy', 'menu', 'widget', 'plugin', 'plugins', 'theme', 'themes',
    
    # Monitoring/Analytics
    'analytics', 'tracking', 'statistics', 'stats', 'report', 'reports', 'metric',
    'metrics', 'log', 'logs', 'audit', 'event', 'events', 'history', 'activity',
    
    # Additional common endpoints
    'ajax', 'json', 'xml', 'api-endpoint', 'endpoint', 'service', 'services',
    'resource', 'resources', 'method', 'methods', 'function', 'functions',
    'class', 'classes', 'module', 'modules', 'package', 'packages', 'library',
    'handler', 'controller', 'route', 'routes', 'middleware',
]

# AWS Cloud Service Wordlist
AWS_WORDLIST = [
    # S3 Buckets
    's3', 's3-website', 's3-accelerate', 's3-static', 'cdn', 'static', 'media',
    'assets', 'images', 'files', 'downloads', 'uploads', 'backup', 'backups',
    'archive', 'archives', 'logs', 'data', 'public', 'private', 'secure',
    
    # CloudFront
    'cloudfront', 'distribution', 'cdn', 'edge', 'cache',
    
    # API Gateway
    'api', 'api-gateway', 'rest-api', 'graphql', 'websocket', 'v1', 'v2', 'v3',
    
    # Lambda
    'lambda', 'function', 'function-url', 'async', 'invoke',
    
    # RDS
    'rds', 'database', 'db', 'postgres', 'mysql', 'mariadb', 'oracle',
    
    # EC2
    'ec2', 'instance', 'elastic-ip', 'load-balancer', 'alb', 'nlb',
    
    # ElastiCache
    'elasticache', 'redis', 'memcached', 'cache',
    
    # DynamoDB
    'dynamodb', 'table', 'stream', 'backup',
    
    # SNS/SQS
    'sns', 'sqs', 'queue', 'topic', 'subscription',
    
    # Other AWS Services
    'cognito', 'auth', 'iam', 'kms', 'secrets', 'ssm', 'parameter',
    'cloudwatch', 'logs', 'metrics', 'alarms', 'events',
    'sns', 'sqs', 'sms', 'ses', 'email',
    'route53', 'acm', 'certificate', 'health-check',
    'elastictranscoder', 'mediaconvert', 'transcribe',
]

# GCP Cloud Service Wordlist
GCP_WORDLIST = [
    # Cloud Storage
    'storage', 'bucket', 'gs', 'cloud-storage', 'object', 'blob',
    'cdn', 'cdn-backend', 'static', 'media', 'assets', 'files',
    
    # App Engine
    'appengine', 'app-engine', 'app', 'service', 'version', 'instance',
    
    # Cloud Run
    'run', 'cloud-run', 'service', 'container', 'revision',
    
    # Cloud Functions
    'functions', 'function', 'cloudfunctions', 'httpsTrigger', 'pubsubTrigger',
    
    # Firestore/Datastore
    'firestore', 'datastore', 'database', 'document', 'collection',
    
    # Pub/Sub
    'pubsub', 'topic', 'subscription', 'message', 'event',
    
    # BigQuery
    'bigquery', 'query', 'table', 'dataset', 'project',
    
    # Cloud SQL
    'sql', 'cloudsql', 'instance', 'database', 'backup',
    
    # Kubernetes/GKE
    'container', 'gke', 'kubernetes', 'cluster', 'node',
    
    # Other GCP Services
    'identity', 'iam', 'auth', 'oauth', 'api-key', 'service-account',
    'monitoring', 'logging', 'trace', 'profiler', 'debugger',
    'translate', 'vision', 'speech', 'language', 'video-intelligence',
    'maps', 'places', 'geocoding', 'directions',
]

# Azure Cloud Service Wordlist
AZURE_WORDLIST = [
    # Blob Storage
    'blob', 'storage', 'container', 'blobs', 'file-share', 'table',
    'static-website', 'cdn', 'assets', 'media', 'files', 'backup',
    
    # App Service
    'app-service', 'app', 'web', 'api', 'function-app', 'mobile-app',
    'service', 'instance', 'slot', 'environment',
    
    # Azure Functions
    'functions', 'function', 'trigger', 'binding', 'http',
    'timer', 'queue', 'blob', 'cosmosdb', 'eventgrid',
    
    # Cosmos DB
    'cosmos', 'cosmosdb', 'database', 'collection', 'container',
    'document', 'graph', 'table', 'mongodb',
    
    # SQL Database
    'sql', 'database', 'server', 'instance', 'query', 'backup',
    'postgresql', 'mysql', 'mariadb', 'sqlserver',
    
    # Virtual Machines
    'vm', 'virtual-machine', 'instance', 'vmss', 'scaleset',
    'disk', 'snapshot', 'image',
    
    # Container Services
    'container', 'container-registry', 'kubernetes', 'aks', 'container-instances',
    'image', 'registry', 'cluster',
    
    # Service Bus/Event Hubs
    'servicebus', 'queue', 'topic', 'eventhub', 'event', 'message',
    
    # Other Azure Services
    'identity', 'entra', 'ad', 'authentication', 'authorization', 'msi',
    'keyvault', 'vault', 'secret', 'certificate', 'key',
    'monitor', 'monitoring', 'insights', 'logs', 'metrics',
    'cognitive', 'translator', 'speech', 'vision', 'language',
    'search', 'indexer', 'skillset',
]

# User Agent presets
USER_AGENT_PRESETS = {
    'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'opera': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
    'edge': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'bot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'curl': 'curl/8.0.0',
    'mobile': 'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
}

# Keyword mutations (inspired by cloud_enum)
KEYWORD_MUTATIONS = [
    '{keyword}',
    '{keyword}s',
    '{keyword}-dev',
    '{keyword}-prod',
    '{keyword}-test',
    '{keyword}-staging',
    '{keyword}-backup',
    '{keyword}-archive',
    '{keyword}-storage',
    '{keyword}-bucket',
    '{keyword}-data',
    '{keyword}-assets',
    '{keyword}-media',
    '{keyword}-cdn',
    '{keyword}-api',
    '{keyword}-app',
    '{keyword}-web',
    '{keyword}-server',
    '{keyword}-service',
    '{keyword}io',
    '{keyword}-io',
    '{keyword}corp',
    '{keyword}-corp',
    '{keyword}cloud',
    '{keyword}-cloud',
    'www-{keyword}',
    'api-{keyword}',
    'storage-{keyword}',
    'bucket-{keyword}',
    'cdn-{keyword}',
    'dev-{keyword}',
    'prod-{keyword}',
    'test-{keyword}',
]

class Fuzzer:
    """Web fuzzer engine with cloud_enum integration"""
    
    def __init__(self, target_url=None, wordlist=None, threads=20, timeout=None, rate_limit=0, extensions=None, 
                 filter_codes=None, method="GET", headers=None, output=None, aws=False, gcp=False, azure=False, 
                 keyword=None, cloud_enum_mode=False, user_agent=None, follow_redirects=False, use_colors=True, verbosity=0, wildcard_domain=None):
        self.target_url = target_url
        self.wordlist_file = wordlist
        self.use_builtin = wordlist is None
        self.wildcard_domain = wildcard_domain
        self.aws = aws
        self.gcp = gcp
        self.verbosity = verbosity
        self.azure = azure
        self.keyword = keyword
        self.cloud_enum_mode = cloud_enum_mode or keyword is not None
        self.threads_count = threads
        self.timeout = timeout
        self.rate_limit = 1.0 / rate_limit if rate_limit > 0 else 0
        self.extensions = extensions.split(',') if extensions else []
        self.filter_codes = set(map(int, filter_codes.split(','))) if filter_codes else {404}
        self.method = method.upper()
        self.user_agent = user_agent
        self.follow_redirects = follow_redirects
        self.headers = headers or {}
        self.output_file = output
        self.use_colors = use_colors
        
        # Ensure FUZZ or * placeholder exists (unless cloud mode or wildcard mode)
        is_cloud = aws or gcp or azure
        if not is_cloud and not wildcard_domain and 'FUZZ' not in self.target_url and '*' not in self.target_url:
            self.target_url += '/FUZZ'
        
        self.results = []
        self.lock = Lock()
        self.session = requests.Session()
        
        # Set User-Agent (use preset or custom)
        if user_agent:
            # Check if it's a preset name
            ua_lower = user_agent.lower()
            if ua_lower in USER_AGENT_PRESETS:
                user_agent = USER_AGENT_PRESETS[ua_lower]
            # Otherwise use the custom user agent as-is
        else:
            # Default user agent
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        self.session.headers.update({'User-Agent': user_agent})
        if headers:
            for header in headers.split(';'):
                key, value = header.split(':', 1)
                self.session.headers.update({key.strip(): value.strip()})
        
        self.total_checked = 0
        self.valid_found = 0
    
    def load_wordlist(self):
        """Load wordlist from file, cloud service, or use built-in"""
        if self.aws:
            return AWS_WORDLIST
        elif self.gcp:
            return GCP_WORDLIST
        elif self.azure:
            return AZURE_WORDLIST
        elif self.use_builtin:
            return BUILTIN_WORDLIST
        else:
            try:
                with open(self.wordlist_file, 'r') as f:
                    words = [line.strip() for line in f if line.strip()]
                return words
            except FileNotFoundError:
                print(f"[!] Wordlist not found: {self.wordlist_file}")
                sys.exit(1)
            except Exception as e:
                print(f"[!] Error loading wordlist: {e}")
                sys.exit(1)
    
    def generate_keyword_mutations(self, keyword):
        """Generate mutations of a keyword (cloud_enum style)"""
        mutations = []
        for mutation in KEYWORD_MUTATIONS:
            mutations.append(mutation.format(keyword=keyword))
        # Remove duplicates while preserving order
        return list(dict.fromkeys(mutations))
    
    def enumerate_s3_buckets(self, keywords):
        """Enumerate AWS S3 buckets using keywords"""
        buckets_to_test = []
        for keyword in keywords:
            # Common S3 bucket patterns
            buckets_to_test.extend([
                f"https://{keyword}.s3.amazonaws.com",
                f"https://s3.amazonaws.com/{keyword}",
                f"https://{keyword}.s3-website-us-east-1.amazonaws.com",
                f"https://{keyword}.s3.us-west-2.amazonaws.com",
                f"https://{keyword}.s3-accelerate.amazonaws.com",
            ])
        return buckets_to_test
    
    def enumerate_azure_storage(self, keywords):
        """Enumerate Azure storage accounts using keywords"""
        storage_endpoints = []
        for keyword in keywords:
            # Azure storage patterns
            storage_endpoints.extend([
                f"https://{keyword}.blob.core.windows.net",
                f"https://{keyword}.table.core.windows.net",
                f"https://{keyword}.queue.core.windows.net",
                f"https://{keyword}.file.core.windows.net",
            ])
        return storage_endpoints
    
    def enumerate_gcp_buckets(self, keywords):
        """Enumerate GCP Cloud Storage buckets using keywords"""
        buckets_to_test = []
        for keyword in keywords:
            # GCP bucket patterns
            buckets_to_test.extend([
                f"https://storage.googleapis.com/{keyword}",
                f"https://{keyword}.storage.googleapis.com",
                f"https://{keyword}-app.appspot.com",
                f"https://{keyword}.web.app",
                f"https://{keyword}.firebaseapp.com",
            ])
        return buckets_to_test
    
    def generate_cloud_endpoints(self, domain):
        """Generate cloud service endpoints for a domain"""
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
        # Remove 'www.' if present
        domain_clean = domain.replace('www.', '')
        
        endpoints = []
        
        if self.aws:
            # AWS endpoints
            endpoints.extend([
                f"https://{domain_clean}.s3.amazonaws.com",
                f"https://{domain_clean}.s3-website-us-east-1.amazonaws.com",
                f"https://{domain_clean}.cloudfront.net",
                f"https://{domain_clean}-cdn.cloudfront.net",
                f"https://{domain_clean}.execute-api.us-east-1.amazonaws.com",
                f"https://{domain_clean}.lambda-url.us-east-1.on.aws",
                f"https://{domain_clean}.elb.amazonaws.com",
                f"https://{domain_clean}.elasticbeanstalk.com",
            ])
        elif self.gcp:
            # GCP endpoints
            endpoints.extend([
                f"https://storage.googleapis.com/{domain_clean}",
                f"https://{domain_clean}.storage.googleapis.com",
                f"https://{domain_clean}-app.appspot.com",
                f"https://{domain_clean}-run.run.app",
                f"https://{domain_clean}-function.cloudfunctions.net",
                f"https://{domain_clean}.web.app",
                f"https://{domain_clean}.firebaseapp.com",
            ])
        elif self.azure:
            # Azure endpoints
            endpoints.extend([
                f"https://{domain_clean}.blob.core.windows.net",
                f"https://{domain_clean}.azurewebsites.net",
                f"https://{domain_clean}.azureedge.net",
                f"https://{domain_clean}.database.windows.net",
                f"https://{domain_clean}.redis.cache.windows.net",
                f"https://{domain_clean}.vault.azure.net",
                f"https://{domain_clean}-app.azurewebsites.net",
                f"https://{domain_clean}.app.services",
            ])
        
        return endpoints
    
    def fuzz_wildcard_domain(self, subdomain):
        """Test a wildcard domain"""
        # Construct domain with subdomain
        domain = f"{subdomain}.{self.wildcard_domain}"
        
        if self.verbosity >= 2:
            print(f"[DEBUG] Testing domain: {domain}")
        
        # Test as HTTPS and HTTP
        urls_to_test = [f"https://{domain}", f"http://{domain}"]
        
        for test_url in urls_to_test:
            try:
                response = self.session.head(test_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                
                with self.lock:
                    self.total_checked += 1
                    
                    # Check if status code is not filtered
                    if response.status_code not in self.filter_codes:
                        self.valid_found += 1
                        result = f"[{colors.green(str(response.status_code))}] {test_url} ({response.headers.get('Server', 'Unknown')})"
                        print(result)
                        if self.output_file:
                            with open(self.output_file, 'a') as f:
                                f.write(result.replace('\033[92m', '').replace('\033[0m', '') + '\n')
                        self.results.append({'url': test_url, 'status': response.status_code})
                        
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)
                    
            except (requests.Timeout, requests.ConnectionError):
                with self.lock:
                    self.total_checked += 1
                if self.verbosity >= 2:
                    print(f"[DEBUG] Failed to connect: {test_url}")
            except Exception as e:
                with self.lock:
                    self.total_checked += 1
                if self.verbosity >= 2:
                    print(f"[DEBUG] Error testing {test_url}: {str(e)}")
    
    def fuzz(self, word):
        """Test a single word/path"""
        # Support both FUZZ and * as placeholders
        url = self.target_url.replace('FUZZ', word).replace('*', word)
        
        if self.verbosity >= 2:
            print(f"[DEBUG] Testing path: {word}")
        
        # Test with extensions
        urls_to_test = [url]
        for ext in self.extensions:
            urls_to_test.append(f"{url}.{ext}")
        
        for test_url in urls_to_test:
            try:
                if self.verbosity >= 2:
                    print(f"[DEBUG] Requesting: {test_url}")
                
                if self.method == "GET":
                    response = self.session.get(test_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                else:
                    response = self.session.request(self.method, test_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                
                status = response.status_code
                
                # Skip filtered codes
                if status not in self.filter_codes:
                    with self.lock:
                        self.results.append({
                            'url': test_url,
                            'status': status,
                            'length': len(response.content),
                            'timestamp': datetime.now().isoformat()
                        })
                        self.valid_found += 1
                        # Color code status codes using Colors class
                        if 200 <= status < 300:
                            status_str = f"[{status:3d}]"
                            if self.use_colors:
                                status_str = colors.green(status_str)
                        elif 300 <= status < 400:
                            status_str = f"[{status:3d}]"
                            if self.use_colors:
                                status_str = colors.blue(status_str)
                        elif 400 <= status < 500:
                            status_str = f"[{status:3d}]"
                            if self.use_colors:
                                status_str = colors.yellow(status_str)
                        elif status >= 500:
                            status_str = f"[{status:3d}]"
                            if self.use_colors:
                                status_str = colors.red(status_str)
                        
                        # Professional formatting with aligned columns
                        url_str = test_url[:67] + "…" if len(test_url) > 68 else test_url
                        bytes_str = f"{len(response.content):>6}"
                        
                        print(f"  {status_str} {url_str:<68} {bytes_str} bytes")
                
                with self.lock:
                    self.total_checked += 1
                
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)
            
            except requests.Timeout:
                with self.lock:
                    self.total_checked += 1
                if self.verbosity >= 2:
                    print(f"[DEBUG] Timeout: {test_url}")
            except requests.ConnectionError:
                with self.lock:
                    self.total_checked += 1
                if self.verbosity >= 2:
                    print(f"[DEBUG] Connection error: {test_url}")
            except Exception as e:
                with self.lock:
                    self.total_checked += 1
                if self.verbosity >= 2:
                    print(f"[DEBUG] Error: {test_url} - {str(e)}")
    
    def worker(self, queue):
        """Worker thread"""
        while True:
            word = queue.get()
            if word is None:
                break
            self.fuzz(word)
            queue.task_done()
    
    def wildcard_worker(self, queue):
        """Worker thread for wildcard domain fuzzing"""
        while True:
            word = queue.get()
            if word is None:
                break
            self.fuzz_wildcard_domain(word)
            queue.task_done()
    
    def run_wildcard_domain_fuzzing(self):
        """Execute wildcard domain fuzzing"""
        print(f"\nMode: Wildcard Domain Fuzzing")
        print(f"Domain: {self.wildcard_domain}")
        print(f"Wordlist: built-in" if self.use_builtin else f"Wordlist: {self.wordlist_file}")
        print(f"Threads: {self.threads_count}")
        
        if self.verbosity >= 1:
            print(f"[*] Timeout: {self.timeout or 'default'} seconds")
            if self.rate_limit > 0:
                print(f"[*] Rate limit: {1.0/self.rate_limit:.2f} req/sec")
        
        print(f"\nStarting wildcard enumeration...\n")
        
        # Create queue and worker threads
        queue = Queue()
        threads = []
        
        for _ in range(self.threads_count):
            t = Thread(target=self.wildcard_worker, args=(queue,))
            t.start()
            threads.append(t)
        
        # Load wordlist
        words = self.load_wordlist()
        print(f"Subdomains to test: {len(words)}")
        
        self.total_checked = 0
        self.valid_found = 0
        self.results = []
        
        # Add words to queue
        for word in words:
            queue.put(word)
        
        # Wait for queue to be processed
        queue.join()
        
        # Stop workers
        for _ in range(self.threads_count):
            queue.put(None)
        
        for t in threads:
            t.join()
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Total tested: {self.total_checked}")
        print(f"Valid found: {self.valid_found}")
        
        if self.output_file:
            print(f"Results saved to: {self.output_file}")
    
    def run(self):
        """Execute the fuzzing"""
        # Check if wildcard domain mode
        if self.wildcard_domain:
            self.run_wildcard_domain_fuzzing()
            return
        
        # Check if cloud_enum keyword mode
        if self.cloud_enum_mode and self.keyword:
            self.run_cloud_enum_mode()
            return
        
        # Check if cloud enumeration mode (domain-based)
        is_cloud_mode = self.aws or self.gcp or self.azure
        
        if self.aws:
            wordlist_source = "AWS Cloud Services"
            mode_type = "Cloud Enumeration"
        elif self.gcp:
            wordlist_source = "GCP Cloud Services"
            mode_type = "Cloud Enumeration"
        elif self.azure:
            wordlist_source = "Azure Cloud Services"
            mode_type = "Cloud Enumeration"
        elif self.use_builtin:
            wordlist_source = "built-in"
            mode_type = "URL Fuzzing"
        else:
            wordlist_source = self.wordlist_file
            mode_type = "URL Fuzzing"
        
        print(f"\nMode: {mode_type}")
        print(f"Wordlist: {wordlist_source}")
        
        print(f"\nTarget: {self.target_url}")
        print(f"Threads: {self.threads_count}")
        print(f"Method: {self.method}")
        print(f"Filtering: {', '.join(map(str, sorted(self.filter_codes)))}")
        
        if self.verbosity >= 1:
            print(f"[*] Timeout: {self.timeout or 'default'} seconds")
            if self.rate_limit > 0:
                print(f"[*] Rate limit: {1.0/self.rate_limit:.2f} req/sec")
            if self.extensions:
                print(f"[*] Extensions: {', '.join(self.extensions)}")
            if self.follow_redirects:
                print(f"[*] Following redirects enabled")
        
        print(f"\nStarting enumeration...\n")
        
        # Create queue and worker threads
        queue = Queue()
        threads = []
        
        for _ in range(self.threads_count):
            t = Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)
        
        # Generate endpoints or use wordlist
        if is_cloud_mode:
            endpoints = self.generate_cloud_endpoints(self.target_url)
            self.total_checked = 0
            self.valid_found = 0
            
            if self.verbosity >= 2:
                print(f"[DEBUG] Generated {len(endpoints)} cloud endpoints to test\n")
            
            for endpoint in endpoints:
                self.test_cloud_endpoint(endpoint)
        else:
            words = self.load_wordlist()
            print(f"Words Loaded: {len(words)}")
            
            # Add words to queue
            for word in words:
                queue.put(word)
            
            # Wait for completion
            queue.join()
        
        # Stop workers
        for _ in range(self.threads_count):
            queue.put(None)
        for t in threads:
            t.join()
        
        # Print summary
        success_rate = (self.valid_found/max(1, self.total_checked)*100)
        
        print(f"\nEnumeration Complete!")
        print(f"\nStatistics:")
        print(f"  Total Checked: {self.total_checked}")
        print(f"  Valid Found: {self.valid_found}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Save results
        if self.output_file:
            self.save_results()
            print(f"  Results Saved: {self.output_file}")
        
        print()
    
    def run_cloud_enum_mode(self):
        """Run cloud_enum style keyword-based enumeration"""
        print(f"\nMode: Cloud Enumeration (cloud_enum style)")
        print(f"Keyword: {self.keyword}")
        
        # Determine which cloud providers to target
        providers = []
        if self.aws:
            providers.append("AWS")
        if self.gcp:
            providers.append("GCP")
        if self.azure:
            providers.append("Azure")
        
        # If no specific provider chosen, enumerate all
        if not providers:
            providers = ["AWS", "GCP", "Azure"]
            self.aws = self.gcp = self.azure = True
        
        print(f"Providers: {', '.join(providers)}")
        
        # Generate keyword mutations
        mutations = self.generate_keyword_mutations(self.keyword)
        print(f"\nKeyword Mutations: {len(mutations)}")
        print(f"Threads: {self.threads_count}")
        print(f"Filtering: {', '.join(map(str, sorted(self.filter_codes)))}")
        
        if self.verbosity >= 1:
            print(f"[*] Timeout: {self.timeout or 'default'} seconds")
            if self.verbosity >= 2:
                print(f"[DEBUG] Mutation list:")
                for m in mutations[:10]:  # Show first 10 mutations
                    print(f"  - {m}")
                if len(mutations) > 10:
                    print(f"  ... and {len(mutations)-10} more")
        
        print(f"\nStarting cloud enumeration...\n")
        
        # Create queue and worker threads
        queue = Queue()
        threads = []
        
        for _ in range(self.threads_count):
            t = Thread(target=self.worker, args=(queue,))
            t.start()
            threads.append(t)
        
        # Generate bucket endpoints for all mutations
        all_buckets = []
        
        if self.aws:
            aws_buckets = self.enumerate_s3_buckets(mutations)
            all_buckets.extend(aws_buckets)
            if self.verbosity >= 1:
                print(f"[*] Generated {len(aws_buckets)} AWS S3 endpoints")
        if self.gcp:
            gcp_buckets = self.enumerate_gcp_buckets(mutations)
            all_buckets.extend(gcp_buckets)
            if self.verbosity >= 1:
                print(f"[*] Generated {len(gcp_buckets)} GCP Storage endpoints")
        if self.azure:
            azure_buckets = self.enumerate_azure_storage(mutations)
            all_buckets.extend(azure_buckets)
            if self.verbosity >= 1:
                print(f"[*] Generated {len(azure_buckets)} Azure Storage endpoints")
        
        self.total_checked = 0
        self.valid_found = 0
        
        if self.verbosity >= 2:
            print(f"\n[DEBUG] Total endpoints to test: {len(all_buckets)}\n")
        else:
            print(f"Testing {len(all_buckets)} cloud endpoints...\n")
        
        # Test each bucket endpoint
        for endpoint in all_buckets:
            self.test_cloud_endpoint(endpoint)
        
        # Stop workers
        for _ in range(self.threads_count):
            queue.put(None)
        for t in threads:
            t.join()
        
        # Print summary
        success_rate = (self.valid_found/max(1, self.total_checked)*100)
        
        print(f"\nCloud Enumeration Complete!")
        print(f"\nStatistics:")
        print(f"  Total Checked: {self.total_checked}")
        print(f"  Valid Found: {self.valid_found}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Save results
        if self.output_file:
            self.save_results()
            print(f"  Results Saved: {self.output_file}")
        
        print()
    
    def test_cloud_endpoint(self, endpoint):
        """Test a cloud service endpoint"""
        try:
            if self.verbosity >= 2:
                print(f"[DEBUG] Testing cloud endpoint: {endpoint}")
            
            if self.method == "GET":
                response = self.session.get(endpoint, timeout=self.timeout, allow_redirects=self.follow_redirects)
            else:
                response = self.session.request(self.method, endpoint, timeout=self.timeout, allow_redirects=self.follow_redirects)
            
            status = response.status_code
            
            # Skip filtered codes
            if status not in self.filter_codes:
                with self.lock:
                    self.results.append({
                        'url': endpoint,
                        'status': status,
                        'length': len(response.content),
                        'timestamp': datetime.now().isoformat()
                    })
                    self.valid_found += 1
                    # Color code status codes using Colors class
                    if 200 <= status < 300:
                        status_str = f"[{status:3d}]"
                        if self.use_colors:
                            status_str = colors.green(status_str)
                    elif 300 <= status < 400:
                        status_str = f"[{status:3d}]"
                        if self.use_colors:
                            status_str = colors.blue(status_str)
                    elif 400 <= status < 500:
                        status_str = f"[{status:3d}]"
                        if self.use_colors:
                            status_str = colors.yellow(status_str)
                    elif status >= 500:
                        status_str = f"[{status:3d}]"
                        if self.use_colors:
                            status_str = colors.red(status_str)
                    
                    endpoint_str = endpoint[:67] + "…" if len(endpoint) > 68 else endpoint
                    bytes_str = f"{len(response.content):>6}"
                    
                    print(f"  {status_str} {endpoint_str:<68} {bytes_str} bytes")
            
            with self.lock:
                self.total_checked += 1
            
            if self.rate_limit > 0:
                time.sleep(self.rate_limit)
        
        except requests.Timeout:
            with self.lock:
                self.total_checked += 1
            if self.verbosity >= 2:
                print(f"[DEBUG] Timeout: {endpoint}")
        except requests.ConnectionError:
            with self.lock:
                self.total_checked += 1
        except Exception as e:
            with self.lock:
                self.total_checked += 1
    
    
    def save_results(self):
        """Save results to file"""
        if self.output_file.endswith('.json'):
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        elif self.output_file.endswith('.csv'):
            import csv
            with open(self.output_file, 'w', newline='') as f:
                if self.results:
                    writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                    writer.writeheader()
                    writer.writerows(self.results)
        else:
            with open(self.output_file, 'w') as f:
                for result in self.results:
                    f.write(f"{result['url']} [{result['status']}] ({result['length']} bytes)\n")


def print_banner():
    """Print ASCII banner"""
    banner = """


                                                    _.-^^---....,,--_
                                                 _--                  --_
                                               (<                       >)
                                               |                         |
                                                '-_                   _-'
                                                   ```--. . , ; .--'''
                                                         | |   |
                                                      .-=||  | |=-.
                                                      `-=#$%&%$#=-'
                                                         | ;  :|
                                                _____.,-#%&$@%#&#~,._____
                                                  Developed by: Not-4O4

             ███████╗███╗   ██╗██╗   ██╗███╗   ███╗ █████╗  ██████╗ ███████╗██████╗ ██████╗  ██████╗ ███╗   ██╗
             ██╔════╝████╗  ██║██║   ██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝██╔══██╗██╔══██╗██╔═══██╗████╗  ██║
             █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║███████║██║  ███╗█████╗  ██║  ██║██║  ██║██║   ██║██╔██╗ ██║
             ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝  ██║  ██║██║  ██║██║   ██║██║╚██╗██║
             ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗██████╔╝██████╔╝╚██████╔╝██║ ╚████║
             ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝

    """
    
    # Build tagline with proper dynamic centering
    tagline_text = 'Discover. Enumerate. Dominate.'
    try:
        import shutil
        terminal_width = shutil.get_terminal_size().columns
        # The visible text is always 30 chars: "Discover. Enumerate. Dominate."
        visible_width = 30
        padding = max(0, (terminal_width - visible_width) // 2)
        spaces = ' ' * padding
    except:
        spaces = ' ' * 45
    
    if colors.enabled:
        tagline = f"{spaces}{colors.white('Discover. Enumerate.')} {colors.red('Dominate.')}\n"
    else:
        tagline = f"{spaces}{tagline_text}\n"
    
    try:
        print(banner)
    except UnicodeEncodeError:
        print("\nEnumageddon\n")
    
    # Always print the tagline, even if banner fails
    try:
        print(tagline)
    except UnicodeEncodeError:
        print(f"{spaces}{tagline_text}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enumageddon - Web Fuzzer for bug bounty hunters",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('-u', '--url', required=False, default=None,
                        help='Target URL with FUZZ or * placeholder (e.g., https://target.com/FUZZ or https://api.target.com/v1/* or https://target.com/*/config)')
    parser.add_argument('-w', '--wordlist', required=False, default=None,
                        help='Path to wordlist file (optional: uses built-in wordlist if not specified)')
    parser.add_argument('-wc', '--wildcard-domain', required=False, default=None,
                        help='Wildcard domain fuzzing (e.g., example.com to enumerate api.example.com, www.example.com, etc.)')
    
    # Core optional arguments
    parser.add_argument('-t', '--threads', type=int, default=20, 
                        help='Number of threads (default: 20)')
    parser.add_argument('-x', '--extensions', 
                        help='Extensions to append (e.g., php,asp,html,js,txt)')
    parser.add_argument('-fc', '--filter-code', default='404', 
                        help='Status codes to filter (hide) (e.g., 404,403,500) (default: 404)')
    
    # Advanced options
    parser.add_argument('-rl', '--rate-limit', type=float, default=0, 
                        help='Requests per second max (0=unlimited) (default: 0)')
    parser.add_argument('--timeout', type=int, default=None, 
                        help='Request timeout in seconds (no default limit)')
    parser.add_argument('--method', default='GET', 
                        help='HTTP method: GET, POST, PUT, DELETE (default: GET)')
    parser.add_argument('-A', '--user-agent',
                        help='User-Agent string. Use preset (chrome, firefox, safari, opera, edge, bot, curl, mobile) or custom string')
    parser.add_argument('-fr', '--follow-redirects', action='store_true',
                        help='Follow HTTP redirects (301, 302, 307, 308)')
    parser.add_argument('-H', '--header', 
                        help='Custom header (format: "Key: Value") - repeatable')
    parser.add_argument('-o', '--output', 
                        help='Save results to file (.txt, .json, .csv)')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose output (-v for verbose, -vv for very verbose)')
    
    # Cloud service enumeration flags
    parser.add_argument('--aws', action='store_true',
                        help='Enumerate AWS S3 buckets (use with -k for keyword-based, or -u for domain-based)')
    parser.add_argument('--gcp', action='store_true',
                        help='Enumerate GCP Cloud Storage (use with -k for keyword-based, or -u for domain-based)')
    parser.add_argument('--azure', action='store_true',
                        help='Enumerate Azure Storage accounts (use with -k for keyword-based, or -u for domain-based)')
    
    # Cloud_enum style keyword-based enumeration
    parser.add_argument('-k', '--keyword',
                        help='Keyword for cloud_enum style enumeration to find cloud buckets (e.g., company name)')
    
    args = parser.parse_args()
    
    # Initialize global color object
    global colors
    colors = Colors(enabled=should_use_color() and not args.no_color)
    
    # Print banner after colors are initialized
    print_banner()
    
    # Interactive mode if no URL and no keyword provided
    if not args.url and not args.keyword and not args.wildcard_domain:
        help_text = """
========== ENUMAGEDDON - INTERACTIVE MODE ==========

USAGE & OPTIONS:

URL FUZZING:
  -u, --url URL              Target URL with FUZZ placeholder
  -w, --wordlist PATH        Custom wordlist file (optional)
  -x, --extensions EXT       Extensions to test (php,asp,html,etc)
  -fc, --filter-code CODES   Status codes to hide (e.g., 404,403)
  --method METHOD            HTTP method: GET, POST, PUT, DELETE
  -H, --header HEADER        Custom header (format: "Key: Value")
  -fr, --follow-redirects    Follow HTTP redirects

CLOUD ENUMERATION:
  -k, --keyword KEYWORD      Keyword for cloud service enumeration
  --aws                      Enumerate AWS S3 buckets
  --gcp                      Enumerate GCP Cloud Storage
  --azure                    Enumerate Azure Storage accounts

REQUEST CONFIGURATION:
  -t, --threads NUM          Number of threads (default: 20)
  -rl, --rate-limit NUM      Requests per second (0=unlimited)
  --timeout SEC              Request timeout in seconds
  -A, --user-agent PRESET    User-Agent preset or custom string
  -o, --output FILE          Save results to file (.json, .csv, .txt)
  --no-color                 Disable colored output
  -v, --verbose              Verbose output

INTERACTIVE COMMANDS:
  quit, exit, q              Exit interactive mode
  help                       Show this help message

====================================================

QUICK START EXAMPLES:
  enumageddon -u https://target.com/FUZZ
  enumageddon -k target --aws
  enumageddon -u https://target.com/api/FUZZ -w wordlist.txt -t 50
  enumageddon -u https://target.com/FUZZ -x php,asp,html
  enumageddon -k target --aws --gcp --azure -o results.json

Type 'help' for full options, or enter a command to continue.
        """
        
        # Interactive loop
        while True:
            # Print help text at the start
            print(help_text)
            
            # Get user input
            prompt_text = colors.red("Enumageddon> ") if colors.enabled else "Enumageddon> "
            try:
                user_input = input(prompt_text).strip()
            except EOFError:
                print("[!] EOF reached. Exiting.")
                sys.exit(1)
            
            # Handle interactive commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("[*] Exiting interactive mode")
                sys.exit(0)
            elif user_input.lower() == 'help':
                continue  # Re-display help
            elif not user_input:
                continue  # Empty input, re-display help
            
            # Parse the input as command line arguments
            input_args = user_input.split()
            
            # Check if it's a valid command (should contain -u or -k)
            if '-u' not in user_input and '-k' not in user_input:
                print("[!] Error: Command must contain -u (URL fuzzing) or -k (cloud enumeration)")
                print("[*] Type 'help' for available options\n")
                continue
            
            # Parse the input as arguments with error suppression
            import io
            from contextlib import redirect_stderr
            stderr_capture = io.StringIO()
            try:
                with redirect_stderr(stderr_capture):
                    parsed = parser.parse_args(input_args)
            except SystemExit as e:
                error_msg = stderr_capture.getvalue()
                if error_msg:
                    # Extract just the error, not the full usage
                    error_lines = error_msg.split('\n')
                    for line in error_lines:
                        if 'error:' in line.lower():
                            print(f"[!] {line.strip()}")
                            break
                else:
                    print("[!] Invalid command format")
                print("[*] Example: -u https://target.com/FUZZ")
                print("[*] Example: -k target --aws")
                print("[*] Type 'help' for available options\n")
                continue
            
            # Update args with parsed input
            args.url = parsed.url
            args.keyword = parsed.keyword
            args.wordlist = parsed.wordlist
            args.threads = parsed.threads
            args.timeout = parsed.timeout
            args.rate_limit = parsed.rate_limit
            args.extensions = parsed.extensions
            args.filter_code = parsed.filter_code
            args.method = parsed.method
            args.header = parsed.header
            args.output = parsed.output
            args.aws = parsed.aws
            args.gcp = parsed.gcp
            args.azure = parsed.azure
            args.user_agent = parsed.user_agent
            args.follow_redirects = parsed.follow_redirects
            args.no_color = parsed.no_color
            args.verbose = parsed.verbose
            args.wildcard_domain = parsed.wildcard_domain
            
            # Validate the parsed arguments
            if not args.url and not args.keyword and not args.wildcard_domain:
                print("[!] Error: Command must contain -u (URL fuzzing), -k (cloud enumeration), or -wc (wildcard domain fuzzing)")
                print("[*] Type 'help' for available options\n")
                continue
            
            # Break out of loop to run the fuzzer
            break
    
    # Main fuzzer loop - continues in interactive mode
    while True:
        # Validate URL and keyword arguments
        is_cloud = args.aws or args.gcp or args.azure
        is_keyword_mode = args.keyword is not None
        
        if is_keyword_mode:
            # Cloud_enum keyword mode - no URL needed
            if not args.keyword:
                print("[!] Error: Keyword is required for cloud_enum mode")
                continue
        elif is_cloud:
            # For cloud mode, domain is sufficient
            if not args.url:
                print("[!] Error: Domain is required for cloud enumeration")
                continue
        else:
            # For standard fuzzing, URL must have protocol and FUZZ placeholder
            if not args.url:
                print("[!] Error: URL is required")
                continue
            if not args.url.startswith(('http://', 'https://')):
                print("[!] Error: URL must start with http:// or https://")
                continue
        
        # Run fuzzer
        try:
            fuzzer = Fuzzer(
                target_url=args.url,
                wordlist=args.wordlist,
                threads=args.threads,
                timeout=args.timeout,
                rate_limit=args.rate_limit,
                extensions=args.extensions,
                filter_codes=args.filter_code,
                method=args.method,
                headers=args.header,
                output=args.output,
                aws=args.aws,
                gcp=args.gcp,
                azure=args.azure,
                keyword=args.keyword,
                cloud_enum_mode=is_keyword_mode,
                user_agent=args.user_agent,
                follow_redirects=args.follow_redirects,
                use_colors=colors.enabled,
                verbosity=args.verbose,
                wildcard_domain=args.wildcard_domain
            )
            fuzzer.run()
            print("\n[*] Scan completed. Returning to interactive mode...\n")
        except KeyboardInterrupt:
            print("\n[*] Scan interrupted by user. Returning to interactive mode...\n")
        except Exception as e:
            print(f"[!] Error: {e}\n")
        
        # Loop back to interactive mode
        if not args.url or (not args.aws and not args.gcp and not args.azure and not args.keyword and not args.wildcard_domain):
            # If started in interactive mode, ask for next command
            help_text = """
Enter your next command or 'help' for options:
  Enumageddon -u https://target.com/FUZZ
  enumageddon -k target --aws
  quit/exit/q to exit

            """
            print(help_text)
            
            prompt_text = colors.red("Enumageddon> ") if colors.enabled else "Enumageddon> "
            try:
                user_input = input(prompt_text).strip()
            except EOFError:
                print("[!] EOF reached. Exiting.")
                sys.exit(0)
            
            # Handle interactive commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("[*] Exiting Enumageddon")
                sys.exit(0)
            elif user_input.lower() == 'help':
                continue  # Re-display help
            elif not user_input:
                continue  # Empty input, re-display help
            
            # Parse the input as command line arguments
            input_args = user_input.split()
            
            # Check if it's a valid command (should contain -u or -k)
            if '-u' not in user_input and '-k' not in user_input:
                print("[!] Error: Command must contain -u (URL fuzzing) or -k (cloud enumeration)")
                print("[*] Type 'help' for available options\n")
                continue
            
            # Parse the input as arguments with error suppression
            import io
            from contextlib import redirect_stderr
            stderr_capture = io.StringIO()
            try:
                with redirect_stderr(stderr_capture):
                    parsed = parser.parse_args(input_args)
            except SystemExit as e:
                error_msg = stderr_capture.getvalue()
                if error_msg:
                    # Extract just the error, not the full usage
                    error_lines = error_msg.split('\n')
                    for line in error_lines:
                        if 'error:' in line.lower():
                            print(f"[!] {line.strip()}")
                            break
                else:
                    print("[!] Invalid command format")
                print("[*] Example: -u https://target.com/FUZZ")
                print("[*] Example: -k target --aws")
                print("[*] Type 'help' for available options\n")
                continue
            
            # Update args with parsed input
            args.url = parsed.url
            args.keyword = parsed.keyword
            args.wordlist = parsed.wordlist
            args.threads = parsed.threads
            args.timeout = parsed.timeout
            args.rate_limit = parsed.rate_limit
            args.extensions = parsed.extensions
            args.filter_code = parsed.filter_code
            args.method = parsed.method
            args.header = parsed.header
            args.output = parsed.output
            args.aws = parsed.aws
            args.gcp = parsed.gcp
            args.azure = parsed.azure
            args.user_agent = parsed.user_agent
            args.follow_redirects = parsed.follow_redirects
            args.no_color = parsed.no_color
            args.verbose = parsed.verbose
            args.wildcard_domain = parsed.wildcard_domain
        else:
            # If started with command-line arguments, exit after one scan
            break


if __name__ == "__main__":
    main()
