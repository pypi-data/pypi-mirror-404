"""Type definitions for Easy Enrichment API responses."""

from typing import List, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class EnrichmentResult(TypedDict, total=False):
    """Enriched transaction data returned by the API."""

    merchant_name: str
    """Clean, normalized merchant name."""

    category: str
    """Spending category (e.g., 'Food & Dining', 'Shopping')."""

    subcategory: str
    """More specific subcategory (e.g., 'Coffee Shops', 'Electronics')."""

    logo_url: str
    """URL to the merchant's logo image."""

    website: str
    """Merchant's website URL."""

    is_subscription: bool
    """Whether the transaction appears to be a recurring subscription."""

    merchant_type: str
    """Type of merchant (e.g., 'online', 'brick_and_mortar')."""

    confidence: float
    """Confidence score of the enrichment (0.0 to 1.0)."""

    original_description: str
    """The original transaction description that was submitted."""

    mcc_code: str
    """Merchant Category Code."""

    carbon_footprint: Optional[float]
    """Estimated carbon footprint in kg CO2e, if available."""


class BillingInfo(TypedDict, total=False):
    """Billing and usage information."""

    requests_used: int
    """Total number of API requests used in the current period."""

    requests_limit: int
    """Maximum number of requests allowed in the current period."""

    period_start: str
    """Start date of the current billing period (ISO 8601)."""

    period_end: str
    """End date of the current billing period (ISO 8601)."""


class EnrichResponse(TypedDict, total=False):
    """Response from the single enrich endpoint."""

    success: bool
    """Whether the request was successful."""

    data: EnrichmentResult
    """The enriched transaction data."""

    request_id: str
    """Unique identifier for this API request."""


class BatchResponse(TypedDict, total=False):
    """Response from the batch enrich endpoint."""

    success: bool
    """Whether the request was successful."""

    data: List[EnrichmentResult]
    """List of enriched transaction results."""

    request_id: str
    """Unique identifier for this API request."""

    count: int
    """Number of transactions processed."""


class UsageResponse(TypedDict, total=False):
    """Response from the usage endpoint."""

    success: bool
    """Whether the request was successful."""

    requests_used: int
    """Total API requests used in the current period."""

    requests_limit: int
    """Maximum requests allowed in the current period."""

    period_start: str
    """Start date of the current billing period."""

    period_end: str
    """End date of the current billing period."""


class BalanceResponse(TypedDict, total=False):
    """Response from the balance endpoint."""

    success: bool
    """Whether the request was successful."""

    balance: float
    """Current account balance in USD."""

    currency: str
    """Currency code (e.g., 'USD')."""
