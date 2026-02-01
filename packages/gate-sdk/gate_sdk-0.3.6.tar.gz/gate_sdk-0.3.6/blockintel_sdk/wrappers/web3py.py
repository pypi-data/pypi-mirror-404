"""
Web3.py Wrapper for BlockIntel Gate

Provides drop-in wrappers for web3.py transaction signing/sending.
"""

from typing import Dict, Any, Optional, Callable
from web3 import Web3
from web3.types import TxParams, HexStr

from ..client import BlockIntelGateClient
from ..exceptions import BlockIntelGateDecisionError


def guarded_send_transaction(
    web3: Web3,
    tx_dict: Dict[str, Any],
    *,
    gate_client: BlockIntelGateClient,
    signing_context: Dict[str, Any],
    request_id: Optional[str] = None,
) -> HexStr:
    """
    Send a transaction through Gate evaluation before signing and broadcasting.

    This function:
    1. Evaluates the transaction with BlockIntel Gate
    2. If ALLOW: signs and sends the transaction via web3
    3. If BLOCK: raises BlockIntelGateDecisionError

    Args:
        web3: Web3 instance (must have account configured via web3.eth.account or middleware)
        tx_dict: Transaction parameters (to, value, data, gas, etc.)
        gate_client: BlockIntelGateClient instance
        signing_context: Signing context for Gate evaluation
        request_id: Optional request ID (for idempotency)

    Returns:
        Transaction hash (HexStr)

    Raises:
        BlockIntelGateDecisionError: If Gate blocks the transaction
        ValueError: If transaction parameters are invalid
    """
    # Extract transaction intent from tx_dict
    chain_id = web3.eth.chain_id
    to_address = tx_dict.get('to')
    value = tx_dict.get('value', 0)
    data = tx_dict.get('data', b'')
    gas_limit = tx_dict.get('gas')
    max_fee_per_gas = tx_dict.get('maxFeePerGas')
    max_priority_fee_per_gas = tx_dict.get('maxPriorityFeePerGas')
    nonce = tx_dict.get('nonce')

    # Build transaction intent
    tx_intent: Dict[str, Any] = {
        'chainId': str(chain_id),
        'toAddress': to_address,
        'value': str(value) if isinstance(value, (int, str)) else str(Web3.to_wei(value, 'ether')) if value else '0',
    }

    if data:
        if isinstance(data, bytes):
            tx_intent['dataHash'] = Web3.keccak(data).hex()
        else:
            tx_intent['dataHash'] = Web3.keccak(hexstr=data).hex() if isinstance(data, str) else None

    if gas_limit:
        tx_intent['gasLimit'] = str(gas_limit)

    if max_fee_per_gas:
        tx_intent['maxFeePerGas'] = str(max_fee_per_gas)

    if max_priority_fee_per_gas:
        tx_intent['maxPriorityFeePerGas'] = str(max_priority_fee_per_gas)

    if nonce is not None:
        tx_intent['nonce'] = nonce

    # Evaluate with Gate
    try:
        decision = gate_client.evaluate(
            signing_context=signing_context,
            tx_intent=tx_intent,
            request_id=request_id,
        )
    except BlockIntelGateDecisionError as e:
        # Gate blocked the transaction
        raise e

    # If ALLOW, proceed with transaction
    if decision.get('decision') == 'ALLOW':
        # Sign and send transaction
        tx_hash = web3.eth.send_transaction(tx_dict)
        return tx_hash
    else:
        # Should not happen (evaluate raises BlockIntelGateDecisionError on BLOCK)
        raise BlockIntelGateDecisionError(
            f"Transaction blocked by Gate: {decision.get('reasonCodes', [])}",
            decision=decision.get('decision'),
            reason_codes=decision.get('reasonCodes', []),
        )


def guarded_sign_transaction(
    web3: Web3,
    tx_dict: Dict[str, Any],
    *,
    gate_client: BlockIntelGateClient,
    signing_context: Dict[str, Any],
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sign a transaction through Gate evaluation (returns signed transaction, does not broadcast).

    This function:
    1. Evaluates the transaction with BlockIntel Gate
    2. If ALLOW: signs the transaction via web3 (returns signed tx)
    3. If BLOCK: raises BlockIntelGateDecisionError

    Args:
        web3: Web3 instance (must have account configured)
        tx_dict: Transaction parameters
        gate_client: BlockIntelGateClient instance
        signing_context: Signing context for Gate evaluation
        request_id: Optional request ID (for idempotency)

    Returns:
        Signed transaction dictionary

    Raises:
        BlockIntelGateDecisionError: If Gate blocks the transaction
        ValueError: If transaction parameters are invalid
    """
    # Extract transaction intent from tx_dict
    chain_id = web3.eth.chain_id
    to_address = tx_dict.get('to')
    value = tx_dict.get('value', 0)
    data = tx_dict.get('data', b'')
    gas_limit = tx_dict.get('gas')
    max_fee_per_gas = tx_dict.get('maxFeePerGas')

    # Build transaction intent
    tx_intent: Dict[str, Any] = {
        'chainId': str(chain_id),
        'toAddress': to_address,
        'value': str(value) if isinstance(value, (int, str)) else str(Web3.to_wei(value, 'ether')) if value else '0',
    }

    if data:
        if isinstance(data, bytes):
            tx_intent['dataHash'] = Web3.keccak(data).hex()
        else:
            tx_intent['dataHash'] = Web3.keccak(hexstr=data).hex() if isinstance(data, str) else None

    if gas_limit:
        tx_intent['gasLimit'] = str(gas_limit)

    if max_fee_per_gas:
        tx_intent['maxFeePerGas'] = str(max_fee_per_gas)

    # Evaluate with Gate
    try:
        decision = gate_client.evaluate(
            signing_context=signing_context,
            tx_intent=tx_intent,
            request_id=request_id,
        )
    except BlockIntelGateDecisionError as e:
        # Gate blocked the transaction
        raise e

    # If ALLOW, proceed with signing
    if decision.get('decision') == 'ALLOW':
        # Sign transaction (web3.eth.account.sign_transaction)
        # Note: This requires account to be available (web3.eth.default_account or account middleware)
        signed_tx = web3.eth.account.sign_transaction(tx_dict)
        return {
            'rawTransaction': signed_tx.rawTransaction.hex(),
            'hash': signed_tx.hash.hex(),
            'r': signed_tx.r,
            's': signed_tx.s,
            'v': signed_tx.v,
        }
    else:
        # Should not happen
        raise BlockIntelGateDecisionError(
            f"Transaction blocked by Gate: {decision.get('reasonCodes', [])}",
            decision=decision.get('decision'),
            reason_codes=decision.get('reasonCodes', []),
        )

