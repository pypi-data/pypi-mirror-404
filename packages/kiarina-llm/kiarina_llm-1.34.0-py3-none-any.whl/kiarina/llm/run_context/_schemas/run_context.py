from typing import Any, Self

from pydantic import BaseModel, Field

from kiarina.llm.app_context import FSName

from .._types.id_str import IDStr


class RunContext(BaseModel):
    app_author: FSName
    """
    Application author

    Used in PlatformDirs.
    """

    app_name: FSName
    """
    Application name

    Used in PlatformDirs.
    """

    tenant_id: IDStr
    """
    Tenant ID

    Identifier for the tenant to which the user belongs.
    """

    user_id: IDStr
    """
    User ID

    Identifier for the user.
    """

    agent_id: IDStr
    """
    Agent ID

    Identifier for the agent used by the user.
    """

    runner_id: IDStr
    """
    Runner ID

    Identifier for the runner used by the AI.
    """

    time_zone: str = "UTC"
    """
    Time Zone

    IANA Time Zone.
    Specify in continent/city format.
    Example: "Asia/Tokyo"
    """

    language: str = "en"
    """
    Language

    ISO 639-1 code.
    Example: "en" (English), "ja" (Japanese)
    """

    currency: str = "USD"
    """
    Currency Code

    ISO 4217 currency code (3 letters).
    Example: "USD" (US Dollar), "JPY" (Japanese Yen), "EUR" (Euro)
    """

    metadata: dict[str, Any] = Field(default_factory=lambda: {})
    """Metadata"""

    def with_metadata(self, **kwargs: Any) -> Self:
        """
        Create a new RunContext with updated metadata.

        Args:
            **kwargs: Key-value pairs to update in metadata

        Returns:
            New RunContext instance with merged metadata

        Example:
            >>> context = create_run_context(metadata={"version": "1.0"})
            >>> new_context = context.with_metadata(version="2.0", env="prod")
            >>> new_context.metadata
            {"version": "2.0", "env": "prod"}
        """
        updated_metadata = {**self.metadata, **kwargs}
        return self.model_copy(update={"metadata": updated_metadata})
