import os
import json
import logging
import requests
from typing import Optional, Dict

import msal

import os

# Path to store the token cache
CACHE_FILE = "token_cache.json"


class MicrosoftSSO:

    def __init__(self):
        self.client_id = os.getenv("MS_CLIENT_ID")
        self.tenant_id = os.getenv("MS_TENANT_ID")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["User.Read", "Analytics.Read", "Chat.Read", "Calendars.Read"]

        self.logger = logging.getLogger(__name__)
        print(f"Microsoft SSO client ID: {self.client_id} is HERE IN {__name__}  ***********************************************************************************")
        # Load or create the token cache
        self.cache = self._load_cache()

        # Initialize MSAL with the cache
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache
        )

    @staticmethod
    def _load_cache() -> msal.SerializableTokenCache:
        """Load the token cache from a file if it exists."""
        cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cache.deserialize(f.read())
        return cache

    def _save_cache(self):
        """Save the token cache to a file if it has changed."""
        if self.cache.has_state_changed:
            with open(CACHE_FILE, "w") as f:
                f.write(self.cache.serialize())

    def get_access_token(self) -> Optional[Dict]:
        """Get an access token, trying silent acquisition first."""
        try:
            # Check for cached accounts
            accounts = self.app.get_accounts()
            if accounts:
                self.logger.info("Attempting silent token acquisition")
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self.logger.info("Token acquired silently")
                    return result
                else:
                    self.logger.info("Silent acquisition failed, falling back to device code")

            # Fallback to device code flow if silent fails
            self.logger.info("Starting device code flow")
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            print(f"Please visit {flow['verification_uri']} and enter code: {flow['user_code']}")
            result = self.app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                self.logger.info("Token acquired via device code flow")
                self._save_cache()  # Save the cache after successful authentication
                return result
            else:
                self.logger.error(f"Token acquisition failed: {result.get('error_description')}")
                return None

        except Exception as e:
            self.logger.error(f"Error acquiring token: {str(e)}", exc_info=True)
            raise SystemExit

    def get_users(self) -> Optional[Dict]:
        """Get a list of users from the Microsoft Graph API."""
        token_result = self.get_access_token()
        if not token_result or "access_token" not in token_result:
            self.logger.error("No valid access token available")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token_result['access_token']}",
                "Content-Type": "application/json"
            }

            self.logger.info("Making Graph API request to /users")
            response = requests.get(
                "https://graph.microsoft.com/v1.0/users",
                headers=headers
            )
            response.raise_for_status()  # Raises an exception for HTTP errors

            users = response.json().get("value")
            if users:
                self.logger.info(f"Successfully retrieved {len(users)} users")
                return users
            else:
                self.logger.error("No users found in response")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Graph API request failed: {str(e)}")
            if isinstance(e.response, requests.Response):
                error_details = e.response.text
                self.logger.error(f"Response details: {error_details}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            return None

    def get_user_info(self) -> Optional[Dict[str, str]]:
        """
        Get the authenticated user's ID and email address from Microsoft Graph API.

        Returns:
            Dict[str, str]: A dictionary with 'id' and 'email' keys, or None if the request fails.
        """
        token_result = self.get_access_token()
        if not token_result or "access_token" not in token_result:
            self.logger.error("No valid access token available")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token_result['access_token']}",
                "Content-Type": "application/json"
            }

            self.logger.info("Making Graph API request to /me")
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers
            )
            response.raise_for_status()  # Raises an exception for HTTP errors

            user_data = response.json()
            print(f"User data: {user_data}")
            user_id = user_data.get("id")
            user_email = user_data.get("mail") or user_data.get("userPrincipalName")

            if user_id and user_email:
                self.logger.info(f"Successfully retrieved user info: ID={user_id}, Email={user_email}")
                return {"id": user_id, "email": user_email}
            else:
                self.logger.error("User ID or email not found in response")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Graph API request failed: {str(e)}")
            if isinstance(e.response, requests.Response):
                error_details = e.response.text
                self.logger.error(f"Response details: {error_details}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            return None

    def make_entra_request(self, input_str: str) -> dict:
        """
        Makes a request to a Microsoft Entra endpoint using the Microsoft Graph API.

        Args:
            input_str (str): A JSON string containing the request details, e.g., {"method": "GET", "path": "me"}

        Returns:
            dict: Response data or error details if the request fails.
        """
        print(f"\n\n CALLING WITH INPUT: {input_str}\n\n")
        try:
            input_data = json.loads(input_str)
            method = input_data["method"]
            path = input_data["path"]
            query_params = input_data.get("query_params", {})
            body = input_data.get("body", {})
            # Add other optional fields as needed (e.g., query_params, body)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input. Expected a string like {\"method\": \"GET\", \"path\": \"me\"}"}
        except KeyError as e:
            return {"error": f"Missing required field: {e}"}

        # Define supported HTTP methods
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if method.upper() not in allowed_methods:
            return {"error": "Unsupported HTTP method"}

        # Obtain access token
        try:
            token_result = self.get_access_token()
        except ValueError as e:
            return {"error": str(e)}

        # print(f"Access Token: {token_result}")
        # Construct the URL
        url = f"https://graph.microsoft.com/beta/{path}"
        headers = {
            "Authorization": f"Bearer {token_result['access_token']}",
            "Content-Type": "application/json"
        }
        # Make the request
        response = None
        try:
            response = requests.request(method.upper(), url, headers=headers, params=query_params, json=body)
            response.raise_for_status()

            if response.status_code == 204:
                return {"message": "Operation successful, no content returned"}
            else:
                return response.json()
        except requests.exceptions.HTTPError as e:
            return {"error": str(e), "status_code": response.status_code, "response": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def logout(self) -> bool:
        try:
            accounts = self.app.get_accounts()
            for account in accounts:
                self.app.remove_account(account)
            self.logger.info("Successfully logged out")
            return True
        except Exception as e:
            self.logger.error(f"Error during logout: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # These values should come from your Azure AD app registration
    TENANT_ID = os.getenv("MS_TENANT_ID")
    CLIENT_ID = os.getenv("MS_CLIENT_ID")
    CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
    # CLIENT_SECRET = None

    sso = MicrosoftSSO()

    # user_id = sso.get_user_id()

    user_info = sso.get_user_info()
    if user_info:
        print(f"Authenticated User ID: {user_info['id']}")
        print(f"Authenticated User Email: {user_info['email']}")
    else:
        print("Failed to authenticate or get user info")

    print(f"\n\nUser list: {sso.get_users()}")
    result = sso.make_entra_request('{"method": "GET", "path": "users/delta"}')
    print(f"\n\nEntitlements: {result}")
    # sso.logout()
