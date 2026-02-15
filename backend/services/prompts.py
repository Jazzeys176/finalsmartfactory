"""
Prompt Service - MLflow-Only Implementation
Uses MLflow Prompt Registry as the single source of truth.
Supports Local MLflow, Azure ML MLflow, and DagsHub.
Uses Azure Key Vault for secure configuration.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import mlflow
from mlflow import MlflowClient
from pydantic import BaseModel

# Azure Key Vault
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Optional local dev
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# 🔐 LOAD CONFIGURATION (KEY VAULT OR LOCAL)
# ============================================================

def load_configuration():
    """
    Load MLflow configuration from Azure Key Vault if KEYVAULT_URL is set.
    Otherwise fallback to .env for local development.
    """

    keyvault_url = os.getenv("KEYVAULT_URL")

    if keyvault_url:
        logger.info("Loading secrets from Azure Key Vault")

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=keyvault_url, credential=credential)

        def get_secret(name):
            try:
                return client.get_secret(name).value
            except Exception as e:
                logger.error(f"Failed to fetch secret '{name}': {e}")
                return None

        # 🔥 Map your exact Key Vault names to MLflow env vars
        os.environ["MLFLOW_TRACKING_URI"] = get_secret("MLFLOW-TRACKING-URI") or ""
        os.environ["MLFLOW_TRACKING_USERNAME"] = get_secret("MLFLOW-TRACKING-USERNAME") or ""
        os.environ["MLFLOW_TRACKING_PASSWORD"] = get_secret("MLFLOW-TRACKING-PASSWORD") or ""

    else:
        logger.info("KEYVAULT_URL not set — using local .env")
        if load_dotenv:
            load_dotenv()


# Load config before MLflow initializes
load_configuration()


# ============================================================
# 🔧 AUTH SETUP
# ============================================================

def setup_azure_ml_auth():
    try:
        import azureml.mlflow
        logger.info("Azure ML MLflow plugin registered")
        return True
    except ImportError:
        logger.error("Install azureml-mlflow for Azure ML support")
        return False


def setup_dagshub_auth():
    username = os.getenv("MLFLOW_TRACKING_USERNAME")
    password = os.getenv("MLFLOW_TRACKING_PASSWORD")

    if not username or not password:
        logger.error("DagsHub requires MLFLOW_TRACKING_USERNAME and MLFLOW_TRACKING_PASSWORD")
        return False

    os.environ["MLFLOW_TRACKING_USERNAME"] = username
    os.environ["MLFLOW_TRACKING_PASSWORD"] = password
    return True


# ============================================================
# 📦 DATA MODEL
# ============================================================

class PromptVersion(BaseModel):
    id: str
    name: str
    version: int
    content: str
    description: str
    variables: List[str]
    tags: List[str]
    model_parameters: Dict
    environment: str
    author: str
    created_at: datetime
    mlflow_run_id: Optional[str] = None


# ============================================================
# 🚀 PROMPT SERVICE
# ============================================================

class PromptService:

    def __init__(self):

        self.mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

        if not self.mlflow_tracking_uri:
            raise RuntimeError("MLFLOW_TRACKING_URI not configured")

        # Detect tracking backend
        if self.mlflow_tracking_uri.startswith("azureml://"):
            if not setup_azure_ml_auth():
                raise RuntimeError("Azure ML authentication failed")

        elif "dagshub.com" in self.mlflow_tracking_uri:
            if not setup_dagshub_auth():
                raise RuntimeError("DagsHub authentication failed")

        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        self.client = MlflowClient(tracking_uri=self.mlflow_tracking_uri)

        logger.info(f"MLflow connected to: {self.mlflow_tracking_uri}")

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _sanitize_name_for_mlflow(self, name: str) -> str:
        name = name.lower().replace(" ", "-")
        name = re.sub(r'[^a-zA-Z0-9\-_.]', '', name)
        return name.strip('-')

    def _extract_variables(self, content: str) -> List[str]:
        pattern = r'\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}'
        return list(set(re.findall(pattern, content)))

    def _get_latest_version(self, name: str) -> int:
        try:
            prompts = mlflow.genai.search_prompts(filter_string=f"name='{name}'")
            if prompts and hasattr(prompts[0], "latest_version"):
                return int(prompts[0].latest_version)
        except:
            pass

        version = 1
        while True:
            try:
                mlflow.genai.load_prompt(f"prompts:/{name}/{version + 1}")
                version += 1
            except:
                break
        return version

    # ========================================================
    # PUBLIC METHODS
    # ========================================================

    def create_prompt_version(
        self,
        name: str,
        content: str,
        tags: List[str] = None,
        description: str = "",
        model_parameters: Dict = None
    ) -> Dict:

        tags = tags or []
        model_parameters = model_parameters or {}

        mlflow_name = self._sanitize_name_for_mlflow(name)
        variables = self._extract_variables(content)

        mlflow_tags = {
            "description": description,
            "display_name": name,
            **{k: str(v) for k, v in model_parameters.items()},
            **{f"tag_{t}": "true" for t in tags}
        }

        info = mlflow.genai.register_prompt(
            name=mlflow_name,
            template=content,
            tags=mlflow_tags
        )

        version = int(getattr(info, "version", 1))

        return {
            "id": f"{mlflow_name}-v{version}",
            "name": name,
            "version": version,
            "variables": variables,
            "description": description
        }

    def list_prompts(self) -> List[Dict]:
        prompts = mlflow.genai.search_prompts()
        results = []

        for p in prompts:
            name = p.name
            version = self._get_latest_version(name)
            prompt_obj = mlflow.genai.load_prompt(f"prompts:/{name}/{version}")

            template = getattr(prompt_obj, "template", "")
            variables = self._extract_variables(template)

            results.append({
                "id": f"{name}-v{version}",
                "name": name,
                "version": version,
                "content": template,
                "variables": variables
            })

        return results

    def get_prompt_by_name(self, name: str, version: Optional[int] = None) -> Optional[Dict]:

        mlflow_name = self._sanitize_name_for_mlflow(name)
        version = version or self._get_latest_version(mlflow_name)

        try:
            prompt_obj = mlflow.genai.load_prompt(f"prompts:/{mlflow_name}/{version}")
        except:
            return None

        template = getattr(prompt_obj, "template", "")
        variables = self._extract_variables(template)

        return {
            "id": f"{mlflow_name}-v{version}",
            "name": name,
            "version": version,
            "content": template,
            "variables": variables,
            "created_at": datetime.utcnow().isoformat()
        }

    def promote_version(self, prompt_name: str, version: int, target_env: str) -> bool:

        mlflow_name = self._sanitize_name_for_mlflow(prompt_name)

        mlflow.genai.set_prompt_alias(
            name=mlflow_name,
            alias=target_env,
            version=version
        )

        logger.info(f"Promoted '{mlflow_name}' v{version} to '{target_env}'")
        return True


# ============================================================
# SINGLETON
# ============================================================

prompt_service = PromptService()
