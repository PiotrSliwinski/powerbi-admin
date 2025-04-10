from .client import PowerBIClient
import logging

logger = logging.getLogger(__name__)

class GatewayAdmin:
    """Provides methods for administering Power BI On-premises Data Gateways."""

    def __init__(self, client: PowerBIClient):
        self.client = client

    def get_gateways(self) -> list[dict]:
        """Retrieves a list of gateways the user has access to.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/get-gateways

        Returns:
            list[dict]: A list of gateway objects.
        """
        logger.info("Fetching gateways...")
        response = self.client.get("gateways")
        gateways = response.get("value", [])
        logger.info(f"Found {len(gateways)} gateways.")
        return gateways

    def get_gateway_datasources(self, gateway_id: str) -> list[dict]:
        """Retrieves a list of datasources for a specific gateway.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/get-datasources

        Args:
            gateway_id: The ID of the gateway.

        Returns:
            list[dict]: A list of datasource objects for the gateway.
        """
        logger.info(f"Fetching datasources for gateway ID: {gateway_id}")
        endpoint = f"gateways/{gateway_id}/datasources"
        response = self.client.get(endpoint)
        datasources = response.get("value", [])
        logger.info(f"Found {len(datasources)} datasources for gateway {gateway_id}.")
        return datasources

    def get_gateway_datasource_users(self, gateway_id: str, datasource_id: str) -> list[dict]:
        """Retrieves a list of users who have access to a specific datasource.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/get-datasource-users

        Args:
            gateway_id: The ID of the gateway.
            datasource_id: The ID of the datasource.

        Returns:
            list[dict]: A list of user objects with access to the datasource.
        """
        logger.info(f"Fetching users for datasource ID: {datasource_id} on gateway ID: {gateway_id}")
        endpoint = f"gateways/{gateway_id}/datasources/{datasource_id}/users"
        # This API might require specific permissions (Datasource.Read.All or Datasource.ReadWrite.All)
        try:
            response = self.client.get(endpoint)
            users = response.get("value", [])
            logger.info(f"Found {len(users)} users for datasource {datasource_id}.")
            return users
        except Exception as e:
            # Handle potential permission errors or other issues gracefully
            logger.error(f"Could not get users for datasource {datasource_id} on gateway {gateway_id}: {e}")
            # Check if the error response is available and contains details
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"API Response Status: {e.response.status_code}")
                try:
                    logger.error(f"API Response Body: {e.response.json()}")
                except Exception:
                    logger.error(f"API Response Body: {e.response.text}")
            return [] # Return empty list on error

    def add_datasource_user(
        self,
        gateway_id: str,
        datasource_id: str,
        principal_id: str,
        principal_type: str, # 'User', 'Group', or 'ServicePrincipal'
        access_right: str,   # 'Read' or 'ReadOverrideEffectiveIdentity'
        display_name: str | None = None,
        email_address: str | None = None,
        profile: dict | None = None # For ServicePrincipal
    ) -> bool:
        """Adds a user or group to a gateway datasource with specified access rights.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/add-datasource-user

        Args:
            gateway_id: The ID of the gateway.
            datasource_id: The ID of the datasource.
            principal_id: The Object ID (GUID) of the principal (user, group, or service principal).
            principal_type: The type of the principal ('User', 'Group', 'ServicePrincipal').
            access_right: The access level ('Read' or 'ReadOverrideEffectiveIdentity').
            display_name: Optional display name for the principal.
            email_address: Optional email address (required for users).
            profile: Optional service principal profile details.

        Returns:
            bool: True if the user was added successfully, False otherwise.
        """
        logger.info(f"Adding {principal_type} (ID: {principal_id}) to datasource {datasource_id} on gateway {gateway_id} with rights: {access_right}")
        endpoint = f"gateways/{gateway_id}/datasources/{datasource_id}/users"

        payload = {
            "identifier": principal_id,
            "principalType": principal_type,
            "datasourceUserAccessRight": access_right,
        }
        if display_name:
            payload["displayName"] = display_name
        if email_address:
            payload["emailAddress"] = email_address
        if principal_type == 'ServicePrincipal' and profile:
            payload["profile"] = profile
        elif principal_type == 'User' and not email_address:
             logger.warning(f"Adding a user principal ({principal_id}) without an emailAddress is often problematic.")
             # Consider raising an error or requiring email for User type

        try:
            # This POST request typically returns 200 OK on success with no body, or 201 Created.
            # The base client handles JSON decoding and status code checks.
            self.client.post(endpoint, json=payload)
            logger.info(f"Successfully added {principal_type} {principal_id} to datasource {datasource_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to add user {principal_id} to datasource {datasource_id} on gateway {gateway_id}: {e}")
            # Log specific API error details if available
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"API Response Status: {e.response.status_code}")
                try:
                    logger.error(f"API Response Body: {e.response.json()}")
                except Exception:
                    logger.error(f"API Response Body: {e.response.text}")
            return False 