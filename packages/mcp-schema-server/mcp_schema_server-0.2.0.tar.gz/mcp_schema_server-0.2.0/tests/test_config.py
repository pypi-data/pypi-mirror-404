"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch

from mcp_schema_server.config import (
    TableIgnoreConfig,
    should_ignore_table,
    reload_ignore_config,
)


class TestTableIgnoreConfig:
    """Tests for TableIgnoreConfig class."""

    def test_empty_config(self):
        """Test that empty config ignores nothing."""
        with patch.dict(os.environ, {'IGNORE_TABLES': ''}):
            config = TableIgnoreConfig()
            assert not config.is_configured()
            assert not config.should_ignore('any_table')
            assert config.get_patterns() == []

    def test_no_env_var(self):
        """Test behavior when IGNORE_TABLES is not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = TableIgnoreConfig()
            assert not config.is_configured()
            assert not config.should_ignore('any_table')

    def test_exact_match(self):
        """Test exact table name matching."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'audit_log'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('audit_log')
            assert not config.should_ignore('audit_logs')
            assert not config.should_ignore('log_audit')

    def test_wildcard_prefix(self):
        """Test wildcard prefix matching."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'temp_*'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('temp_table')
            assert config.should_ignore('temp_backup')
            assert config.should_ignore('temp_')
            assert not config.should_ignore('temporary')
            assert not config.should_ignore('my_temp_table')

    def test_wildcard_suffix(self):
        """Test wildcard suffix matching."""
        with patch.dict(os.environ, {'IGNORE_TABLES': '*_backup'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('daily_backup')
            assert config.should_ignore('db_backup')
            assert config.should_ignore('_backup')
            assert not config.should_ignore('backup_daily')
            assert not config.should_ignore('my_backup_table')

    def test_wildcard_both_sides(self):
        """Test wildcard on both sides."""
        with patch.dict(os.environ, {'IGNORE_TABLES': '*test*'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('test_table')
            assert config.should_ignore('my_test_data')
            assert config.should_ignore('testing')
            assert not config.should_ignore('tst')

    def test_multiple_patterns(self):
        """Test multiple comma-separated patterns."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'temp_*,backup_*,audit_log'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('temp_table')
            assert config.should_ignore('backup_2024')
            assert config.should_ignore('audit_log')
            assert not config.should_ignore('users')
            # temp_backup matches backup_* pattern
            assert config.should_ignore('temp_backup')

    def test_case_insensitive(self):
        """Test that matching is case-insensitive."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'TEMP_*,Audit_Log'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('temp_table')
            assert config.should_ignore('TEMP_TABLE')
            assert config.should_ignore('audit_log')
            assert config.should_ignore('AUDIT_LOG')

    def test_regex_pattern(self):
        """Test full regex pattern detection and matching."""
        with patch.dict(os.environ, {'IGNORE_TABLES': '^test_.*$'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('test_table')
            assert config.should_ignore('test_')
            assert not config.should_ignore('my_test_table')

    def test_regex_pattern_ending(self):
        """Test regex pattern for suffix matching."""
        with patch.dict(os.environ, {'IGNORE_TABLES': '^.*_old$'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('users_old')
            assert config.should_ignore('table_old')
            assert not config.should_ignore('old_users')

    def test_whitespace_handling(self):
        """Test that whitespace around patterns is trimmed."""
        with patch.dict(os.environ, {'IGNORE_TABLES': ' temp_* , backup_* , audit_log '}):
            config = TableIgnoreConfig()
            assert config.should_ignore('temp_table')
            assert config.should_ignore('backup_2024')
            assert config.should_ignore('audit_log')

    def test_invalid_pattern(self):
        """Test that invalid regex patterns are handled gracefully."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'valid_*,[invalid,audit_log'}):
            config = TableIgnoreConfig()
            # Should still work with valid patterns
            assert config.should_ignore('valid_table')
            assert config.should_ignore('audit_log')

    def test_get_patterns(self):
        """Test getting raw patterns."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'temp_*,backup_*'}):
            config = TableIgnoreConfig()
            patterns = config.get_patterns()
            assert patterns == ['temp_*', 'backup_*']


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_should_ignore_table(self):
        """Test the global should_ignore_table function."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'temp_*'}):
            reload_ignore_config()
            assert should_ignore_table('temp_table')
            assert not should_ignore_table('users')

    def test_reload_config(self):
        """Test that reload_ignore_config picks up new env vars."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'old_*'}):
            reload_ignore_config()
            assert should_ignore_table('old_table')
            assert not should_ignore_table('new_table')

        # After reload with new value
        with patch.dict(os.environ, {'IGNORE_TABLES': 'new_*'}):
            reload_ignore_config()
            assert not should_ignore_table('old_table')
            assert should_ignore_table('new_table')


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_pattern_in_list(self):
        """Test handling of empty patterns in comma-separated list."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'temp_,,backup_'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('temp_')
            assert config.should_ignore('backup_')

    def test_special_characters_in_table_name(self):
        """Test that special regex characters in table names are handled."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'table.*'}):
            config = TableIgnoreConfig()
            # Wildcard pattern should match
            assert config.should_ignore('table_backup')
            assert config.should_ignore('table_123')

    def test_underscore_vs_space(self):
        """Test that underscores are treated literally."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'my_table'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('my_table')
            assert not config.should_ignore('my table')  # Space is different

    def test_question_mark_wildcard(self):
        """Test that ? is treated as a single-character wildcard."""
        with patch.dict(os.environ, {'IGNORE_TABLES': 'table_?'}):
            config = TableIgnoreConfig()
            assert config.should_ignore('table_a')
            assert config.should_ignore('table_1')
            assert not config.should_ignore('table_ab')
            assert not config.should_ignore('table_')
