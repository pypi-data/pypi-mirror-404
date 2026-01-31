"""
License Tools

MCP tools for L402 license management.
"""

import json
import logging
from datetime import datetime, timezone

from ..license import LicenseService, LocalLicense, detect_wallet_type

logger = logging.getLogger("lightning-enable-mcp.tools.license")


async def unlock_l402_features(
    wallet: object,
    license_service: LicenseService,
    wallet_pubkey: str | None = None,
    relay_url: str | None = None,
) -> str:
    """
    Purchase L402 license to unlock premium features.
    One-time payment of 6,000 sats, valid forever.

    Args:
        wallet: The wallet to use for payment
        license_service: License service instance
        wallet_pubkey: NWC wallet pubkey (if available)
        relay_url: NWC relay URL (for wallet type detection)

    Returns:
        JSON result string
    """
    # Check if wallet is configured
    if wallet is None:
        return json.dumps({
            "success": False,
            "error": "Wallet not configured",
            "message": (
                "Please configure a wallet first. Options:\n\n"
                "For L402 compatibility (recommended):\n"
                "- NWC_CONNECTION_STRING - Nostr Wallet Connect (Alby, CoinOS, Mutiny)\n\n"
                "Other wallets (direct payments only, no L402):\n"
                "- STRIKE_API_KEY - Strike wallet\n"
                "- OPENNODE_API_KEY - OpenNode wallet"
            )
        })

    # Check wallet type compatibility
    wallet_class_name = wallet.__class__.__name__.lower()
    if "strike" in wallet_class_name or "opennode" in wallet_class_name:
        return json.dumps({
            "success": False,
            "error": "Wallet not L402 compatible",
            "walletType": wallet_class_name,
            "message": (
                f"Your wallet ({wallet_class_name}) does not return payment preimage, "
                "which is required for L402.\n\n"
                "L402 requires a wallet that returns the preimage after payment. "
                "Compatible wallets:\n"
                "- NWC with Alby, CoinOS, Mutiny, Zeus, Bluewallet\n\n"
                "Please reconfigure with an L402-compatible wallet to purchase a license.\n\n"
                f"Note: {wallet_class_name} can still be used for direct payments (pay_invoice), "
                "just not for L402."
            )
        })

    # Set wallet pubkey if available
    if wallet_pubkey:
        wallet_type = detect_wallet_type(relay_url)
        license_service.set_wallet_pubkey(wallet_pubkey, wallet_type)

    # Get identifier
    identifier = license_service.bound_identifier
    identifier_type = license_service.identifier_type

    if not identifier:
        return json.dumps({
            "success": False,
            "error": "Could not detect wallet identifier",
            "message": "Unable to detect your wallet pubkey or generate a device ID. Please try again."
        })

    # Check if already licensed
    if license_service.is_licensed:
        local_license = license_service.get_local_license()
        return json.dumps({
            "success": True,
            "alreadyLicensed": True,
            "licenseKey": license_service.license_key,
            "boundIdentifier": identifier[:16] + "...",
            "identifierType": identifier_type,
            "activatedAt": local_license.activated_at.isoformat() if local_license else None,
            "message": "You already have an active L402 license! All L402 features are unlocked."
        })

    # Check if license exists on server
    existing_check = await license_service.check_license_async(identifier)
    if existing_check and existing_check.get("hasLicense"):
        # License exists on server, save locally
        license = LocalLicense(
            license_key=existing_check.get("licenseKey", ""),
            bound_identifier=identifier,
            identifier_type=existing_check.get("identifierType") or identifier_type or "unknown",
            wallet_type=existing_check.get("walletType"),
            activated_at=datetime.fromisoformat(existing_check["activatedAt"]) if existing_check.get("activatedAt") else datetime.now(timezone.utc),
            last_validated_at=datetime.now(timezone.utc),
            is_valid=True,
        )
        license_service.save_local_license(license)

        return json.dumps({
            "success": True,
            "alreadyLicensed": True,
            "licenseKey": existing_check.get("licenseKey"),
            "restored": True,
            "message": "License found and restored! Your L402 features are now unlocked."
        })

    # Detect wallet type
    wallet_type = detect_wallet_type(relay_url) or "nwc"

    # Initiate license purchase
    logger.info(f"Initiating license purchase for {identifier[:16]}...")

    purchase_result = await license_service.purchase_license_async(
        identifier=identifier,
        identifier_type=identifier_type,
        wallet_type=wallet_type,
    )

    if not purchase_result:
        return json.dumps({
            "success": False,
            "error": "Failed to initiate license purchase",
            "message": "Could not connect to license server. Please check your internet connection."
        })

    if not purchase_result.get("success"):
        return json.dumps({
            "success": False,
            "error": purchase_result.get("error", "Purchase failed"),
            "message": purchase_result.get("message")
        })

    # Check if already licensed (server-side check)
    if purchase_result.get("alreadyLicensed"):
        license = LocalLicense(
            license_key=purchase_result.get("licenseKey", ""),
            bound_identifier=identifier,
            identifier_type=identifier_type or "unknown",
            wallet_type=wallet_type,
            activated_at=datetime.now(timezone.utc),
            last_validated_at=datetime.now(timezone.utc),
            is_valid=True,
        )
        license_service.save_local_license(license)

        return json.dumps({
            "success": True,
            "alreadyLicensed": True,
            "licenseKey": purchase_result.get("licenseKey"),
            "message": purchase_result.get("message", "You already have an active license!")
        })

    # Get the invoice to pay
    invoice = purchase_result.get("invoice")
    if not invoice:
        return json.dumps({
            "success": False,
            "error": "No invoice received",
            "message": "License server did not return an invoice."
        })

    amount_sats = purchase_result.get("amountSats", 6000)
    logger.info(f"Paying invoice ({amount_sats} sats)...")

    # Pay the invoice
    try:
        preimage = await wallet.pay_invoice(invoice)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": "Payment failed",
            "message": str(e),
            "invoice": invoice,
            "amountSats": amount_sats,
            "hint": "You can try paying this invoice manually with your wallet."
        })

    if not preimage:
        return json.dumps({
            "success": False,
            "error": "No preimage received",
            "message": (
                "Payment succeeded but your wallet didn't return the preimage. "
                "This is required to activate your license. "
                "Please use a wallet that returns preimage (Alby, CoinOS, Mutiny, or LND)."
            )
        })

    logger.info("Payment successful, activating license...")

    # Activate the license with preimage
    activate_result = await license_service.activate_license_async(
        preimage=preimage,
        identifier=identifier,
    )

    if not activate_result or not activate_result.get("success"):
        return json.dumps({
            "success": False,
            "error": "Activation failed",
            "preimage": preimage,
            "message": (
                activate_result.get("message") if activate_result else
                "Failed to activate license. Payment was made but activation failed. "
                "Please contact support with your preimage for manual activation."
            )
        })

    # Save license locally
    new_license = LocalLicense(
        license_key=activate_result.get("licenseKey", ""),
        bound_identifier=identifier,
        identifier_type=identifier_type or "unknown",
        wallet_type=wallet_type,
        activated_at=datetime.now(timezone.utc),
        last_validated_at=datetime.now(timezone.utc),
        is_valid=True,
    )
    license_service.save_local_license(new_license)

    return json.dumps({
        "success": True,
        "licenseKey": activate_result.get("licenseKey"),
        "amountPaidSats": amount_sats,
        "boundIdentifier": identifier[:16] + "...",
        "identifierType": identifier_type,
        "walletType": wallet_type,
        "message": (
            "L402 features unlocked! Your license is valid forever. "
            "You can now use access_l402_resource and pay_l402_challenge tools."
        )
    })


