"""
Pydantic Models for Structured Outputs
Defines the cognitive architecture for agent thinking
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ScamType(str, Enum):
    """Types of scams the agent can detect."""
    BANK_FRAUD = "bank_fraud"
    UPI_FRAUD = "upi_fraud"
    DIGITAL_ARREST = "digital_arrest"
    KYC_FRAUD = "kyc_fraud"
    QR_SCAM = "qr_scam"
    LOTTERY_SCAM = "lottery_scam"
    LOAN_SCAM = "loan_scam"
    INVESTMENT_SCAM = "investment_scam"
    COURIER_SCAM = "courier_scam"
    OLX_SCAM = "marketplace_scam"
    AADHAAR_SCAM = "aadhaar_scam"
    UNKNOWN = "unknown"


class Strategy(str, Enum):
    """Counter-strategies the agent can use."""
    FEIGNING_IGNORANCE = "feigning_ignorance"
    TECHNICAL_CONFUSION = "technical_confusion"
    STALLING = "stalling"
    BAITING = "baiting"
    PANIC_MODE = "panic_mode"
    REVERSE_EXTRACTION = "reverse_extraction"


class ExtractedIntelligence(BaseModel):
    """Intelligence extracted from scammer's messages."""
    bank_accounts: List[str] = Field(
        default_factory=list,
        description="Extracted bank account numbers from scammer"
    )
    upi_ids: List[str] = Field(
        default_factory=list,
        description="Extracted UPI IDs (e.g., scammer@ybl)"
    )
    emails: List[str] = Field(
        default_factory=list,
        description="Extracted emails"
    )
    emailAddresses: List[str] = Field(
        default_factory=list,
        description="Extracted email addresses (GUVI scoring field)"
    )
    phishing_links: List[str] = Field(
        default_factory=list,
        description="Malicious links sent by scammer"
    )
    phone_numbers: List[str] = Field(
        default_factory=list,
        description="Extracted phone numbers"
    )
    ifsc_codes: List[str] = Field(
        default_factory=list,
        description="Extracted IFSC codes"
    )
    suspicious_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords indicating scam (OTP, block, verify, urgent)"
    )
    
    def has_actionable_intel(self) -> bool:
        """Check if we have extracted any actionable intelligence."""
        return bool(
            self.bank_accounts or 
            self.upi_ids or 
            self.phishing_links or
            self.ifsc_codes
        )
    
    def to_guvi_format(self) -> dict:
        """Convert to GUVI expected format."""
        return {
            "bankAccounts": self.bank_accounts,
            "upiIds": self.upi_ids,
            "emails": self.emails,
            "emailAddresses": self.emails,
            "phishingLinks": self.phishing_links,
            "phoneNumbers": self.phone_numbers,
            "ifscCodes": self.ifsc_codes,
            "suspiciousKeywords": self.suspicious_keywords
        }


class AgentThought(BaseModel):
    """
    The cognitive output of the agent.
    Agent THINKS first, then SPEAKS.
    """
    # Analysis
    scam_detected: bool = Field(
        ...,
        description="True if the message is definitely from a scammer"
    )
    scam_type: ScamType = Field(
        default=ScamType.UNKNOWN,
        description="Type of scam detected"
    )
    scammer_tactic: str = Field(
        default="",
        description="Current tactic used by scammer (urgency, fear, greed)"
    )
    
    # Strategy
    current_strategy: Strategy = Field(
        ...,
        description="Counter-strategy to use in response"
    )
    strategy_reasoning: str = Field(
        default="",
        description="Why this strategy was chosen"
    )
    
    # Intelligence
    intelligence: ExtractedIntelligence = Field(
        default_factory=ExtractedIntelligence,
        description="Extracted intelligence from scammer's messages"
    )
    
    # State
    is_conversation_complete: bool = Field(
        default=False,
        description="True if we've extracted bank/UPI or scammer gave up"
    )
    agent_notes: str = Field(
        default="",
        description="Internal notes about the conversation"
    )
    
    # Response
    response: str = Field(
        ...,
        description="The message to send back to the scammer"
    )


class SessionData(BaseModel):
    """Data stored for each session."""
    session_id: str
    persona: dict
    message_count: int = 0
    scam_detected: bool = False
    scam_type: Optional[ScamType] = None
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    callback_sent: bool = False
    created_at: Optional[str] = None
    last_activity: Optional[str] = None


class APIRequest(BaseModel):
    """Incoming API request from GUVI."""
    sessionId: str = Field(..., description="Unique session identifier")
    message: dict = Field(..., description="Current message object")
    conversationHistory: List[dict] = Field(
        default_factory=list,
        description="Previous messages in conversation"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata (channel, language, locale)"
    )


class APIResponse(BaseModel):
    """Response format for GUVI."""
    status: str = "success"
    scamDetected: bool = False
    engagementMetrics: dict = Field(default_factory=dict)
    extractedIntelligence: dict = Field(default_factory=dict)
    agentNotes: str = ""
    reply: str = ""
