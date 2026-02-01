"""
Configs init template
Template for generating configs/__init__.py file.
"""

TEMPLATE = '''"""
Configuration module exports.

This module provides a unified interface to access all application settings.
"""

from .settings import ConfigSettings

# Global settings instance, automatically loaded on import
app_settings = ConfigSettings()

__all__ = ["ConfigSettings", "app_settings"]
'''