async def check_l402_license(
    license_service: LicenseService,
) -> str:
    """
    Check the current L402 license status.

    Args:
        license_service: License service instance

    Returns:
        JSON result string
    """
    local_license = license_service.get_local_license()
    is_licensed = license_service.is_licensed
    identifier = license_service.bound_identifier

    # Try to refresh from API if we have an identifier
    server_status = None
    if identifier:
        server_status = await license_service.check_license_async(identifier)

    if is_licensed or (server_status and server_status.get("hasLicense")):
        return json.dumps({
            "success": True,
            "licensed": True,
            "licenseKey": license_service.license_key,
            "localLicense": {
                "boundIdentifier": local_license.bound_identifier[:16] + "..." if local_license else None,
                "identifierType": local_license.identifier_type if local_license else None,
                "walletType": local_license.wallet_type if local_license else None,
                "activatedAt": local_license.activated_at.isoformat() if local_license else None,
                "lastValidatedAt": local_license.last_validated_at.isoformat() if local_license else None,
            } if local_license else None,
            "features": [
                "access_l402_resource - Auto-pay L402 challenges",
                "pay_l402_challenge - Manual L402 payment"
            ],
            "message": "L402 features are unlocked!"
        })

    # Get fee info
    fee_sats = server_status.get("feeSats", 6000) if server_status else 6000

    return json.dumps({
        "success": True,
        "licensed": False,
        "identifier": identifier[:16] + "..." if identifier else None,
        "identifierType": license_service.identifier_type,
        "feeSats": fee_sats,
        "message": f"No active L402 license. Use unlock_l402_features to purchase one for {fee_sats} sats (one-time, valid forever).",
        "freeFeatures": [
            "pay_invoice - Pay any Lightning invoice",
            "check_wallet_balance - Check wallet balance",
            "get_payment_history - View payment history",
            "get_budget_status - View current budget limits"
        ],
        "paidFeatures": [
            "access_l402_resource - Auto-pay L402 challenges",
            "pay_l402_challenge - Manual L402 payment"
        ]
    })


