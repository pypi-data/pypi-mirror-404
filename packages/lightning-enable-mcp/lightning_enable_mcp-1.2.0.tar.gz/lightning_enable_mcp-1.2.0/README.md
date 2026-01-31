# Lightning Enable MCP Server

An MCP (Model Context Protocol) server that enables AI agents to access L402-protected APIs with automatic Lightning Network payments.

## Overview

Lightning Enable MCP provides tools for AI agents (like Claude) to:

- **Access paid APIs** - Automatically handle L402 payment challenges
- **Manage Lightning payments** - Pay invoices via Nostr Wallet Connect (NWC)
- **Control spending** - Set per-request and session budgets
- **Track payments** - View payment history and wallet balance

## Installation

### Using pip

```bash
pip install lightning-enable-mcp
```

### Using uvx (recommended for Claude Desktop)

No installation needed - uvx handles it automatically.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NWC_CONNECTION_STRING` | Yes* | - | Nostr Wallet Connect URI |
| `OPENNODE_API_KEY` | Yes* | - | OpenNode API key (alternative to NWC) |
| `OPENNODE_ENVIRONMENT` | No | production | "production" or "dev" for testnet |
| `L402_MAX_SATS_PER_REQUEST` | No | 1000 | Maximum sats per single request |
| `L402_MAX_SATS_PER_SESSION` | No | 10000 | Maximum sats for entire session |

*Either `NWC_CONNECTION_STRING` or `OPENNODE_API_KEY` is required. NWC takes precedence if both are set.

### Wallet Options

#### Option 1: OpenNode (Recommended for Testing)

Use your OpenNode account to pay invoices. Great for testing since you likely already have an OpenNode account if you're using Lightning Enable.

1. Get your API key from https://app.opennode.com (or https://app.dev.opennode.com for testnet)
2. Ensure the API key has withdrawal permissions
3. Fund your OpenNode account

```bash
export OPENNODE_API_KEY="your-api-key"
export OPENNODE_ENVIRONMENT="dev"  # Use testnet for testing
```

#### Option 2: Nostr Wallet Connect (NWC)

NWC allows this server to pay invoices using your Lightning wallet. You can get a connection string from:

1. **Alby** - https://getalby.com (Browser extension or Alby Hub)
2. **Mutiny Wallet** - https://mutinywallet.com
3. **Coinos** - https://coinos.io
4. **Any NWC-compatible wallet**

The connection string looks like:
```
nostr+walletconnect://pubkey?relay=wss://relay.example.com&secret=hexsecret
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

**Using OpenNode:**
```json
{
  "mcpServers": {
    "lightning-enable": {
      "command": "uvx",
      "args": ["lightning-enable-mcp"],
      "env": {
        "OPENNODE_API_KEY": "your-opennode-api-key",
        "OPENNODE_ENVIRONMENT": "dev"
      }
    }
  }
}
```

**Using NWC:**
```json
{
  "mcpServers": {
    "lightning-enable": {
      "command": "uvx",
      "args": ["lightning-enable-mcp"],
      "env": {
        "NWC_CONNECTION_STRING": "nostr+walletconnect://your-pubkey?relay=wss://relay.getalby.com/v1&secret=your-secret"
      }
    }
  }
}
```

Or if installed via pip, replace `"command": "uvx", "args": ["lightning-enable-mcp"]` with just `"command": "lightning-enable-mcp"`.

## Available Tools

### access_l402_resource

Fetch a URL with automatic L402 payment handling.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `url` | string | Yes | - | The URL to fetch |
| `method` | string | No | GET | HTTP method (GET, POST, PUT, DELETE) |
| `headers` | object | No | {} | Additional request headers |
| `body` | string | No | - | Request body for POST/PUT |
| `max_sats` | integer | No | 1000 | Maximum sats to pay for this request |

**Example:**
```
Use access_l402_resource to fetch https://api.example.com/premium-data
```

**Returns:** Response body text or error message

### pay_l402_challenge

Manually pay an L402 invoice and get the authorization token.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `invoice` | string | Yes | - | BOLT11 invoice string |
| `macaroon` | string | Yes | - | Base64-encoded macaroon from L402 challenge |
| `max_sats` | integer | No | 1000 | Maximum sats allowed for this payment |

**Returns:** L402 token in format `macaroon:preimage` for use in Authorization header

### check_wallet_balance

Check the connected wallet balance via NWC.

**Parameters:** None

**Returns:** Current balance in satoshis

### get_payment_history

List recent L402 payments made during this session.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Maximum number of payments to return |
| `since` | string | No | - | ISO timestamp to filter payments from |

**Returns:** List of payments with url, amount, timestamp, and status

### configure_budget

Set spending limits for the session.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `per_request` | integer | No | 1000 | Maximum sats per individual request |
| `per_session` | integer | No | 10000 | Maximum total sats for the session |

**Returns:** Confirmation of new limits

### pay_invoice

Pay a Lightning invoice directly and get the preimage as proof of payment. Use this to pay any BOLT11 Lightning invoice without L402 protocol overhead.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `invoice` | string | Yes | - | BOLT11 Lightning invoice string to pay |
| `max_sats` | integer | No | 1000 | Maximum sats allowed to pay |

**Example:**
```
Use pay_invoice to pay lnbc100n1pj9npjpp5... with max_sats 500
```

**Returns:** JSON with payment result including:
- `success`: boolean - Whether payment succeeded
- `preimage`: string - Payment preimage (proof of payment)
- `message`: string - Status message
- `invoice.paid`: string - Truncated invoice that was paid

## How L402 Works

L402 (formerly LSAT) is a protocol for API monetization using Lightning Network:

1. Client requests a resource
2. Server returns `402 Payment Required` with a `WWW-Authenticate` header containing:
   - A macaroon (authorization token)
   - A BOLT11 Lightning invoice
3. Client pays the invoice, receiving a preimage
4. Client retries the request with `Authorization: L402 <macaroon>:<preimage>`
5. Server validates and returns the resource

This MCP server handles steps 2-5 automatically when you use `access_l402_resource`.

## Security Considerations

- **Budget Limits**: Always set appropriate spending limits for your use case
- **NWC Secret**: Keep your NWC connection string secure - it allows payments from your wallet
- **Session Isolation**: Each server instance maintains its own budget and payment history
- **Invoice Verification**: The server verifies invoice amounts before paying

## Development

### Setup

```bash
git clone https://github.com/refinedelement/lightning-enable-mcp
cd lightning-enable-mcp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/lightning_enable_mcp
```

### Linting

```bash
ruff check src/
ruff format src/
```

## Architecture

```
lightning_enable_mcp/
├── server.py          # Main MCP server and tool registration
├── l402_client.py     # L402 protocol implementation
├── nwc_wallet.py      # Nostr Wallet Connect client
├── budget.py          # Spending limit management
└── tools/
    ├── access_resource.py   # access_l402_resource tool
    ├── pay_challenge.py     # pay_l402_challenge tool
    ├── wallet.py            # check_wallet_balance tool
    └── budget.py            # configure_budget, get_payment_history tools
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: https://github.com/refinedelement/lightning-enable-mcp/issues
- **Documentation**: https://lightningenable.com/docs
- **Discord**: https://discord.gg/lightningenable

## Related Projects

- [Lightning Enable](https://lightningenable.com) - Bitcoin Lightning payment API middleware
- [MCP Specification](https://modelcontextprotocol.io) - Model Context Protocol
- [NIP-47](https://github.com/nostr-protocol/nips/blob/master/47.md) - Nostr Wallet Connect
