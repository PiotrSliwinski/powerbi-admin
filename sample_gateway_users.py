import os
import logging
from admin.auth import PowerBIAuth
from admin.client import PowerBIClient
from admin.gateway import GatewayAdmin
from azure.identity import CredentialUnavailableError

# --- Configuration ---
# DefaultAzureCredential will attempt to authenticate using environment variables,
# managed identity, Azure CLI login, etc.
# You can optionally specify a tenant ID if needed.
TENANT_ID = os.getenv("POWERBI_TENANT_ID", None) # Optional: Set if needed

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Disable overly verbose logging from underlying libraries if desired
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Main function to demonstrate gateway administration using DefaultAzureCredential."""

    try:
        # 1. Authenticate using DefaultAzureCredential
        logger.info("Authenticating using DefaultAzureCredential...")
        # Pass tenant_id if specified, otherwise None
        auth = PowerBIAuth(tenant_id=TENANT_ID)

        # 2. Create Client
        client = PowerBIClient(auth)

        # 3. Initialize Gateway Admin module
        gw_admin = GatewayAdmin(client)

        # 4. Get Gateways
        gateways = gw_admin.get_gateways()

        if not gateways:
            logger.info("No gateways found or accessible for the authenticated user.")
            return

        print("\n--- Gateway Datasources and Users ---")

        # 5. Iterate through Gateways and Datasources
        for gw in gateways:
            gateway_id = gw['id']
            gateway_name = gw['name']
            print(f"\nGateway: {gateway_name} (ID: {gateway_id})")

            datasources = gw_admin.get_gateway_datasources(gateway_id)

            if not datasources:
                print("  No datasources found for this gateway.")
                continue

            for ds in datasources:
                datasource_id = ds['id']
                datasource_name = ds['datasourceName']
                datasource_type = ds['datasourceType']
                print(f"  Datasource: {datasource_name} (ID: {datasource_id}, Type: {datasource_type})")

                # 6. Get Users for each Datasource
                users = gw_admin.get_gateway_datasource_users(gateway_id, datasource_id)

                if not users:
                    print("    No users found for this datasource.")
                else:
                    print("    Users:")
                    for user in users:
                        # Adjust fields based on actual API response structure if needed
                        display_name = user.get('displayName', 'N/A')
                        email = user.get('emailAddress', 'N/A')
                        principal_type = user.get('principalType', 'N/A') # e.g., User, Group, ServicePrincipal
                        access_right = user.get('datasourceUserAccessRight', 'N/A') # e.g., Read, ReadOverrideEffectiveIdentity
                        print(f"      - Name: {display_name}, Email: {email}, Type: {principal_type}, Access: {access_right}")

    except CredentialUnavailableError:
        # Specific handling for credential errors from DefaultAzureCredential
        logger.error("Authentication failed. DefaultAzureCredential could not find valid credentials.")
        logger.error("Please ensure you are logged in via 'az login', or have appropriate environment variables set (e.g., AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET or AZURE_USERNAME, AZURE_PASSWORD), or are running in an Azure environment with Managed Identity configured.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main() 