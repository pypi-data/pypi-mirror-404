import json
import os
import logging
import warnings
from typing import Dict, Any, Optional, Mapping, Union

# Optional import to support newer config objects without hard dependency
try:
    from core.utils.qd_config import QDConfig  # type: ignore
except Exception:  # pragma: no cover - not present in all installs
    QDConfig = None  # type: ignore[misc,assignment]

import msal
import requests

CACHE_FILE = "token_cache.json"


class Microsoft365Provider:

    def __init__(self, config: Union["QDConfig", Mapping[str, Any], None] = None):
        self.logger = logging.getLogger(__name__)

        # Maintain compatibility with upstream provider expectations
        if config is None:
            warnings.warn(
                "Microsoft365Provider() without config is deprecated. Pass config explicitly.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Read from explicit config when provided; fall back to environment.
        if QDConfig is not None and isinstance(config, QDConfig):
            self.logger.info(f"Loading supplied QDConfig")
            tenant_id = config.get_ms_tenant_id()
            client_id = config.get_ms_client_id()
            client_secret = config.get_ms_client_secret()
            redirect_uri = config.get_ms_redirect_uri()
            scopes = config.get_ms_scopes()
        elif isinstance(config, Mapping):
            self.logger.info(f"Loading supplied config mapping")
            tenant_id = config.get("QD_MS_TENANT_ID") or config.get("MS_TENANT_ID") or os.getenv("MS_TENANT_ID")
            client_id = config.get("QD_MS_CLIENT_ID") or config.get("MS_CLIENT_ID") or os.getenv("MS_CLIENT_ID")
            client_secret = config.get("QD_MS_CLIENT_SECRET") or config.get("MS_CLIENT_SECRET") or os.getenv("MS_CLIENT_SECRET")
            redirect_uri = config.get("QD_MS_REDIRECT_URI") or config.get("MS_REDIRECT_URI") or os.getenv("MS_REDIRECT_URI")
            scopes = config.get("QD_MS_SCOPES") or config.get("MS_SCOPES") or os.getenv("MS_SCOPES")
        else:
            self.logger.info(f"Loading from environment variables")
            tenant_id = os.getenv("MS_TENANT_ID")
            client_id = os.getenv("MS_CLIENT_ID")
            client_secret = os.getenv("MS_CLIENT_SECRET")
            redirect_uri = os.getenv("MS_REDIRECT_URI")
            scopes = os.getenv("MS_SCOPES")

        if not tenant_id:
            self.logger.warning("MS_TENANT_ID environment variable not set")
            raise RuntimeError("MS_TENANT_ID environment variable not set")
        self.tenant_id = tenant_id
        self.logger.info(f"tenant_id: {self.tenant_id}")

        if not client_id:
            self.logger.warning("MS_CLIENT_ID environment variable not set")
            raise RuntimeError("MS_CLIENT_ID environment variable not set")
        self.client_id = client_id
        self.logger.info(f"client_id: {self.client_id}")

        if not client_secret:
            self.logger.warning("MS_CLIENT_SECRET environment variable not set")
            raise RuntimeError("MS_CLIENT_SECRET environment variable not set")
        self.client_secret = client_secret
        self.logger.info(f"client_secret: {self.client_secret[0:4]}...")

        if not redirect_uri:
            self.logger.warning("MS_REDIRECT_URI environment variable not set")
            raise RuntimeError("MS_REDIRECT_URI environment variable not set")
        self.redirect_uri = redirect_uri
        self.logger.info(f"Redirect URI from OS Env: {self.redirect_uri}")
        self.logger.info(f"redirect_uri: {self.redirect_uri}")

        if not scopes:
            self.logger.warning("MS_SCOPES environment variable not set")
            raise RuntimeError("MS_SCOPES environment variable not set")
        self.logger.info(f"scopes: {scopes}")

        self.scopes = self._parse_scopes(scopes)
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.logger.info(f"Configured authority={self.authority}, redirect_uri={self.redirect_uri}, scopes={self.scopes}")

        self.cache = self._load_cache()
        try:
            self.msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
                token_cache=self.cache
            )
            self.logger.info("MSAL ConfidentialClientApplication initialized")
        except Exception as exc:
            self.logger.exception("Failed to initialize MSAL client: %s", exc)
            raise

        self.authorization_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.userinfo_endpoint = "https://graph.microsoft.com/v1.0/me"

    @staticmethod
    def _load_cache() -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    payload = f.read()
                    cache.deserialize(payload)
                logging.getLogger(__name__).debug("Loaded token cache from %s (bytes=%d)", CACHE_FILE, len(payload))
            else:
                logging.getLogger(__name__).debug("No token cache present at %s", CACHE_FILE)
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to load token cache: %s", exc)
        return cache

    @staticmethod
    def _parse_scopes(raw: Optional[str]) -> list[str]:
        """Parse MS_SCOPES from JSON array, comma-separated, or space-separated string.

        Falls back to standard defaults when unset/invalid.
        """
        defaults = ["openid", "profile", "offline_access", "User.Read"]
        if not raw:
            return defaults
        try:
            s = raw.strip()
            # JSON array style
            if s.startswith('['):
                import json as _json
                arr = _json.loads(s)
                vals = [str(x).strip() for x in arr if str(x).strip()]
                return vals or defaults
            # Comma or whitespace separated
            s = s.replace(',', ' ')
            vals = [p for p in s.split() if p]
            return vals or defaults
        except Exception:  # noqa
            return defaults

    def _save_cache(self):
        try:
            if self.cache.has_state_changed:
                data = self.cache.serialize()
                with open(CACHE_FILE, "w") as f:
                    f.write(data)
                self.logger.debug("Token cache saved to %s (bytes=%d)", CACHE_FILE, len(data))
        except Exception as exc:
            self.logger.warning("Failed to save token cache: %s", exc)

    @staticmethod
    def _redact(token: str | None) -> str:
        if not token:
            return "<none>"
        try:
            return f"len={len(token)}:{token[:8]}...{token[-6:]}"
        except Exception:  # noqa
            return "<redacted>"

    def get_auth_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        self.logger.info("Building authorization URL (state=%s)", state)
        try:
            # MSAL automatically injects reserved OIDC scopes. Do not include them explicitly.
            self.logger.info(f"Scopes = {self.scopes}")
            reserved = {"openid", "offline_access", "profile"}
            auth_scopes = [s for s in (self.scopes or []) if s not in reserved]
            if not auth_scopes:
                auth_scopes = ["User.Read"]
            # Allow caller to override redirect URI per-request (e.g., localhost)
            redirect = redirect_uri or self.redirect_uri
            url = self.msal_app.get_authorization_request_url(  # noqa
                scopes=auth_scopes,
                state=state,
                redirect_uri=redirect
            )
            self.logger.debug("Authorization URL generated: %s", url)
            return url
        except Exception as exc:
            self.logger.exception("Failed to build authorization URL: %s", exc)
            raise

    def exchange_code(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        self.logger.info("Exchanging authorization code for tokens")
        try:
            reserved = {"openid", "offline_access", "profile"}
            token_scopes = [s for s in (self.scopes or []) if s not in reserved] or ["User.Read"]
            redirect = redirect_uri or self.redirect_uri
            result = self.msal_app.acquire_token_by_authorization_code(  # noqa
                code,
                scopes=token_scopes,
                redirect_uri=redirect
            )
            self._save_cache()
        except Exception as exc:
            self.logger.exception("acquire_token_by_authorization_code failed: %s", exc)
            raise

        if "error" in result:
            self.logger.error("MSAL error: %s", result.get('error_description') or result.get('error'))
            raise Exception(f"MSAL error: {result.get('error_description') or result.get('error')}")

        # Log token meta with redaction
        self.logger.debug(
            "Token response received: access_token=%s, id_token=%s, expires_in=%s",
            self._redact(result.get('access_token')), self._redact(result.get('id_token')), result.get('expires_in')
        )
        return result

    def get_user_info(self, token_response: Dict[str, Any]) -> Dict[str, Any]:
        access_token = token_response.get("access_token")
        if not access_token:
            self.logger.error("No access token in token response")
            return {}
        headers = {"Authorization": f"Bearer {access_token}"}
        self.logger.info("Fetching user info from Graph: %s", self.userinfo_endpoint)
        try:
            resp = requests.get(self.userinfo_endpoint, headers=headers)
            self.logger.debug("Graph /me status=%s", getattr(resp, 'status_code', '?'))
            resp.raise_for_status()
            user_data = resp.json()
            self.logger.info(f"User data: {user_data}")
            out = {
                "id": user_data.get("id"),
                "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                "displayName": user_data.get("displayName")
            }
            self.logger.info("Graph user: id=%s email=%s displayName=%s", out.get('id'), out.get('email'), out.get('displayName'))
            return out
        except requests.exceptions.HTTPError as e:
            self.logger.error("User info HTTP error: %s, Response: %s", e, getattr(e.response, 'text', ''))
            return {}
        except Exception as e:
            self.logger.error("User info error: %s", e)
            return {}

    def get_access_token(self) -> Optional[Dict[str, Any]]:
        accounts = self.msal_app.get_accounts()
        self.logger.debug("Accounts in cache: %d", len(accounts or []))
        if accounts:
            self.logger.info("Attempting silent token acquisition")
            result = self.msal_app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                self.logger.info("Token acquired silently")
                self.logger.debug(
                    "Silent token: access_token=%s expires_in=%s",
                    self._redact(result.get('access_token')), result.get('expires_in')
                )
                return result
            self.logger.error(f"Token acquisition failed: {result.get('error_description')}")

        return None

    def make_entra_request(self, input_str: str) -> dict:
        try:
            input_data = json.loads(input_str)
            method = input_data["method"]
            path = input_data["path"]
            query_params = input_data.get("query_params", {})
            body = input_data.get("body", {})
        except (json.JSONDecodeError, KeyError) as e:
            return {"error": str(e)}

        self.logger.info("Entra API request: %s %s", method.upper(), path)
        token_response = self.get_access_token()
        if not token_response or "access_token" not in token_response:
            self.logger.error("No valid access token available for Entra API call")
            return {"error": "No valid access token"}

        url = f"https://graph.microsoft.com/beta/{path}"
        headers = {
            "Authorization": f"Bearer {token_response['access_token']}",
            "Content-Type": "application/json"
        }

        try:
            self.logger.debug("HTTP %s %s params=%s body=%s", method.upper(), url, query_params, body)
            response = requests.request(method.upper(), url, headers=headers, params=query_params, json=body)
            self.logger.info("Entra response status=%s", getattr(response, 'status_code', '?'))
            response.raise_for_status()
            payload = response.json() if response.status_code != 204 else {"message": "No content"}
            self.logger.debug("Entra response payload keys=%s", list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
            return payload
        except requests.exceptions.RequestException as e:
            self.logger.error("Entra request failed: %s | body=%s", e, getattr(e.response, 'text', ''))
            return {"error": str(e), "response": getattr(e.response, 'text', '')}

    def logout(self) -> bool:
        try:
            accounts = self.msal_app.get_accounts()
            self.logger.info("Logging out; accounts=%d", len(accounts or []))
            for account in accounts:
                self.logger.debug("Removing account: %s", getattr(account, 'username', '<unknown>'))
                self.msal_app.remove_account(account)
            self.logger.info("Successfully logged out")
            return True
        except Exception as e:
            self.logger.error("Logout error: %s", e)
            return False
