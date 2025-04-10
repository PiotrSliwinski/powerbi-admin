import logging
from azure.identity import DefaultAzureCredential, CredentialUnavailableError

logger = logging.getLogger(__name__)

class PowerBIAuth:
    """Handles authentication using DefaultAzureCredential to obtain tokens for Power BI API access."""

    def __init__(self, tenant_id: str | None = None):
        """Initializes the authentication handler.

        Args:
            tenant_id: Optional Tenant ID. If provided, credentials will be restricted
                       to this tenant. If None, DefaultAzureCredential will try to
                       determine the tenant from the environment or logged-in user.
        """
        self.tenant_id = tenant_id
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]
        # Initialize DefaultAzureCredential, optionally specifying the tenant ID
        try:
            self.credential = DefaultAzureCredential(authority=f"https://login.microsoftonline.com/{self.tenant_id}" if self.tenant_id else None)
            # Perform a quick check to see if credentials might be available
            # This is not foolproof but can catch immediate configuration issues.
            # self.credential.get_token(self.scope)
        except ImportError:
             logger.error("Azure Identity library not installed. Please install 'azure-identity'.")
             raise
        except Exception as e:
            logger.error(f"Error initializing DefaultAzureCredential: {e}")
            raise

    def get_access_token(self) -> str:
        """Acquires an access token for the Power BI API using DefaultAzureCredential.

        DefaultAzureCredential attempts various strategies (Environment, Managed Identity,
        Azure CLI, etc.) to obtain a token.

        Returns:
            str: The access token.

        Raises:
            CredentialUnavailableError: If DefaultAzureCredential fails to find credentials
                                       or authenticate.
            Exception: For other potential errors during token acquisition.
        """
        try:
            logger.info("Attempting to acquire token using DefaultAzureCredential...")
            access_token_info = self.credential.get_token(*self.scope)
            logger.info("Successfully acquired access token.")
            return access_token_info.token
        except CredentialUnavailableError as e:
            logger.error(f"DefaultAzureCredential failed: {e}")
            logger.error("Ensure you are logged in via Azure CLI ('az login'), "
                         "or have environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID), "
                         "or are running in an environment with Managed Identity.")
            raise
        except Exception as e:
            # Catch other potential exceptions from get_token
            logger.error(f"An unexpected error occurred during token acquisition: {e}")
            raise 