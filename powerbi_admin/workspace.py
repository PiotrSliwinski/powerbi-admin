from .client import PowerBIClient
import logging

logger = logging.getLogger(__name__)

class WorkspaceAdmin:
    """Provides methods for administering Power BI Workspaces (also known as Groups)."""

    def __init__(self, client: PowerBIClient):
        self.client = client

    def get_workspaces(self, filter_str: str | None = None, top: int | None = None, skip: int | None = None) -> list[dict]:
        """Retrieves a list of workspaces the user has access to.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/groups/get-groups

        Args:
            filter_str: OData filter string (e.g., "startswith(name, 'Test')").
            top: Number of results to return.
            skip: Number of results to skip.

        Returns:
            list[dict]: A list of workspace (group) objects.
        """
        logger.info("Fetching workspaces...")
        params = {}
        if filter_str:
            params["$filter"] = filter_str
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip

        response = self.client.get("groups", params=params)
        workspaces = response.get("value", [])
        logger.info(f"Found {len(workspaces)} workspaces matching criteria.")
        return workspaces

    def get_workspace_users(self, workspace_id: str) -> list[dict]:
        """Retrieves a list of users and their access rights for a specific workspace.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/groups/get-group-users

        Args:
            workspace_id: The ID of the workspace (group).

        Returns:
            list[dict]: A list of user access objects for the workspace.
        """
        logger.info(f"Fetching users for workspace ID: {workspace_id}")
        endpoint = f"groups/{workspace_id}/users"
        try:
            response = self.client.get(endpoint)
            users = response.get("value", [])
            logger.info(f"Found {len(users)} users for workspace {workspace_id}.")
            return users
        except Exception as e:
            logger.error(f"Could not get users for workspace {workspace_id}: {e}")
            self._log_api_error(e)
            return []

    def add_workspace_user(
        self,
        workspace_id: str,
        identifier: str,
        principal_type: str, # 'User', 'Group', 'ServicePrincipal', 'App'
        access_right: str,   # 'Admin', 'Member', 'Contributor', 'Viewer'
        email_address: str | None = None # Required for 'User' principal type
    ) -> bool:
        """Adds a user or principal to a workspace with specified access rights.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/groups/add-group-user

        Args:
            workspace_id: The ID of the workspace (group).
            identifier: The identifier of the principal. For 'User', it's email or UPN.
                        For 'Group', it's the group object ID.
                        For 'ServicePrincipal', it's the service principal object ID.
                        For 'App', it's the application ID.
            principal_type: Type of principal ('User', 'Group', 'ServicePrincipal', 'App').
            access_right: Access level ('Admin', 'Member', 'Contributor', 'Viewer').
            email_address: Required when principal_type is 'User'.

        Returns:
            bool: True if the user was added successfully, False otherwise.
        """
        logger.info(f"Adding {principal_type} ({identifier}) to workspace {workspace_id} with rights: {access_right}")
        endpoint = f"groups/{workspace_id}/users"

        payload = {
            "identifier": identifier,
            "principalType": principal_type,
            "groupUserAccessRight": access_right,
        }
        # Email is required for user type according to docs, include it in payload
        if principal_type == 'User':
            if email_address:
                 payload["emailAddress"] = email_address
            else:
                # The API expects identifier to be email/UPN for User, but let's keep email separate for clarity
                # If email isn't provided, we assume identifier is the email/UPN.
                logger.warning(f"Adding User principal ({identifier}) without explicit emailAddress. Assuming identifier is email/UPN.")
                payload["emailAddress"] = identifier

        try:
            self.client.post(endpoint, json=payload)
            logger.info(f"Successfully added {principal_type} {identifier} to workspace {workspace_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to add {principal_type} {identifier} to workspace {workspace_id}: {e}")
            self._log_api_error(e)
            return False

    def delete_workspace_user(self, workspace_id: str, identifier: str, principal_type: str | None = None) -> bool:
        """Removes a user or principal from a workspace.

        Ref: https://learn.microsoft.com/en-us/rest/api/power-bi/groups/delete-user-in-group

        Note: The API documentation for DELETE is slightly ambiguous about the identifier.
              It usually requires the UPN or Object ID depending on the context/principal type.
              If principal_type is not 'User', the 'identifier' should typically be the Object ID.
              For 'User', it is usually the UPN.

        Args:
            workspace_id: The ID of the workspace (group).
            identifier: The UPN (for User) or Object ID (for Group/SP/App) to remove.
            principal_type: Optional hint ('User', 'Group', 'ServicePrincipal', 'App') for logging/debugging.
                          The API endpoint itself doesn't take this parameter.

        Returns:
            bool: True if the user was deleted successfully, False otherwise.
        """
        principal_info = f"{principal_type} ({identifier})" if principal_type else identifier
        logger.info(f"Deleting {principal_info} from workspace {workspace_id}")

        # The API endpoint structure requires the user identifier directly in the URL.
        # Ensure the identifier is properly URL-encoded if it contains special characters,
        # although the requests library usually handles this.
        endpoint = f"groups/{workspace_id}/users/{identifier}"

        try:
            # Need to add a delete method to the base client
            # For now, let's assume it exists or call _request directly
            self.client._request("DELETE", endpoint)
            logger.info(f"Successfully deleted {principal_info} from workspace {workspace_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {principal_info} from workspace {workspace_id}: {e}")
            self._log_api_error(e)
            return False

    def _log_api_error(self, error: Exception):
        """Helper method to log API error details."""
        if hasattr(error, 'response') and error.response is not None:
            logger.error(f"API Response Status: {error.response.status_code}")
            try:
                logger.error(f"API Response Body: {error.response.json()}")
            except Exception:
                logger.error(f"API Response Body: {error.response.text}") 