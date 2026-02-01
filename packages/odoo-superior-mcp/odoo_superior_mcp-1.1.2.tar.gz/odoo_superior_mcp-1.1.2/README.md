
# Odoo Superior MCP

![demo.gif](demo.gif)

<div align="center">

![Odoo Superior MCP Logo](https://img.shields.io/badge/Odoo%20Superior%20MCP-brightgreen?style=for-the-badge&logo=odoo)

[![PyPI version](https://img.shields.io/badge/pypi-v1.1.2-blue.svg)](https://pypi.org/project/odoo-superior-mcp/)
[![Python Versions](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/odoo-superior-mcp/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Enhanced Model Context Protocol (MCP) server for Odoo ERP with advanced tools for sales, purchases, inventory and accounting**

Based on `odoo-mcp-enhanced` but with up-to-date libraries, using Python 3.12, and improved logging and configuration options.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Tools Reference](#-tools-reference)
- [Resources Reference](#-resources-reference)
- [Prompts](#-prompts)
- [Claude Desktop Integration](#-claude-desktop-integration)
- [License](#-license)

---

## 🔍 Overview

Odoo Superior MCP is a comprehensive implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for Odoo ERP systems. It provides a bridge between large language models like Claude and your Odoo instance, enabling AI assistants to interact directly with your business data and processes.

This extended version enhances the original MCP-Odoo implementation with advanced tools and resources for sales, purchases, inventory management, and accounting, making it a powerful solution for AI-assisted business operations.

---

## ✨ Features

### Core Capabilities
- **Seamless Odoo Integration**: Connect directly to your Odoo instance via XML-RPC
- **Comprehensive Data Access**: Query and manipulate data across all Odoo modules
- **Modular Architecture**: Easily extensible with new tools and resources
- **Robust Error Handling**: Clear error messages and validation for reliable operation

### Business Domain Support
- **Sales Management**: Order tracking, customer insights, and performance analysis
- **Purchase Management**: Supplier management, order processing, and performance metrics
- **Inventory Management**: Stock monitoring, inventory adjustments, and turnover analysis
- **Accounting**: Financial reporting, journal entries, and ratio analysis

### Advanced Functionality
- **Analytical Tools**: Business intelligence capabilities across all domains
- **Specialized Prompts**: Pre-configured prompts for common business scenarios
- **Resource URIs**: Standardized access to Odoo data through URI patterns
- **Performance Optimization**: Caching and efficient data retrieval

---

## 📦 Installation

### Using pip

```bash
pip install odoo-superior-mcp
```

### Using a pre-built Docker image

```bash
docker pull nitram509/odoo-superior-mcp:latest
docker run -p 8081:8081 \
   -e ODOO_URL=http://your-odoo-instance.com \
   -e ODOO_DB=your_database \
   -e ODOO_USERNAME=your_username \
   -e ODOO_PASSWORD=your_password \
   -e ODOO_TIMEOUT="10" \
   -e ODOO_VERIFY_SSL="0" \
   nitram509/odoo-superior-mcp:latest
```

## 🚀 Usage

### Running the Server

```bash
# Using the module
python -m odoo_mcp
```

### Example Interactions

```
# Sales Analysis
Using the Odoo MCP, analyze our sales performance for the last quarter and identify our top-selling products.

# Inventory Check
Check the current stock levels for product XYZ across all warehouses.

# Financial Analysis
Calculate our current liquidity and profitability ratios based on the latest financial data.

# Customer Insights
Provide insights on customer ABC's purchase history and payment patterns.
```

---

## 🤖 Claude Desktop Integration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your_database",
        "ODOO_USERNAME": "your_username",
        "ODOO_PASSWORD": "your_password"
      }
    }
  }
}
```

---

## 🛠️ Tools Reference

### Sales Tools

| Tool | Description |
|------|-------------|
| `search_sales_orders` | Search for sales orders with advanced filtering |
| `create_sales_order` | Create a new sales order |
| `analyze_sales_performance` | Analyze sales performance by period, product, or customer |
| `get_customer_insights` | Get detailed insights about a specific customer |

### Purchase Tools

| Tool | Description |
|------|-------------|
| `search_purchase_orders` | Search for purchase orders with advanced filtering |
| `create_purchase_order` | Create a new purchase order |
| `analyze_supplier_performance` | Analyze supplier performance metrics |

### Inventory Tools

| Tool | Description |
|------|-------------|
| `check_product_availability` | Check stock availability for products |
| `create_inventory_adjustment` | Create inventory adjustment entries |
| `analyze_inventory_turnover` | Calculate and analyze inventory turnover metrics |

### Accounting Tools

| Tool | Description |
|------|-------------|
| `search_journal_entries` | Search for accounting journal entries |
| `create_journal_entry` | Create a new journal entry |
| `analyze_financial_ratios` | Calculate key financial ratios |

---

## 🔗 Resources Reference

### Sales Resources

| URI | Description |
|-----|-------------|
| `odoo://sales/orders` | List sales orders |
| `odoo://sales/order/{order_id}` | Get details of a specific sales order |
| `odoo://sales/products` | List sellable products |
| `odoo://sales/customers` | List customers |

### Purchase Resources

| URI | Description |
|-----|-------------|
| `odoo://purchase/orders` | List purchase orders |
| `odoo://purchase/order/{order_id}` | Get details of a specific purchase order |
| `odoo://purchase/suppliers` | List suppliers |

### Inventory Resources

| URI | Description |
|-----|-------------|
| `odoo://inventory/products` | List products in inventory |
| `odoo://inventory/stock/{location_id}` | Get stock levels at a specific location |
| `odoo://inventory/movements` | List inventory movements |

### Accounting Resources

| URI | Description |
|-----|-------------|
| `odoo://accounting/accounts` | List accounting accounts |
| `odoo://accounting/journal_entries` | List journal entries |
| `odoo://accounting/reports/{report_type}` | Get financial reports |

---

## 💬 Prompts

Odoo Superior MCP includes specialized prompts for different business scenarios:

### Sales Analysis Prompts
- Sales trend analysis
- Customer segmentation
- Product performance evaluation
- Sales team performance

### Inventory Management Prompts
- Stock optimization
- Reordering suggestions
- Warehouse efficiency analysis
- Product movement patterns

### Human Resources Prompts
- Staff planning
- Scheduling optimization
- Performance evaluation
- Resource allocation

### Financial Analysis Prompts
- Ratio interpretation
- Cash flow analysis
- Budget variance analysis
- Financial health assessment

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

This repo is extended from [mcp-odoo](https://github.com/tuanle96/mcp-odoo) - [Lê Anh Tuấn](https://github.com/tuanle96)

---

<div align="center">

**Odoo Superior MCP** - Empowering AI assistants with comprehensive Odoo ERP capabilities

</div>
