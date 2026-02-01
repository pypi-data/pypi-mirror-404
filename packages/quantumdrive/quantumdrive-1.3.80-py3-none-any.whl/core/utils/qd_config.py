"""
QuantumDrive Configuration Module

This module provides configuration handling for QuantumDrive. It accepts
configuration dictionaries from host applications (like Quantify) and
extracts the appropriate subsets for QuantumDrive and AgentForge components.

Configuration Namespaces:
- QD_* : QuantumDrive-specific settings
- AF_* : AgentForge settings (passed through to AgentForge)
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, SecretStr

logger = logging.getLogger(__name__)

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli  # Python 3.11+
    except ImportError:
        tomli = None  # type: ignore


class QDMicrosoftConfig(BaseModel):
    """Microsoft 365 / Entra ID configuration."""
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[SecretStr] = None
    redirect_uri: Optional[str] = None
    scopes: Optional[str] = None  # JSON array or comma-separated


class QDConfig(BaseModel):
    """
    QuantumDrive configuration object.
    
    This is the standard way to configure QuantumDrive components. Host applications
    (like Quantify) should create a QDConfig and pass it to QuantumDrive entry points.
    """
    # Microsoft 365 / SSO
    microsoft: QDMicrosoftConfig = Field(default_factory=QDMicrosoftConfig)
    
    # Flask settings (if using webapp)
    flask_debug: bool = False
    flask_port: int = 5000
    
    # ChromaDB settings (for Q Assistant)
    chroma_collection_name: str = "quantumdrive"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Data directory
    data_dir: Optional[str] = None
    
    # Raw config dict for passthrough to AgentForge
    raw_config: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_dict(cls, config: Dict[str, Any], prefix: str = "QD_") -> "QDConfig":
        """
        Create QDConfig from a flat dictionary with prefixed keys.
        
        This is the primary factory method for host applications like Quantify
        that load configuration from secrets backends and TOML files.
        
        Args:
            config: Flat dictionary with prefixed keys (e.g., QD_MS_TENANT_ID)
            prefix: Key prefix to strip (default: "QD_")
        
        Returns:
            QDConfig instance
        
        Example:
            config = {
                'QD_MS_TENANT_ID': '...',
                'QD_MS_CLIENT_ID': '...',
                'QD_MS_CLIENT_SECRET': '...',
                'AF_OPENAI_API_KEY': 'sk-...',
                'AF_LLM_PROVIDER': 'openai',
            }
            qd_config = QDConfig.from_dict(config)
        """
        def get(key: str, default=None):
            """Get value with or without prefix."""
            return config.get(f"{prefix}{key}") or config.get(key) or default
        
        def get_secret(key: str) -> Optional[SecretStr]:
            """Get value as SecretStr if present."""
            val = get(key)
            return SecretStr(val) if val else None
        
        return cls(
            microsoft=QDMicrosoftConfig(
                tenant_id=get("MS_TENANT_ID"),
                client_id=get("MS_CLIENT_ID"),
                client_secret=get_secret("MS_CLIENT_SECRET"),
                redirect_uri=get("MS_REDIRECT_URI"),
                scopes=get("MS_SCOPES"),
            ),
            flask_debug=str(get("FLASK_DEBUG", "false")).lower() in ("true", "1", "yes"),
            flask_port=int(get("FLASK_PORT", 5000)),
            chroma_collection_name=get("CHROMA_COLLECTION_NAME", "quantumdrive"),
            embedding_model_name=get("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
            data_dir=get("DATA_DIR"),
            raw_config=config,
        )

    @classmethod
    def from_env(cls) -> "QDConfig":
        """
        Create QDConfig from environment variables.
        
        This is for backward compatibility and standalone usage.
        """
        config = {k: v for k, v in os.environ.items()}
        return cls.from_dict(config, prefix="QD_")
    
    @classmethod
    def from_toml(cls, toml_path: Optional[str] = None) -> "QDConfig":
        """
        Create QDConfig from TOML file.
        
        Loads configuration from TOML file and merges with environment variables.
        Environment variables take precedence over TOML values.
        
        Args:
            toml_path: Path to TOML file. If None, searches for (in order):
                1. ./quantumdrive.toml (project root)
                2. ~/.config/quantumdrive/quantumdrive.toml (user config)
                3. quantumdrive/resources/default_quantumdrive.toml (built-in default)
        
        Returns:
            QDConfig instance
        """
        if tomli is None:
            logger.warning("tomli/tomllib not available; falling back to environment variables")
            return cls.from_env()
        
        # Determine TOML file path
        if toml_path is None:
            # Try project root first (for development)
            project_config = Path.cwd() / "quantumdrive.toml"
            if project_config.exists():
                toml_path = str(project_config)
                logger.info(f"Loading config from project root: {toml_path}")
            else:
                # Try user config directory
                user_config = Path.home() / ".config" / "quantumdrive" / "quantumdrive.toml"
                if user_config.exists():
                    toml_path = str(user_config)
                    logger.info(f"Loading config from user directory: {toml_path}")
                else:
                    # Fall back to default
                    default_config = Path(__file__).parent.parent.parent / "resources" / "default_quantumdrive.toml"
                    if default_config.exists():
                        toml_path = str(default_config)
                        logger.info(f"Loading config from default file: {toml_path}")
                    else:
                        logger.warning("No TOML config found; using environment variables only")
                        return cls.from_env()
        
        # Load TOML file
        try:
            with open(toml_path, "rb") as f:
                toml_data = tomli.load(f)
            logger.debug(f"Loaded TOML config from {toml_path}")
        except Exception as e:
            logger.error(f"Failed to load TOML file {toml_path}: {e}")
            return cls.from_env()
        
        # Flatten TOML structure to match expected format
        flat_config = cls._flatten_toml(toml_data)
        
        # Merge with environment variables (env vars take precedence)
        for key, value in os.environ.items():
            flat_config[key] = value
        
        return cls.from_dict(flat_config, prefix="QD_")
    
    @staticmethod
    def _flatten_toml(data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """
        Flatten nested TOML structure to flat dictionary with prefixes.
        
        Example:
            {"MICROSOFT": {"TENANT_ID": "..."}} -> {"QD_MS_TENANT_ID": "..."}
            {"AF_LLM": {"PROVIDER": "openai"}} -> {"AF_LLM_PROVIDER": "openai"}
        """
        flat = {}
        
        for key, value in data.items():
            # Build the full key
            if parent_key:
                # Handle special cases for section names
                if parent_key == "MICROSOFT":
                    full_key = f"QD_MS_{key}"
                elif parent_key == "FLASK":
                    full_key = f"QD_FLASK_{key}"
                elif parent_key == "CHROMA":
                    full_key = f"QD_CHROMA_{key}"
                elif parent_key == "EMBEDDING":
                    full_key = f"QD_EMBEDDING_{key}"
                elif parent_key == "LOGGING":
                    full_key = f"QD_LOG_{key}"
                elif parent_key.startswith("AF_"):
                    # AgentForge sections
                    section = parent_key[3:]  # Remove AF_ prefix
                    if section in ("LLM", "PATHS", "VECTORSTORE", "MILVUS", "CHROMA", "FAISS", "KGRAPH", "EMBEDDING", "LOGGING", "ORCHESTRATOR"):
                        full_key = f"AF_{section}_{key}"
                    else:
                        full_key = f"{parent_key}_{key}"
                else:
                    full_key = f"QD_{key}"
            else:
                # Top-level keys
                if key in ("DATA_DIR",):
                    full_key = f"QD_{key}"
                else:
                    full_key = key
            
            # Recursively flatten nested dicts
            if isinstance(value, dict):
                flat.update(QDConfig._flatten_toml(value, full_key))
            else:
                flat[full_key] = value
        
        return flat
    
    @classmethod
    def from_legacy_config(cls) -> "QDConfig":
        """
        Create QDConfig from legacy configuration sources.
        
        This method provides backward compatibility by loading from:
        1. TOML files (user config or default)
        2. Environment variables (override TOML)
        
        This is the recommended method for standalone QuantumDrive usage.
        """
        return cls.from_toml()

    def get_af_config_dict(self) -> Dict[str, Any]:
        """
        Extract AgentForge configuration from the raw config.
        
        Returns a dictionary with AF_* prefixed keys that can be passed
        to AgentConfig.from_dict().
        """
        return {k: v for k, v in self.raw_config.items() if k.startswith("AF_")}

    def get_ms_tenant_id(self) -> Optional[str]:
        """Get Microsoft tenant ID."""
        return self.microsoft.tenant_id or os.getenv("MS_TENANT_ID")
    
    def get_ms_client_id(self) -> Optional[str]:
        """Get Microsoft client ID."""
        return self.microsoft.client_id or os.getenv("MS_CLIENT_ID")
    
    def get_ms_client_secret(self) -> Optional[str]:
        """Get Microsoft client secret."""
        if self.microsoft.client_secret:
            return self.microsoft.client_secret.get_secret_value()
        return os.getenv("MS_CLIENT_SECRET")
    
    def get_ms_redirect_uri(self) -> Optional[str]:
        """Get Microsoft redirect URI."""
        return self.microsoft.redirect_uri or os.getenv("MS_REDIRECT_URI")
    
    def get_ms_scopes(self) -> Optional[str]:
        """Get Microsoft scopes."""
        return self.microsoft.scopes or os.getenv("MS_SCOPES")
