"""
Scope Parser Module
Handles parsing scope.txt file and wildcard pattern matching
"""

import re
from pathlib import Path
from typing import List, Set


class ScopeParser:
    def __init__(self, scope_file: str = "scope.txt"):
        self.scope_file = scope_file
        self.domains = []
        self.wildcard_patterns = []
    
    def load_scope(self) -> bool:
        """
        Load domains from scope.txt file
        Returns True if successful, False otherwise
        """
        try:
            if not Path(self.scope_file).exists():
                print(f"[!] Error: {self.scope_file} not found")
                return False
            
            with open(self.scope_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    if '*' in line:
                        self.wildcard_patterns.append(line)
                    else:
                        self.domains.append(line)
            
            print(f"[+] Loaded {len(self.domains)} exact domains")
            print(f"[+] Loaded {len(self.wildcard_patterns)} wildcard patterns")
            return True
        
        except Exception as e:
            print(f"[!] Error loading scope file: {e}")
            return False
    
    def is_in_scope(self, domain: str) -> bool:
        """
        Check if a domain matches any scope rules
        Supports both exact matches and wildcard patterns
        """
        # Check exact matches
        if domain in self.domains:
            return True
        
        # Check wildcard patterns
        for pattern in self.wildcard_patterns:
            if self._matches_pattern(domain, pattern):
                return True
        
        return False
    
    @staticmethod
    def _matches_pattern(domain: str, pattern: str) -> bool:
        """
        Check if a domain matches a wildcard pattern
        Example: www.dev.example.com matches *.example.com and *.dev.example.com
        """
        # Convert pattern to regex
        # * becomes a regex that matches any subdomain segment
        regex_pattern = pattern.replace('.', r'\.').replace('*', r'[a-zA-Z0-9\-]+')
        regex_pattern = f"^{regex_pattern}$"
        
        return re.match(regex_pattern, domain) is not None
    
    def get_all_domains(self) -> List[str]:
        """Return all exact domains (non-wildcard)"""
        return self.domains
    
    def get_all_patterns(self) -> List[str]:
        """Return all wildcard patterns"""
        return self.wildcard_patterns
