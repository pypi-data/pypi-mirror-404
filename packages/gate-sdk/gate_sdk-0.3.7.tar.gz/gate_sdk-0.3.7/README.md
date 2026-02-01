# BlockIntel Gate Python SDK

Production-grade Python SDK for [BlockIntel Gate](https://blockintelai.com) Hot Path API.

## Installation

```bash
pip install gate-sdk
```

Or from source:

```bash
cd sdk/python
pip install -e ".[dev]"
```

## Requirements

- Python >= 3.9
- httpx >= 0.25.0

## Quick Start

### HMAC Authentication (Recommended for Production)

```python
from gate_sdk import GateClient, GateClientConfig, HmacAuth

# Initialize client with HMAC auth
gate = GateClient(GateClientConfig(
    base_url="https://gate.blockintelai.com",
    tenant_id="your-tenant-id",
    auth=HmacAuth(
        mode="hmac",
        key_id="your-key-id",
        secret="your-hmac-secret",
    ),
    enable_stepup=True,
))

# Evaluate a transaction
response = gate.evaluate({
    "txIntent": {
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": "1000000000000000000",  # 1 ETH in wei
        "data": "0x...",
        "nonce": 42,
        "gasPrice": "20000000000",
        "gasLimit": "21000",
        "chainId": 1,
    },
    "signingContext": {
        "signerId": "my-signer-id",
        "source": {
            "repo": "myorg/myrepo",
            "workflow": "deploy-production",
            "environment": "production",
        },
        "wallet": {
            "address": "0x1234...",
            "type": "hardware",
        },
    },
})

if response["decision"] == "ALLOW":
    # Proceed with transaction
    print(f"Transaction approved: {response.get('correlationId')}")
elif response["decision"] == "REQUIRE_STEP_UP":
    # Poll for step-up decision
    final = gate.await_stepup_decision(
        request_id=response["stepUp"]["requestId"]
    )

    if final["status"] == "APPROVED":
        # Proceed with transaction
        print(f"Step-up approved: {final.get('correlationId')}")
    else:
        # Block transaction
        print(f"Step-up denied or expired: {final['status']}")
else:
    # BLOCK
    print(f"Transaction blocked: {response['reasonCodes']}")
```

### API Key Authentication

```python
from gate_sdk import GateClient, GateClientConfig, ApiKeyAuth

# Initialize client with API key
gate = GateClient(GateClientConfig(
    base_url="https://gate.blockintelai.com",
    tenant_id="your-tenant-id",
    auth=ApiKeyAuth(
        mode="apiKey",
        api_key="your-api-key",
    ),
))

response = gate.evaluate({
    "txIntent": {
        "from": "0x123...",
        "to": "0x456...",
        "value": "1000000000000000000",
    },
})
```

### Local Development with Gate Local

For local development and testing, use **Gate Local** - a Docker container that emulates the Gate Hot Path:

```bash
# Start Gate Local
docker pull blockintelai/gate-local:latest
docker run -d --name gate-local -p 3000:3000 blockintelai/gate-local:latest
```

Then configure your client for local mode:

```python
from gate_sdk import GateClient, GateClientConfig, ApiKeyAuth

# Local development configuration
gate = GateClient(GateClientConfig(
    base_url="http://localhost:3000",  # Gate Local endpoint
    tenant_id="local-dev",              # Any tenant ID (ignored in local mode)
    local=True,                          # Enable local mode (disables auth/heartbeat)
    auth=ApiKeyAuth(
        mode="apiKey",
        api_key="local-dev-key"          # Any API key (ignored in local mode)
    ),
))

# Evaluate transactions locally
response = gate.evaluate({
    "txIntent": {
        "toAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "value": "1000000000000000000",  # 1 ETH in wei
        "valueUsd": 2500.0,
        "chainId": 1,
    },
})

print(f"Decision: {response['decision']}")
```

**📚 Full Local Development Guide**: See [Gate Local Quick Start Guide](https://docs.blockintelai.com/gate/local-development) for complete setup instructions, trading bot integration examples, and troubleshooting.

### Step-Up Polling

```python
# Manual polling
status = gate.get_stepup_status(request_id="stepup-request-id")
print(f"Status: {status['status']}")  # PENDING | APPROVED | DENIED | EXPIRED

# Automatic polling with timeout
result = gate.await_stepup_decision(
    request_id="stepup-request-id",
    max_wait_ms=15000,  # 15 seconds
    interval_ms=250,  # Poll every 250ms
)

print(f"Final status: {result['status']}")
print(f"Elapsed time: {result['elapsedMs']} ms")
```

**Polling behavior:**
- `404 NOT_FOUND` → request ID does not exist OR does not belong to the tenant
- `EXPIRED` → TTL exceeded (deterministic), even if DynamoDB TTL has not deleted the item yet
- `PENDING` → waiting for external approval
- `APPROVED | DENIED` → terminal states

## Configuration

### `GateClientConfig`

```python
from dataclasses import dataclass
from gate_sdk import GateClientConfig, HmacAuth, StepUpConfig

config = GateClientConfig(
    base_url="https://gate.blockintelai.com",  # Gate Hot Path API base URL
    tenant_id="your-tenant-id",                # Your tenant ID
    auth=HmacAuth(                              # Authentication
        mode="hmac",
        key_id="your-key-id",
        secret="your-secret",
    ),
    timeout_ms=15000,                          # Request timeout (default: 15000ms)
    user_agent="my-app/1.0",                   # User agent (default: blockintel-gate-sdk/0.1.0)
    clock_skew_ms=120000,                      # Clock skew tolerance (default: 120000ms)
    enable_stepup=False,                       # Enable step-up support (default: False)
    stepup=StepUpConfig(                       # Step-up configuration
        polling_interval_ms=250,               # Polling interval (default: 250ms)
        max_wait_ms=15000,                     # Max wait time (default: 15000ms)
        treat_require_stepup_as_block_when_disabled=True,  # Transform REQUIRE_STEP_UP to BLOCK (default: True)
    ),
)
```

When step-up is disabled, the SDK treats `REQUIRE_STEP_UP` as `BLOCK` by default to preserve Gate-only safety, unless the caller explicitly overrides this behavior.

gate = GateClient(config)
```

## API Reference

Responses are returned in the same JSON shape as the Gate Hot Path API (no automatic key renaming).

### `GateClient.evaluate(req, request_id=None)`

Evaluate a transaction defense request.

**Parameters:**
- `req: Dict[str, Any]` - Request dictionary with `txIntent` and optional `signingContext`
- `request_id: Optional[str]` - Optional request ID (auto-generated if not provided)

**Returns:** `DefenseEvaluateResponseV2`

**Response:**
```python
{
    "decision": "ALLOW" | "BLOCK" | "REQUIRE_STEP_UP",
    "reasonCodes": List[str],
    "policyVersion": Optional[str],
    "correlationId": Optional[str],
    "stepUp": Optional[{
        "requestId": str,
        "ttlSeconds": Optional[int],
    }],
}
```

### `GateClient.get_stepup_status(request_id, tenant_id=None)`

Get current step-up status.

**Parameters:**
- `request_id: str` - Step-up request ID
- `tenant_id: Optional[str]` - Optional tenant ID (default: from config)

**Returns:** `StepUpStatusResponse`

**Status Types:**
- `PENDING` - Waiting for decision
- `APPROVED` - Step-up approved
- `DENIED` - Step-up denied
- `EXPIRED` - Step-up expired (TTL exceeded)

**Polling behavior:**
- Returns `404 NOT_FOUND` if request ID does not exist OR does not belong to the tenant
- Returns `EXPIRED` deterministically if TTL exceeded, even if DynamoDB TTL has not deleted the item yet

### `GateClient.await_stepup_decision(request_id, max_wait_ms=None, interval_ms=None)`

Poll step-up status until decision is reached or timeout.

**Parameters:**
- `request_id: str` - Step-up request ID
- `max_wait_ms: Optional[int]` - Maximum wait time in milliseconds
- `interval_ms: Optional[int]` - Polling interval in milliseconds

**Returns:** `StepUpFinalResult`

## Error Handling

The SDK provides custom exception types:

```python
from gate_sdk import (
    GateError,
    GateNetworkError,
    GateTimeoutError,
    GateNotFoundError,
    GateAuthError,
    GateRateLimitError,
    StepUpNotConfiguredError,
)

try:
    response = gate.evaluate({...})
except GateAuthError as e:
    print(f"Auth failed: {e}")
    print(f"Status: {e.status_code}")
    print(f"Request ID: {e.request_id}")
except GateRateLimitError as e:
    print(f"Rate limited: {e.retry_after}")
except StepUpNotConfiguredError as e:
    print(f"Step-up not configured: {e}")
except GateError as e:
    print(f"Error: {e.code} - {e.message}")
```

**Error Codes:**
- `NETWORK_ERROR` - Network connection failed
- `TIMEOUT` - Request timeout
- `NOT_FOUND` - Resource not found (404)
- `UNAUTHORIZED` - Authentication failed (401)
- `FORBIDDEN` - Access denied (403)
- `RATE_LIMITED` - Rate limit exceeded (429)
- `SERVER_ERROR` - Server error (5xx)
- `INVALID_RESPONSE` - Invalid response format
- `STEP_UP_NOT_CONFIGURED` - Step-up required but not enabled
- `STEP_UP_TIMEOUT` - Step-up polling timeout
- `HEARTBEAT_MISSING` - Heartbeat token is missing or expired
- `HEARTBEAT_EXPIRED` - Heartbeat token has expired
- `HEARTBEAT_INVALID` - Heartbeat token is invalid
- `HEARTBEAT_MISMATCH` - Heartbeat token does not match expected parameters

## Authentication

### HMAC v1 Signing

The SDK implements HMAC v1 signing for secure authentication:

**Signing String:**
```
v1\n
<HTTP_METHOD>\n
<PATH>\n
<TENANT_ID>\n
<KEY_ID>\n
<TIMESTAMP_MS>\n
<REQUEST_ID>\n
<SHA256_HEX_OF_BODY>\n
```

**Signature:**
```
HMAC-SHA256(secret, signingString) as hex
```

**Headers:**
- `X-GATE-TENANT-ID`
- `X-GATE-KEY-ID`
- `X-GATE-TIMESTAMP-MS`
- `X-GATE-REQUEST-ID`
- `X-GATE-SIGNATURE`

### API Key

For simpler onboarding, use API key authentication:

**Headers:**
- `X-API-KEY`
- `X-GATE-TENANT-ID`
- `X-GATE-REQUEST-ID`
- `X-GATE-TIMESTAMP-MS`

## Step-Up Flow

Step-up is a feature-flagged capability that allows Gate to defer decisions to an external approval system.

**Flow:**
1. SDK calls `evaluate()` → Gate returns `REQUIRE_STEP_UP`
2. SDK polls `/defense/stepup/status` until decision is reached
3. External system (Control Plane) approves/denies via separate API
4. SDK receives final decision: `APPROVED`, `DENIED`, or `EXPIRED`

**Important:**
- Hot Path **never** approves/denies step-up
- Approve/deny happens **only** on Control Plane
- SDK only polls status from Hot Path
- **The SDK never performs approve/deny actions. Step-up resolution is handled exclusively by the Control Plane.**

Gate-only deployments should leave step-up disabled; the SDK will never "wait" unless step-up is enabled.

**TTL Guardrails:**
- Default: 600 seconds
- Min: 300 seconds
- Max: 900 seconds

## Retry Logic

The SDK automatically retries failed requests:

- **Max Attempts:** 3
- **Retry On:** Network errors, timeouts, 429, 5xx
- **Never Retry On:** 4xx (except 429)
- **Backoff:** Exponential with jitter (100ms base, 2x factor, 800ms max)

**Request ID Stability:**
- Same `request_id` is used across all retries
- Ensures idempotency on Gate server

## Degraded Mode / X-BlockIntel-Degraded

When the SDK is in a degraded situation, it logs `X-BlockIntel-Degraded: true` with a `reason` for **logs and telemetry only**. This is **never sent as an HTTP request header** to the Gate server.

**Reasons:** `retry`, `429`, `fail_open`, `fail_safe_allow`.

**Example (one line):**  
`[GATE SDK] X-BlockIntel-Degraded: true (reason=retry) attempt=1/3 status=503 exc=GateServerError requestId=abc-123`

**How to observe:**
- **Logs:** `[GATE SDK] X-BlockIntel-Degraded: true (reason: <reason>)` at `WARNING` level. Ensure `logging` captures `gate_sdk` (e.g. `logging.getLogger('gate_sdk')` or root).
- **Metrics:** Use `on_metrics`; metrics include `timeouts`, `errors`, `failOpen` etc. Correlate with log lines if you ship both.

**Manual check (retry):** Point the SDK at an endpoint that returns 5xx; confirm one degraded log per retry attempt including `attempt`, `max`, and `status`/`exc`.

## Heartbeat System

The SDK includes a **Heartbeat Manager** that automatically acquires and refreshes heartbeat tokens from the Gate Control Plane. Heartbeat tokens are required for all signing operations and ensure that Gate is alive and enforcing policy.

### How It Works

1. **Automatic Token Acquisition**: The SDK automatically starts a background heartbeat refresher when the `GateClient` is initialized. This continuously sends heartbeats to the Control Plane, keeping the signer status active in the UI.
2. **Token Refresh**: Heartbeat tokens are refreshed every 10 seconds (configurable via `heartbeat_refresh_interval_seconds`) to maintain a valid token
3. **Signing Enforcement**: Before any `evaluate()` call, the SDK checks for a valid heartbeat token. If missing or expired, it throws `HEARTBEAT_MISSING` error
4. **Token Inclusion**: The heartbeat token is automatically included in the `signingContext` of every evaluation request
5. **No Manual Scripts Needed**: The SDK handles all heartbeat management automatically - no need for separate heartbeat scripts

### Configuration

The heartbeat manager is automatically configured based on your `GateClientConfig`:

```python
gate = GateClient(GateClientConfig(
    base_url="https://gate.blockintelai.com",  # Hot Path URL
    tenant_id="your-tenant-id",
    auth=HmacAuth(...),
    # Heartbeat manager uses base_url to infer Control Plane URL
    # Or explicitly set control_plane_url if different
    control_plane_url="https://control-plane.blockintelai.com",  # Optional
    signer_id="my-signer-id",  # Optional: signerId for heartbeat (if known upfront)
    heartbeat_refresh_interval_seconds=10,  # Optional: heartbeat refresh interval (default: 10s)
))
```

### Heartbeat Token Properties

- **TTL**: 15-30 seconds (short-lived for security)
- **Scope**: Scoped to `tenantId`, `signerId`, `environment`, and `policyVersion`
- **Validation**: Hot Path validates heartbeat tokens before processing any transaction
- **Enforcement**: "No valid heartbeat → NO SIGNATURE" - transactions are blocked if heartbeat is missing or expired

### Error Handling

```python
from gate_sdk import GateError, GateErrorCode

try:
    response = gate.evaluate({...})
except GateError as e:
    if e.code == GateErrorCode.HEARTBEAT_MISSING:
        print("Heartbeat token missing - Gate may be down or unreachable")
    elif e.code == GateErrorCode.HEARTBEAT_EXPIRED:
        print("Heartbeat token expired - will retry automatically")
```

### Heartbeat Manager API

The heartbeat manager is internal to the SDK, but you can access it if needed:

```python
# Check if heartbeat is valid
is_valid = gate._heartbeat_manager.is_valid()

# Get current heartbeat token (if valid)
token = gate._heartbeat_manager.get_token()

# Update signer ID (called automatically when signer is known)
gate._heartbeat_manager.update_signer_id("new-signer-id")

# Stop heartbeat refresher (e.g., on shutdown)
gate._heartbeat_manager.stop()
```

**Note**: The heartbeat manager automatically updates the `signerId` when using the KMS wrapper, so manual updates are typically not needed.

## KMS Wrapper

The SDK provides a KMS wrapper that automatically intercepts boto3 KMS signing operations and enforces Gate policies. This allows you to protect your KMS keys without modifying your existing code.

### Basic Usage

```python
from gate_sdk import (
    GateClient,
    GateClientConfig,
    HmacAuth,
    wrap_kms_client,
    BlockIntelBlockedError,
    BlockIntelStepUpRequiredError,
)
import boto3

# Initialize Gate client
gate = GateClient(GateClientConfig(
    base_url="https://gate.blockintelai.com",
    tenant_id="your-tenant-id",
    auth=HmacAuth(
        mode="hmac",
        key_id="your-key-id",
        secret="your-hmac-secret",
    ),
))

# Initialize boto3 KMS client
kms = boto3.client('kms', region_name='us-east-1')

# Wrap KMS client with Gate protection
protected_kms = wrap_kms_client(kms, gate, {
    'mode': 'enforce',  # 'enforce' or 'dry-run'
    'extract_tx_intent': lambda **kwargs: {
        'toAddress': '0x...',  # Extract from message if possible
        'networkFamily': 'EVM',
        'chainId': 1,
    },
    'on_decision': lambda decision, details: print(f'Gate decision: {decision}', details),
})

# Use wrapped KMS client - Gate will intercept automatically
try:
    response = protected_kms.sign(
        KeyId='alias/my-key',
        Message=b'transaction-data',
        MessageType='RAW',
        SigningAlgorithm='ECDSA_SHA_256',
    )
    print('Signature:', response['Signature'])
except BlockIntelBlockedError as e:
    print(f'Transaction blocked by Gate: {e.message}')
except BlockIntelStepUpRequiredError as e:
    print(f'Step-up required: {e.request_id}')
    # Handle step-up flow
```

### Wrapper Modes

- **`enforce`** (default): Gate policies are enforced. Transactions are blocked if Gate denies.
- **`dry-run`**: Gate evaluates transactions but always allows KMS calls. Useful for testing and monitoring.

### Automatic Signer ID Detection

The KMS wrapper automatically extracts the signer ID from the KMS `KeyId` and updates the heartbeat manager. This ensures that heartbeats are sent with the correct signer ID.

### Advanced Configuration

```python
from gate_sdk.kms import WrapKmsClientOptions

options = WrapKmsClientOptions(
    mode='enforce',
    extract_tx_intent=lambda **kwargs: {
        # Custom extraction logic
        'toAddress': extract_address_from_message(kwargs.get('Message')),
        'networkFamily': 'EVM',
        'chainId': 1,
    },
    on_decision=lambda decision, details: log_decision(decision, details),
)

protected_kms = wrap_kms_client(kms, gate, options)
```

## Security

- **HTTPS Required:** SDK validates HTTPS in production (localhost exception)
- **Secret Protection:** Never logs secrets or API keys
- **Clock Skew:** Configurable tolerance for timestamp validation
- **Replay Protection:** Request ID + timestamp prevent replay attacks
- **Heartbeat Enforcement:** All signing operations require valid heartbeat tokens

## Testing

Run the test suite:

```bash
cd sdk/python
pytest -v
```

Run with coverage:

```bash
pytest --cov=gate_sdk --cov-report=term-missing
```

## Building

Build the package:

```bash
cd sdk/python
python -m build
```

This creates:
- `dist/blockintel_gate_sdk-*.whl` (wheel)
- `dist/blockintel-gate-sdk-*.tar.gz` (source distribution)

## Publishing

- Package versions are immutable once published (PyPI does not allow overwriting a released version). Always bump the version before tagging a release.

See [PUBLISHING.md](./PUBLISHING.md) for detailed publishing instructions.

**Quick steps:**
1. Update version in `pyproject.toml`
2. Create GitHub release tag
3. GitHub Actions publishes to PyPI automatically

## License

MIT License - see [LICENSE](./LICENSE) file.

## Support

- **Documentation:** https://docs.blockintelai.com
- **Issues:** https://github.com/4KInc/blockintel-ai/issues
- **Email:** support@blockintelai.com

## Keywords

blockintel, gate, sdk, defense, crypto, security
