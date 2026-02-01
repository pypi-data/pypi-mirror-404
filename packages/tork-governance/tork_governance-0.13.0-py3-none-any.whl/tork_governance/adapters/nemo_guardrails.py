"""
NeMo Guardrails adapter for Tork Governance.

Integrates Tork governance with NVIDIA's NeMo Guardrails toolkit.
Provides actions, config wrappers, and Colang flow integration.

Example:
    from nemoguardrails import RailsConfig, LLMRails
    from tork_governance.adapters.nemo_guardrails import TorkNeMoAction, TorkRailsConfig

    # Use as a custom action
    config = RailsConfig.from_path("config")
    rails = LLMRails(config)
    rails.register_action(TorkNeMoAction(), name="tork_govern")

    # Use wrapped config
    tork_config = TorkRailsConfig(config)
    rails = tork_config.create_rails()
"""

from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
from ..core import Tork, GovernanceResult, GovernanceAction


class TorkNeMoAction:
    """
    NeMo Guardrails action for Tork governance.

    Can be registered as a custom action in NeMo Guardrails to
    enable PII detection and redaction in Colang flows.

    Colang usage:
        define flow check_pii
            $result = execute tork_govern(text=$user_message)
            if $result.has_pii
                bot inform pii detected
            else
                continue
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        action_on_pii: str = "redact",  # "redact", "block", "warn", "allow"
        pii_types_to_block: Optional[List[str]] = None,
    ):
        self.tork = Tork(api_key=api_key)
        self.action_on_pii = action_on_pii
        self.pii_types_to_block = pii_types_to_block or ["ssn", "credit_card"]
        self._receipts: List[str] = []

    async def __call__(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the Tork governance action.

        Args:
            text: The text to govern
            context: NeMo context dictionary

        Returns:
            Dictionary with governance results for Colang
        """
        result = self.tork.govern(text)

        if result.receipt:
            self._receipts.append(result.receipt.receipt_id)

        pii_types = [m.type.value for m in result.pii.matches]
        has_blocked_pii = any(
            pii_type in self.pii_types_to_block
            for pii_type in pii_types
        )

        # Determine action
        should_block = (
            self.action_on_pii == "block" and result.pii.has_pii
        ) or (
            has_blocked_pii and self.action_on_pii != "allow"
        )

        return {
            "text": result.output,
            "original": text,
            "has_pii": result.pii.has_pii,
            "pii_types": pii_types,
            "action": result.action.value,
            "should_block": should_block,
            "receipt_id": result.receipt.receipt_id if result.receipt else None,
            "redacted": result.output != text,
        }

    def sync_call(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Synchronous version of the action."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self(text, context, **kwargs)
        )

    @property
    def receipts(self) -> List[str]:
        """Get all governance receipt IDs."""
        return self._receipts.copy()


class TorkRailsConfig:
    """
    Wrapper for NeMo RailsConfig that adds Tork governance.

    Automatically registers Tork actions and adds governance
    to the rails configuration.
    """

    def __init__(
        self,
        config: Any = None,
        config_path: Optional[str] = None,
        api_key: Optional[str] = None,
        govern_input: bool = True,
        govern_output: bool = True,
    ):
        self.config = config
        self.config_path = config_path
        self.tork = Tork(api_key=api_key)
        self.govern_input = govern_input
        self.govern_output = govern_output
        self._action = TorkNeMoAction(api_key=api_key)

    def create_rails(self, **kwargs) -> Any:
        """
        Create LLMRails with Tork governance enabled.

        Returns:
            LLMRails instance with Tork actions registered
        """
        try:
            from nemoguardrails import RailsConfig, LLMRails
        except ImportError:
            raise ImportError(
                "nemoguardrails is required: pip install nemoguardrails"
            )

        # Load config
        if self.config is None and self.config_path:
            config = RailsConfig.from_path(self.config_path)
        else:
            config = self.config

        # Create rails
        rails = LLMRails(config, **kwargs)

        # Register Tork actions
        rails.register_action(self._action, name="tork_govern")
        rails.register_action(self._action, name="tork_check_pii")
        rails.register_action(self._govern_text_action, name="tork_redact")

        return rails

    async def _govern_text_action(self, text: str, **kwargs) -> str:
        """Simple governance action that returns redacted text."""
        result = self.tork.govern(text)
        return result.output

    def get_colang_flows(self) -> str:
        """
        Get Colang flow definitions for Tork governance.

        Returns Colang code that can be added to your config.
        """
        return '''
# Tork Governance Flows

define flow tork input governance
    """Check user input for PII and redact if needed."""
    $governance = execute tork_govern(text=$user_message)
    if $governance.should_block
        bot inform pii blocked
        stop
    else if $governance.has_pii
        $user_message = $governance.text

define flow tork output governance
    """Check bot response for PII and redact if needed."""
    $governance = execute tork_govern(text=$bot_message)
    if $governance.has_pii
        $bot_message = $governance.text

define bot inform pii blocked
    "I cannot process this request as it contains sensitive personal information that I'm not allowed to handle."

define bot inform pii detected
    "I noticed some personal information in your message. I've redacted it for your privacy."
'''

    @property
    def action(self) -> TorkNeMoAction:
        """Get the Tork action instance."""
        return self._action


