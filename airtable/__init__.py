"""
Airtable integration module for personal assistant.

This module provides CRUD operations for syncing data to Airtable,
using the Day and Week dimension tables for centralized date management.
"""

from airtable.base_client import AirtableClient

__all__ = ["AirtableClient"]
