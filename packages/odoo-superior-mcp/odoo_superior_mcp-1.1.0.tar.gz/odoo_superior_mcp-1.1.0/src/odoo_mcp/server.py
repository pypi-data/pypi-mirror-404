import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from fastmcp import FastMCP, Context

from .odoo_client import OdooClient
from .odoo_config import get_odoo_client
from .prompts import register_all_prompts
from .resources import register_all_resources
from .tools_accounting import register_accounting_tools
from .tools_employee import search_employee
from .tools_holiday import search_holidays
from .tools_inventory import register_inventory_tools
from .tools_purchase import register_purchase_tools
from .tools_sales import register_sales_tools


@dataclass
class AppContext:
    odoo_client: OdooClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Application lifespan for initialization and cleanup
    """
    # Initialize Odoo client on startup
    odoo_client = get_odoo_client()

    try:
        yield AppContext(odoo_client=odoo_client)
    finally:
        # No cleanup needed for Odoo client
        pass


# Create MCP server
mcp = FastMCP(
    "Odoo MCP Server",
    lifespan=app_lifespan,
)


# ----- Pydantic models for type safety -----

# TODO: ist not used?
# class DomainCondition(BaseModel):
#     """A single condition in a search domain"""
#
#     field: str = Field(description="Field name to search")
#     operator: str = Field(
#         description="Operator (e.g., '=', '!=', '>', '<', 'in', 'not in', 'like', 'ilike')"
#     )
#     value: Any = Field(description="Value to compare against")
#
#     def to_tuple(self) -> List:
#         """Convert to Odoo domain condition tuple"""
#         return [self.field, self.operator, self.value]

# TODO: ist not used?
# class SearchDomain(BaseModel):
#     """Search domain for Odoo models"""
#
#     conditions: List[DomainCondition] = Field(
#         default_factory=list,
#         description="List of conditions for searching. All conditions are combined with AND operator.",
#     )
#
#     def to_domain_list(self) -> List[List]:
#         """Convert to Odoo domain list format"""
#         return [condition.to_tuple() for condition in self.conditions]


@mcp.tool(description="Execute a custom method on an Odoo model")
def execute_method(
    ctx: Context,
    model: str,
    method: str,
    args: List = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a custom method on an Odoo model

    Parameters:
        model: The model name (e.g., 'res.partner')
        method: Method name to execute
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - result: Result of the method (if success)
        - error: Error message (if failure)
    """
    odoo = ctx.request_context.lifespan_context.odoo_client
    args = args or []
    kwargs = kwargs or {}

    try:
        # Special handling for search methods like search, search_count, search_read
        search_methods = ["search", "search_count", "search_read"]
        if method in search_methods and args:
            # Search methods usually have domain as the first parameter
            # args: [[domain], limit, offset, ...] or [domain, limit, offset, ...]
            normalized_args = list(
                args
            )  # Create a copy to avoid affecting the original args

            if len(normalized_args) > 0:
                # Process domain in args[0]
                domain = normalized_args[0]
                domain_list = []

                # Check if domain is wrapped unnecessarily ([domain] instead of domain)
                if (
                    isinstance(domain, list)
                    and len(domain) == 1
                    and isinstance(domain[0], list)
                ):
                    # Case [[domain]] - unwrap to [domain]
                    domain = domain[0]

                # Normalize domain similar to search_records function
                if domain is None:
                    domain_list = []
                elif isinstance(domain, dict):
                    if "conditions" in domain:
                        # Object format
                        conditions = domain.get("conditions", [])
                        domain_list = []
                        for cond in conditions:
                            if isinstance(cond, dict) and all(
                                k in cond for k in ["field", "operator", "value"]
                            ):
                                domain_list.append(
                                    [cond["field"], cond["operator"], cond["value"]]
                                )
                elif isinstance(domain, list):
                    # List format
                    if not domain:
                        domain_list = []
                    elif all(isinstance(item, list) for item in domain) or any(
                        item in ["&", "|", "!"] for item in domain
                    ):
                        domain_list = domain
                    elif len(domain) >= 3 and isinstance(domain[0], str):
                        # Case [field, operator, value] (not [[field, operator, value]])
                        domain_list = [domain]
                elif isinstance(domain, str):
                    # String format (JSON)
                    try:
                        parsed_domain = json.loads(domain)
                        if (
                            isinstance(parsed_domain, dict)
                            and "conditions" in parsed_domain
                        ):
                            conditions = parsed_domain.get("conditions", [])
                            domain_list = []
                            for cond in conditions:
                                if isinstance(cond, dict) and all(
                                    k in cond for k in ["field", "operator", "value"]
                                ):
                                    domain_list.append(
                                        [cond["field"], cond["operator"], cond["value"]]
                                    )
                        elif isinstance(parsed_domain, list):
                            domain_list = parsed_domain
                    except json.JSONDecodeError:
                        try:
                            import ast

                            parsed_domain = ast.literal_eval(domain)
                            if isinstance(parsed_domain, list):
                                domain_list = parsed_domain
                        except:
                            domain_list = []

                # Xác thực domain_list
                if domain_list:
                    valid_conditions = []
                    for cond in domain_list:
                        if isinstance(cond, str) and cond in ["&", "|", "!"]:
                            valid_conditions.append(cond)
                            continue

                        if (
                            isinstance(cond, list)
                            and len(cond) == 3
                            and isinstance(cond[0], str)
                            and isinstance(cond[1], str)
                        ):
                            valid_conditions.append(cond)

                    domain_list = valid_conditions

                # Cập nhật args với domain đã chuẩn hóa
                normalized_args[0] = domain_list
                args = normalized_args

                # Log for debugging
                logging.info(
                    f"Executing {method} with normalized domain: {domain_list}"
                )

        result = odoo.execute_method(model, method, *args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        logging.warning(
            f"execute_method(model={model}, method={method}, args={args}, kwargs={kwargs})",
            e,
        )
        return {"success": False, "error": str(e)}


# Registrar todas las extensiones
register_all_prompts(mcp)
register_all_resources(mcp)
register_sales_tools(mcp)
register_purchase_tools(mcp)
register_inventory_tools(mcp)
register_accounting_tools(mcp)

mcp.tool(search_employee, description="Search for employees by name")
mcp.tool(search_holidays, description="Search for holidays within a date range")
