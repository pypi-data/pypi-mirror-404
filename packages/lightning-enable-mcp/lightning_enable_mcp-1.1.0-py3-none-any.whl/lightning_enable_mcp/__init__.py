"""
Lightning Enable MCP Server

An MCP server for L402 Lightning payments that enables AI agents
to access paid APIs with automatic payment handling.

FREE TIER (no license required):
- pay_invoice - Pay any Lightning invoice
- check_wallet_balance - Check wallet balance
- get_payment_history - View payment history
- get_budget_status - View current budget limits

PAID TIER (requires L402 license - one-time 6,000 sats):
- access_l402_resource - Auto-pay L402 challenges
- pay_l402_challenge - Manual L402 payment
"""

__version__ = "1.1.0"

from .budget import BudgetManager, BudgetExceededError, PaymentRecord
from .l402_client import L402Client, L402Error, L402Challenge, L402Token
from .license import LicenseService, LocalLicense
from .nwc_wallet import NWCWallet, NWCError, NWCConfig
from .server import LightningEnableServer, main

__all__ = [
    # Server
    "LightningEnableServer",
    "main",
    # L402 Client
    "L402Client",
    "L402Error",
    "L402Challenge",
    "L402Token",
    # NWC Wallet
    "NWCWallet",
    "NWCError",
    "NWCConfig",
    # Budget
    "BudgetManager",
    "BudgetExceededError",
    "PaymentRecord",
    # License
    "LicenseService",
    "LocalLicense",
    # Version
    "__version__",
]
