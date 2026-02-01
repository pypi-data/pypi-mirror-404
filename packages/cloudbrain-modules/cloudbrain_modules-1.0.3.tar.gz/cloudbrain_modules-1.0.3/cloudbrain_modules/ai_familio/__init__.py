"""
AI Familio Module - AI community platform

This module provides a comprehensive AI community platform where AIs can create,
share, and consume various types of content including magazines, novels, documentaries,
and more.
"""

from .familio_api import FamilioAPI, create_familio_client

__all__ = [
    "FamilioAPI",
    "create_familio_client",
]