class TorkNeMoMiddleware:
    """
    Middleware for NeMo Guardrails that applies Tork governance.

    Can be used to wrap the generate method of LLMRails.
    """

    def __init__(
        self,
        rails: Any,
        api_key: Optional[str] = None,
        govern_input: bool = True,
        govern_output: bool = True,
    ):
        self.rails = rails
        self.tork = Tork(api_key=api_key)
        self.govern_input = govern_input
        self.govern_output = govern_output
        self._receipts: List[str] = []

    async def generate(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate with governance applied.

        Governs input messages/prompt and output response.
        """
        # Govern input
        if self.govern_input:
            if messages:
                messages = self._govern_messages(messages)
            if prompt:
                result = self.tork.govern(prompt)
                prompt = result.output
                if result.receipt:
                    self._receipts.append(result.receipt.receipt_id)

        # Call rails
        if messages:
            response = await self.rails.generate_async(messages=messages, **kwargs)
        else:
            response = await self.rails.generate_async(prompt=prompt, **kwargs)

        # Govern output
        if self.govern_output:
            if isinstance(response, str):
                result = self.tork.govern(response)
                response = result.output
                if result.receipt:
                    self._receipts.append(result.receipt.receipt_id)
            elif isinstance(response, dict) and "content" in response:
                result = self.tork.govern(response["content"])
                response["content"] = result.output
                if result.receipt:
                    self._receipts.append(result.receipt.receipt_id)

        return response

    def _govern_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Govern a list of messages."""
        governed = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                result = self.tork.govern(content)
                governed_msg = msg.copy()
                governed_msg["content"] = result.output
                if result.receipt:
                    self._receipts.append(result.receipt.receipt_id)
                governed.append(governed_msg)
            else:
                governed.append(msg)
        return governed

    @property
    def receipts(self) -> List[str]:
        """Get all governance receipt IDs."""
        return self._receipts.copy()


def govern_rails(
    api_key: Optional[str] = None,
    govern_input: bool = True,
    govern_output: bool = True,
):
    """
    Decorator to add Tork governance to NeMo Guardrails functions.

    Example:
        @govern_rails()
        async def my_rails_function(rails, prompt: str) -> str:
            return await rails.generate_async(prompt=prompt)
    """
    def decorator(func: Callable) -> Callable:
        tork = Tork(api_key=api_key)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Govern string arguments
            if govern_input:
                args = tuple(
                    tork.govern(arg).output if isinstance(arg, str) else arg
                    for arg in args
                )
                kwargs = {
                    k: tork.govern(v).output if isinstance(v, str) else v
                    for k, v in kwargs.items()
                }

            result = await func(*args, **kwargs)

            # Govern output
            if govern_output and isinstance(result, str):
                result = tork.govern(result).output

            return result

        return wrapper
    return decorator


def register_tork_actions(rails: Any, api_key: Optional[str] = None) -> None:
    """
    Register all Tork actions with an LLMRails instance.

    Convenience function to quickly add Tork governance to existing rails.

    Example:
        from nemoguardrails import LLMRails
        from tork_governance.adapters.nemo_guardrails import register_tork_actions

        rails = LLMRails(config)
        register_tork_actions(rails)
    """
    action = TorkNeMoAction(api_key=api_key)
    rails.register_action(action, name="tork_govern")
    rails.register_action(action, name="tork_check_pii")

    tork = Tork(api_key=api_key)

    async def tork_redact(text: str, **kwargs) -> str:
        return tork.govern(text).output

    rails.register_action(tork_redact, name="tork_redact")
