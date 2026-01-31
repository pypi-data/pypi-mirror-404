"""
Access L402 Resource Tool

Fetches URLs with automatic L402 payment handling.
"""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..budget import BudgetManager
    from ..l402_client import L402Client

logger = logging.getLogger("lightning-enable-mcp.tools.access")


async def access_l402_resource(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    max_sats: int = 1000,
    l402_client: "L402Client | None" = None,
    budget_manager: "BudgetManager | None" = None,
) -> str:
    """
    Fetch a URL with automatic L402 payment handling.

    If the server returns a 402 Payment Required response with an L402 challenge,
    this function will automatically pay the invoice and retry the request.

    Args:
        url: The URL to fetch
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional additional request headers
        body: Optional request body for POST/PUT requests
        max_sats: Maximum satoshis to pay for this request
        l402_client: L402 client instance
        budget_manager: Budget manager for tracking spending

    Returns:
        Response body text or error message
    """
    if not l402_client:
        return "Error: L402 client not initialized. Check NWC connection."

    headers = headers or {}
    method = method.upper()

    # Validate method
    if method not in ("GET", "POST", "PUT", "DELETE"):
        return f"Error: Invalid HTTP method: {method}"

    try:
        # Check budget before making request
        if budget_manager:
            # We don't know the cost yet, but check if we have any remaining budget
            status = budget_manager.get_status()
            if status["remaining"] <= 0:
                return (
                    f"Error: Session budget exhausted. "
                    f"Spent {status['spent']}/{status['limits']['per_session']} sats. "
                    f"Use configure_budget to increase limit."
                )

        # Make request with L402 handling
        response_text, amount_paid = await l402_client.fetch(
            url=url,
            method=method,
            headers=headers,
            body=body,
            max_sats=max_sats,
        )

        # Record payment if one was made
        if amount_paid is not None and budget_manager:
            budget_manager.record_payment(
                url=url,
                amount_sats=amount_paid,
                invoice="(auto-paid)",
                preimage="(auto-paid)",
                status="success",
            )
            logger.info(f"Paid {amount_paid} sats for L402 access to {url}")

        # Format response
        result = {
            "success": True,
            "url": url,
            "method": method,
            "paid_sats": amount_paid,
            "response": response_text[:5000] if len(response_text) > 5000 else response_text,
        }

        if amount_paid:
            result["message"] = f"Paid {amount_paid} sats for access"

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.exception(f"Error accessing {url}")

        error_result = {
            "success": False,
            "url": url,
            "method": method,
            "error": str(e),
        }

        return json.dumps(error_result, indent=2)
