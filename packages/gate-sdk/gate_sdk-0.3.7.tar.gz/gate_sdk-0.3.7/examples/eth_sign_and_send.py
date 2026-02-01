"""
Example: Ethereum Transaction Signing with BlockIntel Gate

This example shows how to use BlockIntel Gate SDK to evaluate,
sign, and send Ethereum transactions.
"""

import os
from blockintel_sdk import BlockIntelGateClient, BlockIntelGateDecisionError

# Configuration
API_BASE_URL = os.getenv("BLOCKINTEL_API_URL", "https://api.blockintelai.com")
TENANT_ID = os.getenv("BLOCKINTEL_TENANT_ID", "your-tenant-id")
API_KEY = os.getenv("BLOCKINTEL_API_KEY", "your-api-key")

# Initialize client
client = BlockIntelGateClient(
    api_base_url=API_BASE_URL,
    tenant_id=TENANT_ID,
    api_key=API_KEY,
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
    # Example transaction intent
    tx_intent = {
        "chainId": "ETH",
        "toAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "value": "1.0",  # 1 ETH
        "gasLimit": "21000",
        "maxFeePerGas": "20000000000",  # 20 gwei
    }

    # Example signing context (GitHub Actions)
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

