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

__version__ = "1.0.4"
__author__ = "Not-4O4"

# This ensures enumageddon can be imported and used as a module
__all__ = [
    'Fuzzer',
    'Colors',
    'should_use_color',
    'print_banner',
    'main',
]
