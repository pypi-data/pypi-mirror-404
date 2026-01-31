"""Configuration module for MCP schema server.

This module handles environment-based configuration including
table ignore patterns with regex support.
"""

import os
import re
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TableIgnoreConfig:
    """Configuration for table ignore patterns.
    
    Parses IGNORE_TABLES environment variable and provides
    pattern matching for table names.
    
    Environment Variable:
        IGNORE_TABLES: Comma-separated list of patterns
            Example: "temp_*,db_subscription_*,audit_log"
            
    Pattern Syntax:
        - Exact match: "audit_log" matches only "audit_log"
        - Wildcard *: "temp_*" matches "temp_table", "temp_backup", etc.
        - Full regex supported: "^db_.*_backup$" for advanced patterns
    """
    
    def __init__(self):
        self._patterns: List[re.Pattern] = []
        self._raw_patterns: List[str] = []
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load ignore patterns from environment variable."""
        ignore_tables_env = os.getenv('IGNORE_TABLES', '').strip()
        
        if not ignore_tables_env:
            return
        
        # Split by comma and process each pattern
        raw_patterns = [p.strip() for p in ignore_tables_env.split(',') if p.strip()]
        
        for pattern in raw_patterns:
            self._raw_patterns.append(pattern)
            try:
                # Convert simple wildcards to regex
                # If pattern contains regex special chars (other than *), treat as regex
                if self._is_regex_pattern(pattern):
                    # Treat as full regex
                    compiled = re.compile(pattern, re.IGNORECASE)
                else:
                    # Convert wildcards: * -> .*, ? -> .
                    regex_pattern = pattern.replace('*', '.*').replace('?', '.')
                    # Anchor to match full string
                    regex_pattern = f'^{regex_pattern}$'
                    compiled = re.compile(regex_pattern, re.IGNORECASE)
                
                self._patterns.append(compiled)
            except re.error as e:
                # Log warning but continue with other patterns
                import logging
                logging.getLogger('mcp_schema_server').warning(
                    f"Invalid ignore pattern '{pattern}': {e}"
                )
    
    def _is_regex_pattern(self, pattern: str) -> bool:
        """Check if pattern appears to be a full regex expression.
        
        Args:
            pattern: The pattern to check
            
        Returns:
            True if pattern contains regex metacharacters (beyond wildcards)
        """
        # Regex special chars excluding * and ? which we treat as wildcards
        regex_chars = set('.^$+{}[]|()\\')
        return any(c in pattern for c in regex_chars)
    
    def should_ignore(self, table_name: str) -> bool:
        """Check if a table name matches any ignore pattern.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table should be ignored, False otherwise
        """
        if not self._patterns:
            return False
        
        return any(pattern.match(table_name) for pattern in self._patterns)
    
    def get_patterns(self) -> List[str]:
        """Get list of raw pattern strings.
        
        Returns:
            List of pattern strings as configured
        """
        return self._raw_patterns.copy()
    
    def is_configured(self) -> bool:
        """Check if any ignore patterns are configured.
        
        Returns:
            True if at least one pattern is configured
        """
        return len(self._patterns) > 0


# Global instance for caching
_ignore_config: Optional[TableIgnoreConfig] = None


def get_ignore_config() -> TableIgnoreConfig:
    """Get the global table ignore configuration.
    
    Returns:
        TableIgnoreConfig instance (cached)
    """
    global _ignore_config
    if _ignore_config is None:
        _ignore_config = TableIgnoreConfig()
    return _ignore_config


def should_ignore_table(table_name: str) -> bool:
    """Check if a table should be ignored based on configured patterns.
    
    Convenience function that uses the global configuration.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if table should be ignored, False otherwise
        
    Example:
        >>> should_ignore_table('temp_backup')
        True  # If IGNORE_TABLES includes "temp_*"
    """
    return get_ignore_config().should_ignore(table_name)


def reload_ignore_config() -> None:
    """Reload ignore patterns from environment.
    
    Useful for testing or when environment changes.
    """
    global _ignore_config
    _ignore_config = TableIgnoreConfig()
