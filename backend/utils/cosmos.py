import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# --------------------------------------------------
# Load .env
# --------------------------------------------------
ROOT_ENV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..", ".env")
)

print("Loading .env from:", ROOT_ENV_PATH)
load_dotenv(ROOT_ENV_PATH)

# --------------------------------------------------
# Environment Variables
# --------------------------------------------------
COSMOS_CONN_READ = os.getenv("COSMOS_CONN_READ")
COSMOS_CONN_WRITE = os.getenv("COSMOS_CONN_WRITE")
COSMOS_DB = os.getenv("COSMOS_DB", "llmops-data")

if not COSMOS_CONN_READ:
    raise RuntimeError("❌ COSMOS_CONN_READ missing in .env")

if not COSMOS_CONN_WRITE:
    raise RuntimeError("❌ COSMOS_CONN_WRITE missing in .env")

# Clean connection strings (important)
COSMOS_CONN_READ = COSMOS_CONN_READ.strip().strip('"').strip("'")
COSMOS_CONN_WRITE = COSMOS_CONN_WRITE.strip().strip('"').strip("'")

# --------------------------------------------------
# Cosmos Clients
# --------------------------------------------------
cosmos_client_read = CosmosClient.from_connection_string(COSMOS_CONN_READ)
cosmos_client_write = CosmosClient.from_connection_string(COSMOS_CONN_WRITE)

# --------------------------------------------------
# Database Clients
# --------------------------------------------------
database_read = cosmos_client_read.get_database_client(COSMOS_DB)
database_write = cosmos_client_write.get_database_client(COSMOS_DB)

# --------------------------------------------------
# Container Clients
# --------------------------------------------------
# 🔹 READ-ONLY containers (GET endpoints)
traces_container = database_read.get_container_client("traces")
evaluations_container = database_read.get_container_client("evaluations")
evaluators_container = database_read.get_container_client("evaluators")
metrics_container = database_read.get_container_client("metrics")

# 🔹 WRITE-ENABLED containers (POST / PUT / DELETE)
templates_container = database_write.get_container_client("templates")

print("✅ Cosmos DB initialized")
print("   Database:", COSMOS_DB)
print("   READ client: enabled")
print("   WRITE client: enabled")
