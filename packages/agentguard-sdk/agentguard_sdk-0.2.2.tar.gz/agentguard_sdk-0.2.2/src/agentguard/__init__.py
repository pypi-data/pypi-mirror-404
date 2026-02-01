"""AgentGuard Python SDK - Enterprise-grade security for AI agents."""

from agentguard.client import AgentGuard
from agentguard.policy import PolicyBuilder, PolicyTester
from agentguard.types import ExecutionResult, SecurityDecision
from agentguard.guardrails import (
    Guardrail,
    GuardrailResult,
    GuardrailEngine,
    GuardrailEngineResult,
    PIIDetectionGuardrail,
    ContentModerationGuardrail,
    PromptInjectionGuardrail,
)

# Cost tracking and budget management
from agentguard.cost import (
    # Types
    ModelProvider,
    BudgetPeriod,
    BudgetAction,
    AlertSeverity,
    ModelPricing,
    TokenUsage,
    CostBreakdown,
    CostEstimate,
    CostRecord,
    BudgetScope,
    BudgetConfig,
    BudgetStatus,
    CostAlert,
    CostSummary,
    # Pricing
    MODEL_PRICING,
    get_model_pricing,
    get_provider_models,
    is_model_supported,
    get_supported_models,
    get_supported_providers,
    # Tracker
    CostTracker,
    CostTrackerConfig,
)

# Storage and budget management
from agentguard.cost.storage import CostStorage, InMemoryCostStorage
from agentguard.cost.budget import BudgetManager

# Guarded AI clients
from agentguard.clients import (
    GuardedOpenAI,
    GuardedOpenAIConfig,
    GuardedAnthropic,
    GuardedAnthropicConfig,
    GuardedAzureOpenAI,
    GuardedAzureOpenAIConfig,
)

__version__ = "0.2.2"
__all__ = [
    # Core client
    "AgentGuard",
    "PolicyBuilder",
    "PolicyTester",
    "ExecutionResult",
    "SecurityDecision",
    # Guardrails
    "Guardrail",
    "GuardrailResult",
    "GuardrailEngine",
    "GuardrailEngineResult",
    "PIIDetectionGuardrail",
    "ContentModerationGuardrail",
    "PromptInjectionGuardrail",
    # Cost tracking types
    "ModelProvider",
    "BudgetPeriod",
    "BudgetAction",
    "AlertSeverity",
    "ModelPricing",
    "TokenUsage",
    "CostBreakdown",
    "CostEstimate",
    "CostRecord",
    "BudgetScope",
    "BudgetConfig",
    "BudgetStatus",
    "CostAlert",
    "CostSummary",
    # Pricing functions
    "MODEL_PRICING",
    "get_model_pricing",
    "get_provider_models",
    "is_model_supported",
    "get_supported_models",
    "get_supported_providers",
    # Cost tracking
    "CostTracker",
    "CostTrackerConfig",
    "CostStorage",
    "InMemoryCostStorage",
    # Budget management
    "BudgetManager",
    # Guarded clients
    "GuardedOpenAI",
    "GuardedOpenAIConfig",
    "GuardedAnthropic",
    "GuardedAnthropicConfig",
    "GuardedAzureOpenAI",
    "GuardedAzureOpenAIConfig",
]
