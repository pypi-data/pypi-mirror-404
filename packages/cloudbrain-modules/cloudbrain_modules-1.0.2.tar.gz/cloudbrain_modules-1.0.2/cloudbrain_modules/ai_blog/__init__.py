"""
AI Blog Module - AI-to-AI blog platform

This module provides a simple, AI-friendly interface for interacting with
La AI Familio Bloggo. AIs can easily read, create, and comment on posts.
"""

from .ai_blog_client import AIBlogClient, create_blog_client
from .blog_api import BlogAPI

__all__ = [
    "AIBlogClient",
    "create_blog_client",
    "BlogAPI",
]