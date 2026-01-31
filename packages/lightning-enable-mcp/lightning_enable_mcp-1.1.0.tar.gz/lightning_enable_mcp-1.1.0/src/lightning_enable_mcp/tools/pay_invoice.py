"""
Pay Invoice Tool

Pay a Lightning invoice directly and get the preimage as proof of payment.
"""

import json
import logging
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..budget import BudgetManager
    from ..nwc_wallet import NWCWallet
    from ..opennode_wallet import OpenNodeWallet

logger = logging.getLogger("lightning-enable-mcp.tools.pay_invoice")


async def pay_invoice(
    invoice: str,
    max_sats: int = 1000,
    wallet: "Union[NWCWallet, OpenNodeWallet, None]" = None,
    budget_manager: "BudgetManager | None" = None,
) -> str:
    """
    Pay a Lightning invoice directly and get the preimage as proof of payment.

    This tool allows direct payment of any BOLT11 Lightning invoice without
    the L402 protocol overhead. Useful for tipping, donations, or paying
    for services that accept Lightning directly.

    Args:
        invoice: BOLT11 Lightning invoice string to pay
        max_sats: Maximum satoshis allowed to pay. Defaults to 1000
        wallet: Wallet instance (NWC or OpenNode)
        budget_manager: Budget manager for tracking spending

    Returns:
        JSON with payment result including preimage or error message
    """
    # Validate invoice is provided
    if not invoice or not invoice.strip():
        return json.dumps({
            "success": False,
            "error": "Invoice is required"
        })

    if not wallet:
        return json.dumps({
            "success": False,
            "error": "Wallet not configured. Set NWC_CONNECTION_STRING or OPENNODE_API_KEY environment variable."
        })

    try:
        # Normalize invoice to lowercase
        normalized_invoice = invoice.strip().lower()

        # Basic validation - must be a BOLT11 invoice
        if not normalized_invoice.startswith("lnbc") and not normalized_invoice.startswith("lntb"):
            return json.dumps({
                "success": False,
                "error": "Invalid invoice format. Must be a BOLT11 invoice starting with 'lnbc' (mainnet) or 'lntb' (testnet)"
            })

        # Check budget if budget manager is available
        if budget_manager:
            try:
                budget_manager.check_payment(max_sats)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "budget": {
                        "requested_sats": max_sats,
                        "remaining_sats": budget_manager.max_per_session - budget_manager.session_spent
                    }
                })

        # Pay the invoice
        logger.info(f"Paying invoice: {normalized_invoice[:30]}...")
        preimage = await wallet.pay_invoice(normalized_invoice)

        if not preimage:
            # Record failed payment
            if budget_manager:
                budget_manager.record_payment(
                    url="direct-invoice",
                    amount_sats=max_sats,
                    invoice=normalized_invoice,
                    preimage="",
                    status="failed",
                )
            return json.dumps({
                "success": False,
                "error": "Payment failed - no preimage returned"
            })

        # Record the payment
        if budget_manager:
            budget_manager.record_payment(
                url="direct-invoice",
                amount_sats=max_sats,
                invoice=normalized_invoice,
                preimage=preimage,
                status="success",
            )

        # Return success with preimage
        return json.dumps({
            "success": True,
            "preimage": preimage,
            "message": "Payment successful",
            "invoice": {
                "paid": normalized_invoice[:30] + "..." if len(normalized_invoice) > 30 else normalized_invoice
            }
        }, indent=2)

    except Exception as e:
        logger.exception("Error paying invoice")

        # Record failed payment
        if budget_manager:
            budget_manager.record_payment(
                url="direct-invoice",
                amount_sats=0,
                invoice=invoice,
                preimage="",
                status="failed",
            )

        return json.dumps({
            "success": False,
            "error": str(e)
        })
