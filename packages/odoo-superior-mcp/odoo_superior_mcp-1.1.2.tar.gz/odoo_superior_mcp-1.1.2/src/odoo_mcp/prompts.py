from fastmcp import FastMCP


def register_all_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        sales_analysis_prompt,
        name="sales_analysis",
        description="Analyze sales for a specific period and provide key insights",
    )
    mcp.prompt(
        purchase_analysis_prompt,
        name="purchase_analysis",
        description="Analyze purchase orders and supplier performance",
    )
    mcp.prompt(
        inventory_management_prompt,
        name="inventory_management",
        description="Analyzes inventory status and provides recommendations",
    )
    mcp.prompt(
        financial_analysis_prompt,
        name="financial_analysis",
        description="Perform a basic financial analysis",
    )


def sales_analysis_prompt() -> str:
    return """
    Analiza las ventas del último {period} (ej. 'month', 'quarter', 'year') y proporciona insights sobre:
    - Productos más vendidos (top 5)
    - Clientes principales (top 5)
    - Tendencias de ventas (comparación con período anterior si es posible)
    - Rendimiento por vendedor (si aplica)
    - Recomendaciones accionables para mejorar las ventas.
    
    Utiliza las herramientas disponibles como 'search_sales_orders' y 'execute_method' para obtener los datos necesarios de Odoo.
    """


def purchase_analysis_prompt() -> str:
    return """
    Analiza las compras realizadas en el último {period} (ej. 'month', 'quarter', 'year') y proporciona insights sobre:
    - Productos más comprados (top 5)
    - Proveedores principales (top 5 por volumen/valor)
    - Tendencias de compras
    - Plazos de entrega promedio por proveedor
    - Recomendaciones para optimizar compras o negociar con proveedores.
    
    Utiliza las herramientas disponibles como 'search_purchase_orders' para obtener los datos necesarios de Odoo.
    """


def inventory_management_prompt() -> str:
    return """
    Analiza el estado actual del inventario y proporciona información sobre:
    - Productos con bajo stock (por debajo del mínimo si está configurado)
    - Productos con exceso de stock (por encima del máximo o sin movimiento)
    - Valoración actual del inventario
    - Rotación de inventario para productos clave
    - Recomendaciones para ajustes, reabastecimiento o liquidación de stock.
    
    Utiliza las herramientas disponibles como 'check_product_availability' y 'analyze_inventory_turnover' para obtener los datos necesarios de Odoo.
    """


def financial_analysis_prompt() -> str:
    return """
    Realiza un análisis financiero para el período {period} (ej. 'last_month', 'last_quarter', 'year_to_date') y proporciona:
    - Resumen del estado de resultados (ingresos, gastos, beneficio)
    - Resumen del balance general (activos, pasivos, patrimonio)
    - Ratios financieros clave (ej. liquidez, rentabilidad)
    - Comparación con el período anterior si es posible
    - Observaciones o alertas importantes.
    
    Utiliza las herramientas disponibles como 'search_journal_entries' y 'analyze_financial_ratios' para obtener los datos necesarios de Odoo.
    """
