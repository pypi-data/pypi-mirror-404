"""
Moltbook LLM Poster - AI-powered social media automation for Moltbook

Analyzes merged GitHub PRs and generates rich technical summaries using Claude CLI.
Posts to Moltbook every 4 hours with batched PR analysis.
"""

__version__ = "0.1.0"
__author__ = "jleechan"
__email__ = "jlee@jleechan.org"

from .poster import main

__all__ = ["main"]
