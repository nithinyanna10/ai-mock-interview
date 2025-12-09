"""
Run script for FastAPI server
"""

import uvicorn
import logging
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Load config for port
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8080)
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        host = "0.0.0.0"
        port = 8080
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run("api:app", host=host, port=port, reload=True)

