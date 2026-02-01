import json
import logging
import os

from odoo_mcp.odoo_client import OdooClient, OdooConfig


def load_config_from_file() -> OdooConfig:
    config_files_to_check = [
        "odoo_config.json",
        os.path.expanduser(os.path.join("~", ".config", "odoo", "config.json")),
        os.path.expanduser(os.path.join("~", ".odoo_config.json")),
    ]

    for path in config_files_to_check:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            with open(expanded_path, "r") as f:
                return json.load(f)

    raise FileNotFoundError(
        f"No Odoo configuration found. "
        f"Either create environment variables OR place a config file "
        f"in one of these locations: {config_files_to_check}"
    )


def get_odoo_client() -> OdooClient:
    """Get a configured Odoo client instance"""
    if all(
        var in os.environ
        for var in ["ODOO_URL", "ODOO_DB", "ODOO_USERNAME", "ODOO_PASSWORD"]
    ):
        config = OdooConfig(
            os.environ["ODOO_URL"],
            os.environ["ODOO_DB"],
            os.environ["ODOO_USERNAME"],
            os.environ["ODOO_PASSWORD"],
        )
    else:
        config = load_config_from_file()

    # Get additional options from environment variables
    config.timeout = int(
        os.environ.get("ODOO_TIMEOUT", "30")
    )  # Increase default timeout to 30 seconds
    config.verify_ssl = os.environ.get("ODOO_VERIFY_SSL", "1").lower() in [
        "1",
        "true",
        "yes",
    ]

    logging.debug("Odoo client configuration:")
    logging.debug(f"  URL: {config.url}")
    logging.debug(f"  Database: {config.db}")
    logging.debug(f"  Username: {config.username}")
    logging.debug(f"  Timeout: {config.timeout}s")
    logging.debug(f"  Verify SSL: {config.verify_ssl}")

    return OdooClient(config)
