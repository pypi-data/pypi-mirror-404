"""Tests for Bedrock provider creation and error handling.

Tests the _create_bedrock_provider and _create_bedrock_model functions including:
- ARN-based model creation (expected format)
- Legacy model ID format (with warning)
- Error handling for missing credentials
- Error handling for access denied
- Error handling for general boto errors
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


class TestCreateBedrockProvider:
    """Tests for _create_bedrock_provider function."""

    @patch("lineage.agent.pydantic.utils.BedrockProvider")
    def test_provider_creation(self, mock_provider):
        """Provider creation succeeds with valid region."""
        from lineage.agent.pydantic.utils import _create_bedrock_provider

        mock_provider.return_value = MagicMock()

        result = _create_bedrock_provider("us-west-2")

        mock_provider.assert_called_once_with(region_name="us-west-2")
        assert result is not None

    @patch.dict("os.environ", {}, clear=True)
    @patch("lineage.agent.pydantic.utils.BedrockProvider")
    def test_no_credentials_error(self, mock_provider):
        """Proper error handling when credentials are not found."""
        from lineage.agent.pydantic.utils import _create_bedrock_provider

        mock_provider.side_effect = NoCredentialsError()

        with pytest.raises(RuntimeError) as exc_info:
            _create_bedrock_provider("us-west-2")

        assert "AWS credentials not found" in str(exc_info.value)
        assert "AWS_PROFILE" in str(exc_info.value)

    @patch.dict("os.environ", {}, clear=True)
    @patch("lineage.agent.pydantic.utils.BedrockProvider")
    def test_access_denied_error(self, mock_provider):
        """Proper error handling when access is denied."""
        from lineage.agent.pydantic.utils import _create_bedrock_provider

        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized to perform bedrock:InvokeModel",
            }
        }
        mock_provider.side_effect = ClientError(error_response, "InvokeModel")

        with pytest.raises(RuntimeError) as exc_info:
            _create_bedrock_provider("us-west-2")

        assert "AccessDeniedException" in str(exc_info.value)
        assert "bedrock:InvokeModel" in str(exc_info.value)

    @patch.dict("os.environ", {}, clear=True)
    @patch("lineage.agent.pydantic.utils.BedrockProvider")
    def test_general_boto_error(self, mock_provider):
        """Proper error handling for general boto errors."""
        from lineage.agent.pydantic.utils import _create_bedrock_provider

        mock_provider.side_effect = BotoCoreError()

        with pytest.raises(RuntimeError) as exc_info:
            _create_bedrock_provider("us-west-2")

        assert "Bedrock provider creation failed" in str(exc_info.value)


class TestCreateBedrockModel:
    """Tests for _create_bedrock_model function.

    AWS Bedrock requires inference profile ARNs for most model invocations.
    Using a bare model ID will result in a ValidationException:
        "Invocation of model ID anthropic.claude-haiku-4-5-20251001-v1:0 with
        on-demand throughput isn't supported. Retry your request with the ID
        or ARN of an inference profile that contains this model."
    """

    @patch("lineage.agent.pydantic.utils._create_bedrock_provider")
    @patch("lineage.agent.pydantic.utils.BedrockConverseModel")
    def test_model_with_arn(self, mock_model, mock_provider):
        """Model creation with ARN extracts region and uses ARN directly.

        This is the expected format for Bedrock model invocation.
        """
        from lineage.agent.pydantic.utils import _create_bedrock_model

        mock_provider.return_value = MagicMock()
        mock_model.return_value = MagicMock()

        arn = "arn:aws:bedrock:us-west-2:025066247024:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0"
        _create_bedrock_model(arn)

        # Region should be extracted from ARN
        mock_provider.assert_called_once_with("us-west-2")
        # ARN should be passed directly to the model
        mock_model.assert_called_once()
        assert mock_model.call_args[0][0] == arn

    @patch("lineage.agent.pydantic.utils._create_bedrock_provider")
    @patch("lineage.agent.pydantic.utils.BedrockConverseModel")
    def test_model_without_arn(self, mock_model, mock_provider, caplog):
        """Model creation with legacy model ID logs a warning.

        Legacy format may not work with newer models that require inference profiles.
        """
        from lineage.agent.pydantic.utils import _create_bedrock_model

        mock_provider.return_value = MagicMock()
        mock_model.return_value = MagicMock()

        with patch.dict("os.environ", {}, clear=True):
            _create_bedrock_model("anthropic.claude-3-sonnet-20240229-v1:0")

        # Should use default region us-west-2
        mock_provider.assert_called_once_with("us-west-2")
        # Should log a warning about legacy format
        assert any("legacy" in record.message.lower() for record in caplog.records)
        assert any("arn" in record.message.lower() for record in caplog.records)
