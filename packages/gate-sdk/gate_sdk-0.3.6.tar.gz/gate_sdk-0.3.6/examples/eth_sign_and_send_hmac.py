"""
Example: Ethereum Transaction Signing with BlockIntel Gate (HMAC v1)

This example shows how to use BlockIntel Gate SDK with HMAC v1 authentication
to evaluate, sign, and send Ethereum transactions.
"""

import os
from blockintel_sdk import BlockIntelGateClient, BlockIntelGateDecisionError
from blockintel_sdk.auth_hmac import HmacAuthProvider

# Configuration
API_BASE_URL = os.getenv("BLOCKINTEL_API_URL", "https://api.blockintelai.com")
TENANT_ID = os.getenv("BLOCKINTEL_TENANT_ID", "your-tenant-id")
KEY_ID = os.getenv("BLOCKINTEL_KEY_ID", "key-1")  # Key ID for key rotation
HMAC_SECRET = os.getenv("BLOCKINTEL_HMAC_SECRET", "your-hmac-secret")

# Initialize HMAC v1 auth provider
auth_provider = HmacAuthProvider(
    tenant_id=TENANT_ID,
    key_id=KEY_ID,
    hmac_secret=HMAC_SECRET,
    allowed_clock_skew_ms=120000  # 2 minutes
)

# Initialize client with HMAC auth
client = BlockIntelGateClient(
    api_base_url=API_BASE_URL,
    tenant_id=TENANT_ID,
    auth_provider=auth_provider,  # Use HMAC provider instead of API key
)


def sign_transaction(tx_intent: dict) -> dict:
    """
    Sign a transaction (mock implementation).

    In production, this would use your signing mechanism (AWS KMS, hardware wallet, etc.)
    """
    print(f"Signing transaction: {tx_intent}")
    # Mock signed transaction
    return {
        "signed": True,
        "rawTransaction": "0x...",
        "txHash": "0x...",
    }


def send_transaction(signed_tx: dict) -> str:
    """
    Send a signed transaction (mock implementation).

    In production, this would broadcast to the blockchain.
    """
    print(f"Sending transaction: {signed_tx}")
    return signed_tx.get("txHash", "0x...")


def main():
    # Example transaction intent (v2 format with networkFamily and atomic values)
    tx_intent = {
        "networkFamily": "EVM",
        "chainId": 1,  # Ethereum mainnet
        "chain": "ETHEREUM",
        "toAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "valueAtomic": "1000000000000000000",  # 1 ETH in wei
        "assetSymbol": "ETH",
        "valueDecimal": "1.0",  # Display only
        "gasLimit": "21000",
        "maxFeePerGas": "20000000000",  # 20 gwei
        "intentType": "TX",
    }

    # Example signing context
    signing_context = {
        "actorPrincipal": "arn:aws:iam::123456789012:role/DeploymentRole",
        "signerId": "alias/production-signing-key",
        "sourceIp": "10.0.0.1",
        "region": "us-east-1",
        "github": {
            "repository": "myorg/myrepo",
            "workflow": "deploy",
            "job": "deploy-production",
            "runId": "123456789",
        },
        "environment": "prod",
    }

    try:
        # Method 1: Evaluate first, then sign/send manually
        print("=== Method 1: Evaluate then sign/send ===")
        decision = client.evaluate(signing_context, tx_intent)
        print(f"Decision: {decision['decision']}")
        print(f"Policy Version: {decision['policyVersion']}")

        if decision["decision"] == "ALLOW":
            signed_tx = sign_transaction(tx_intent)
            tx_hash = send_transaction(signed_tx)
            print(f"Transaction sent: {tx_hash}")
        elif decision["decision"] == "REQUIRE_STEP_UP":
            step_up = decision.get("stepUp")
            if step_up:
                print(f"Step-up required: {step_up['stepUpId']}")
                print(f"Approval URL: {step_up.get('approvalUrl', 'N/A')}")
                # In production, you would poll for approval or redirect user
                # client.wait_for_stepup_approval(step_up['stepUpId'])

        # Method 2: Use guarded_sign_and_send (convenience method)
        print("\n=== Method 2: guarded_sign_and_send ===")
        tx_hash = client.guarded_sign_and_send(
            signing_context,
            tx_intent,
            sign_fn=sign_transaction,
            send_fn=send_transaction,
        )
        print(f"Transaction sent: {tx_hash}")

    except BlockIntelGateDecisionError as e:
        print(f"Transaction blocked: {e}")
        print(f"Reason codes: {e.decision_data.get('reasonCodes', [])}")
        # Handle blocked transaction (log, alert, etc.)
    except Exception as e:
        print(f"Error: {e}")
        # Handle error


if __name__ == "__main__":
    main()






