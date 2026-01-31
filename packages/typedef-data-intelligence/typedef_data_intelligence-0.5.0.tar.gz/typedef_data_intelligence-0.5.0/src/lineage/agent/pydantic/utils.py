"""Utility helpers for configuring agents and updating preview state."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from anthropic.types.beta import BetaThinkingConfigEnabledParam
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.openai import (
    OpenAIResponsesModel,
    OpenAIResponsesModelSettings,
)
from pydantic_ai.providers.bedrock import BedrockProvider

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from lineage.agent.pydantic.types import AgentState

logger = logging.getLogger(__name__)


def _create_bedrock_provider(region: str) -> BedrockProvider:
    """Create a Bedrock provider for the given region.

    Uses boto3's default credential chain which supports:
    - AWS_PROFILE environment variable (named profile)
    - IAM role credentials (when running on AWS infrastructure with a service account)

    Args:
        region: AWS region for the Bedrock service.

    Returns:
        Configured BedrockProvider instance.

    Raises:
        RuntimeError: If credentials are not found or Bedrock access is denied.
    """
    auth_method = "AWS_PROFILE" if os.environ.get("AWS_PROFILE") else "IAM role"
    logger.info(f"Creating Bedrock provider in {region} using {auth_method} credentials")

    try:
        provider = BedrockProvider(region_name=region)
        logger.info(f"Bedrock provider created successfully in {region}")
        return provider
    except NoCredentialsError as e:
        logger.error(
            f"No AWS credentials found for Bedrock in {region}. "
            f"Set AWS_PROFILE environment variable or ensure IAM role is attached to the service account. "
            f"Error: {e}"
        )
        raise RuntimeError(
            "AWS credentials not found. Set AWS_PROFILE or configure IAM role for the service account."
        ) from e
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(
            f"AWS Bedrock access denied in {region}. "
            f"Ensure the IAM role/profile has bedrock:InvokeModel permission. "
            f"Error code: {error_code}, Message: {error_message}"
        )
        raise RuntimeError(
            f"Bedrock access denied ({error_code}): {error_message}. "
            f"Check IAM permissions for bedrock:InvokeModel."
        ) from e
    except BotoCoreError as e:
        logger.error(f"Failed to create Bedrock provider in {region}: {e}")
        raise RuntimeError(f"Bedrock provider creation failed: {e}") from e


def _create_bedrock_model(model_spec: str) -> BedrockConverseModel:
    """Create a Bedrock model from a model specification.

    Args:
        model_spec: Model specification after 'bedrock:' prefix.
            Expected format: inference profile ARN
            Example:
                - arn:aws:bedrock:us-west-2:025066247024:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0

            Legacy formats (may not work with newer models):
                - anthropic.claude-3-sonnet-20240229-v1:0
                - us-west-2/anthropic.claude-3-sonnet-20240229-v1:0

    Returns:
        Configured BedrockConverseModel instance.

    Note:
        AWS Bedrock requires inference profile ARNs for most model invocations. Using a bare
        model ID (e.g., 'anthropic.claude-haiku-4-5-20251001-v1:0') will result in a
        ValidationException: "Invocation of model ID ... with on-demand throughput isn't
        supported. Retry your request with the ID or ARN of an inference profile that
        contains this model."

        Bedrock is currently only supported from us-west-2. The region is extracted from
        the ARN. If using legacy format without region, AWS_DEFAULT_REGION/AWS_REGION
        environment variables are checked, defaulting to us-west-2.

    AWS credentials are resolved via boto3's default credential chain:
        - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        - AWS credentials file (~/.aws/credentials)
        - AWS_PROFILE environment variable
        - IAM role (when running on AWS infrastructure)
    """
    # Check if it's an ARN (starts with arn:aws:bedrock)
    if model_spec.startswith("arn:aws:bedrock"):
        # Extract region from ARN: arn:aws:bedrock:REGION:ACCOUNT:inference-profile/...
        arn_parts = model_spec.split(":")
        if len(arn_parts) >= 4:
            region = arn_parts[3]  # Region is the 4th part
        else:
            region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-west-1")

            # Validate region format
        if not region or not region.startswith(("us-", "eu-", "ap-", "ca-", "sa-")):
            logger.error(f"Extracted region '{region}' from ARN may be invalid")

        logger.info(f"detected bedrock profile ARN: region={region}, arn={model_spec}")
        bedrock_provider = _create_bedrock_provider(region)

        return BedrockConverseModel(
            model_spec,  # Pass ARN directly as model_id
            provider=bedrock_provider,
            settings=BedrockModelSettings(
                parallel_tool_calls=True,
                bedrock_cache_instructions=True,
                bedrock_cache_tool_definitions=True,
                bedrock_cache_messages=True,
                bedrock_additional_model_requests_fields={
                    "thinking": {"type": "enabled", "budget_tokens": 2048}
                },
            ),
        )

    # Legacy format: region/model-id or bare model-id
    # Warn user that this may not work with newer models
    logger.warning(
        f"Using legacy Bedrock model ID format '{model_spec}'. "
        "AWS Bedrock now requires inference profile ARNs for most models. "
        "If you get a ValidationException, use the full ARN format: "
        "arn:aws:bedrock:REGION:ACCOUNT:inference-profile/MODEL"
    )

    if "/" in model_spec:
        region, model_id = model_spec.split("/", 1)
    else:
        model_id = model_spec
        region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-west-2")

    logger.info(f"Using legacy bedrock model: region={region}, model_id={model_id}")

    bedrock_provider = _create_bedrock_provider(region)

    return BedrockConverseModel(
        model_id,
        provider=bedrock_provider,
        settings=BedrockModelSettings(
            parallel_tool_calls=True,
            bedrock_cache_instructions=True,
            bedrock_cache_tool_definitions=True,
            bedrock_cache_messages=True,
            bedrock_additional_model_requests_fields={
                "thinking": {"type": "enabled", "budget_tokens": 2048}
            },
        ),
    )


def create_model(model: str) -> Union[Model, str]:
    """Create a configured PydanticAI model from a shorthand identifier.

    Supported formats:
        anthropic:claude-sonnet-4-5
        openai:gpt-4o
        google:gemini-1.5-pro
        gateway/anthropic:claude-sonnet-4-5 (via proxy)
        bedrock:anthropic.claude-3-sonnet-20240229-v1:0
        bedrock:us-west-2/anthropic.claude-3-sonnet-20240229-v1:0 (with region)
        bedrock:arn:aws:bedrock:... (profile ARN)
    """
    # Handle bedrock specially since model IDs contain colons
    if model.startswith("bedrock:"):
        model_spec = model[8:]  # Remove "bedrock:" prefix
        return _create_bedrock_model(model_spec)

    # Standard parsing for other providers: [provider/]family:name
    provider_parts = model.split("/")
    provider = None
    model_name_family = provider_parts[0]
    if len(provider_parts) > 1:
        provider = provider_parts[0]
        model_name_family =  provider_parts[1]
    parts = model_name_family.split(":")
    if not len(parts) == 2:
        raise ValueError(f"Invalid model name: {model_name_family}")
    family = parts[0]
    name = parts[1]
    if not provider:
        provider = family

    print(f"detected from: {model}, {provider}/{family}:{name}")
    if family == "anthropic":
        return AnthropicModel(
            name,
            settings=AnthropicModelSettings(
                anthropic_cache_instructions=True,
                anthropic_cache_tool_definitions=True,
                anthropic_cache_messages=True,
                parallel_tool_calls=True,
                anthropic_thinking=BetaThinkingConfigEnabledParam(
                    type="enabled",
                    budget_tokens=2048
            ),
        ),
        provider=provider
    )
    elif family == "openai":
        return OpenAIResponsesModel(name, settings=OpenAIResponsesModelSettings(
            parallel_tool_calls=True,
            openai_reasoning_effort="medium",
            openai_reasoning_summary="detailed",
        ),
            provider=provider,
            )
    elif family == "google":
        return GoogleModel(name, settings=GoogleModelSettings(
            parallel_tool_calls=True,
            google_thinking_config={'include_thoughts': True, 'thinking_budget_tokens': -1},
        ),
        provider=provider
    )
    else:
        logger.warning(f"Unknown model family: {family}")
        return model


def push_preview_tab(
    state: AgentState,
    *,
    title: str,
    tool_name: str,
    tab_type: str,
    data: Dict[str, Any],
    tab_id: Optional[str] = None,
    auto_open: bool = False,
    max_tabs: int = 20,
) -> str:
    """Append or update a preview tab entry in agent state."""
    if not state:
        return ""

    entry_id = tab_id or f"preview_{uuid4().hex[:10]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    tab_entry: Dict[str, Any] = {
        "id": entry_id,
        "title": title,
        "toolName": tool_name,
        "tabType": tab_type,
        "timestamp": timestamp,
        "data": data,
        "autoOpen": auto_open,
    }

    state.preview_tabs = [
        tab for tab in state.preview_tabs if tab.get("id") != entry_id
    ]
    state.preview_tabs.append(tab_entry)

    if len(state.preview_tabs) > max_tabs:
        state.preview_tabs = state.preview_tabs[-max_tabs:]

    return entry_id