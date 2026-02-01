"""
AgentGuard Guarded Clients

Drop-in replacements for AI provider clients with integrated security and cost tracking.
"""

from .guarded_openai import (
    GuardedOpenAI,
    GuardedOpenAIConfig,
    ChatCompletionMessage,
    ChatCompletionRequest,
    SecurityMetadata,
    ChatCompletionResponse,
)

from .guarded_anthropic import (
    GuardedAnthropic,
    GuardedAnthropicConfig,
    MessageCreateRequest,
    MessageCreateResponse,
)

from .guarded_azure_openai import (
    GuardedAzureOpenAI,
    GuardedAzureOpenAIConfig,
    AzureChatCompletionMessage,
    AzureChatCompletionRequest,
    AzureChatCompletionResponse,
)

__all__ = [
    'GuardedOpenAI',
    'GuardedOpenAIConfig',
    'ChatCompletionMessage',
    'ChatCompletionRequest',
    'SecurityMetadata',
    'ChatCompletionResponse',
    'GuardedAnthropic',
    'GuardedAnthropicConfig',
    'MessageCreateRequest',
    'MessageCreateResponse',
    'GuardedAzureOpenAI',
    'GuardedAzureOpenAIConfig',
    'AzureChatCompletionMessage',
    'AzureChatCompletionRequest',
    'AzureChatCompletionResponse',
]
