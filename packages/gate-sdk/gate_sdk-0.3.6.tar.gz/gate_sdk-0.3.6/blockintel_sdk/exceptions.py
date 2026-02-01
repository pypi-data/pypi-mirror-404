"""
BlockIntel Gate SDK Exceptions
"""


class BlockIntelGateError(Exception):
    """Base exception for BlockIntel Gate SDK errors"""

    pass


class BlockIntelGateAuthError(BlockIntelGateError):
    """Authentication error"""

    pass


class BlockIntelGateDecisionError(BlockIntelGateError):
    """Decision error (transaction blocked or requires step-up)"""

    def __init__(self, message: str, decision_data: dict = None):
        super().__init__(message)
        self.decision_data = decision_data

