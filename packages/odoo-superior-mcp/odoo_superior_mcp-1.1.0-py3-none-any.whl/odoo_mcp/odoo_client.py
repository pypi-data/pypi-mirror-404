"""
Odoo XML-RPC client for MCP server integration
"""

import logging
import re
import urllib.parse
import xmlrpc.client
from dataclasses import dataclass
from typing import Dict, Optional

from odoo_mcp.transport import RedirectTransport


@dataclass(init=False)
class OdooConfig:
    url: str
    db: str
    username: str
    password: str
    timeout: Optional[int] = 30
    verify_ssl: Optional[bool] = True

    def __init__(self, url, db, username, password, timeout=None, verify_ssl=None):
        super().__init__()
        self.db = db
        self.url = url
        self.username = username
        self.password = password
        if timeout is not None:
            self.timeout = timeout
        if verify_ssl is not None:
            self.verify_ssl = verify_ssl


class OdooClient:
    """Client for interacting with Odoo via XML-RPC"""

    def __init__(self, config: OdooConfig):
        # Ensure URL has a protocol
        if not re.match(r"^https?://", config.url):
            config.url = f"http://{config.url}"

        # Remove trailing slash from URL if present
        url = config.url.rstrip("/")

        self.url = url
        self.db = config.db
        self.username = config.username
        self.password = config.password
        self.uid = None

        # Set timeout and SSL verification
        self.timeout = config.timeout
        self.verify_ssl = config.verify_ssl

        # Setup connections
        self._common = None
        self._models = None

        # Parse hostname for logging
        parsed_url = urllib.parse.urlparse(self.url)
        self.hostname = parsed_url.netloc

        self._connect()

    def _connect(self):
        """Initialize the XML-RPC connection and authenticate"""
        # Tạo transport với timeout phù hợp
        is_https = self.url.startswith("https")
        transport = RedirectTransport(
            timeout=self.timeout, use_https=is_https, verify_ssl=self.verify_ssl
        )

        self._common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", transport=transport
        )
        self._models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", transport=transport
        )

        # Xác thực và lấy user ID
        logging.info(
            f"Authenticating with database: {self.db}, username: {self.username}"
        )
        logging.info(
            f"Making request to {self.hostname}/xmlrpc/2/common "
            f"| Timeout: {self.timeout}s, Verify SSL: {self.verify_ssl}"
        )
        self.uid = self._common.authenticate(self.db, self.username, self.password, {})
        if not self.uid:
            raise ValueError("Authentication failed: Invalid username or password")

    def execute_method(self, odoo_model, method, *args, **kwargs):
        """Execute an arbitrary method on a model"""
        return self._models.execute_kw(
            self.db, self.uid, self.password, odoo_model, method, args, kwargs
        )

    def get_models(self) -> Dict[str, any]:
        """Get a list of all available models in the system"""
        try:
            # First search for model IDs
            model_ids = self.execute_method("ir.model", "search", [])
        except Exception as e:
            logging.error("Error search for model IDs", e)
            return {
                "model_names": [],
                "models_details": {},
                "error": "Error search for model IDs",
            }

        if not model_ids:
            return {
                "model_names": [],
                "models_details": {},
                "error": "No models found",
            }

        try:
            # Then read the model data with only the most basic fields
            # that are guaranteed to exist in all Odoo versions
            result = self.execute_method(
                "ir.model", "read", model_ids, ["model", "name"]
            )

            # Extract and sort model names alphabetically
            models = sorted([rec["model"] for rec in result])

            # For more detailed information, include the full records
            models_info = {
                "model_names": models,
                "models_details": {
                    rec["model"]: {"name": rec.get("name", "")} for rec in result
                },
            }

            return models_info
        except Exception as e:
            logging.error("get_models()", e)
            return {"model_names": [], "models_details": {}, "error": str(e)}

    def get_model_info(self, model_name):
        """
        Get information about a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary with model information

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> info = client.get_model_info('res.partner')
            >>> print(info['name'])
            'Contact'
        """
        try:
            result = self.execute_method(
                "ir.model",
                "search_read",
                [("model", "=", model_name)],
                {"fields": ["name", "model"]},
            )

            if not result:
                return {"error": f"Model {model_name} not found"}

            return result[0]
        except Exception as e:
            logging.error(f"get_model_info(model_name={model_name})")
            return {"error": str(e)}

    def get_model_fields(self, model_name):
        """
        Get field definitions for a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary mapping field names to their definitions

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> fields = client.get_model_fields('res.partner')
            >>> print(fields['name']['type'])
            'char'
        """
        try:
            fields = self.execute_method(model_name, "fields_get")
            return fields
        except Exception as e:
            logging.error(f"get_model_fields(model_name={model_name})", e)
            return {"error": str(e)}

    def search_read(
        self, model_name, domain, fields=None, offset=None, limit=None, order=None
    ):
        """
        Search for records and read their data in a single call

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            domain: Search domain (e.g., [('is_company', '=', True)])
            fields: List of field names to return (None for all)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Sorting criteria (e.g., 'name ASC, id DESC')

        Returns:
            List of dictionaries with the matching records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.search_read('res.partner', [('is_company', '=', True)], limit=5)
            >>> print(len(records))
            5
        """
        try:
            kwargs = {}
            if offset:
                kwargs["offset"] = offset
            if fields is not None:
                kwargs["fields"] = fields
            if limit is not None:
                kwargs["limit"] = limit
            if order is not None:
                kwargs["order"] = order

            result = self.execute_method(model_name, "search_read", domain, **kwargs)
            return result
        except Exception as e:
            logging.error("Error in search_read", e)
            return []

    def read_records(self, model_name, ids, fields=None):
        """
        Read data of records by IDs

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            ids: List of record IDs to read
            fields: List of field names to return (None for all)

        Returns:
            List of dictionaries with the requested records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.read_records('res.partner', [1])
            >>> print(records[0]['name'])
            'YourCompany'
        """
        try:
            kwargs = {}
            if fields is not None:
                kwargs["fields"] = fields

            result = self.execute_method(model_name, "read", ids, **kwargs)
            return result
        except Exception as e:
            logging.error(
                f"read_records(model_name={model_name}, ids={ids}, fields={fields})", e
            )
            return []
