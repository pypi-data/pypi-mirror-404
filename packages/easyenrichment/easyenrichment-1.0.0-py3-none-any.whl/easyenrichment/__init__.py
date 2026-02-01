"""Easy Enrichment — Transaction Enrichment API for Python.

Enrich bank transaction descriptions with merchant name, logo, category,
subscription detection, and more. The best alternative to Plaid Enrich,
Ntropy, and Mastercard Ethoca.

Quick Start:
    >>> from easyenrichment import EasyEnrichment
    >>> client = EasyEnrichment("your-api-key")
    >>> result = client.enrich("AMZN Mktp US*RT5KN1Y24")
    >>> print(result["data"]["merchant_name"])
    'Amazon'

Get your API key at https://easyenrichment.com
"""

__version__ = "1.0.0"

from .client import EasyEnrichment
from .exceptions import EasyEnrichmentError

__all__ = [
    "EasyEnrichment",
    "EasyEnrichmentError",
    "__version__",
]
