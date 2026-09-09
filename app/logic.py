"""
Business Logic Layer — Jodo operational dashboard system
Tasks T042, T043, T044: Stock status classification, alert extraction, and dashboard KPIs

Phase 1-3 uses this with mock data; Phase 4+ calls Odoo XML-RPC for live data.
"""

from datetime import datetime


def get_status(item):
    """
    Classify the stock status of a single product based on qty vs min_qty.
    
    Task T042: Stock Status Classifier
    
    Args:
        item (dict): Product record with 'qty' (current_stock) and 'min_qty' (reorder_point) keys
        
    Returns:
        str: One of 'ok', 'low', 'critical', or 'out'
        
    Example:
        >>> get_status({'qty': 5, 'min_qty': 20})
        'critical'
        >>> get_status({'qty': 100, 'min_qty': 20})
        'ok'
    """
    qty = item.get("qty") or item.get("current_stock", 0)
    min_qty = item.get("min_qty") or item.get("reorder_point", 0)
    
    if qty <= 0:
        return "out"
    elif qty < min_qty:
        return "critical"
    elif qty < min_qty * 1.2:
        return "low"
    else:
        return "ok"


def get_alerts(stock):
    """
    Extract and sort products below their minimum threshold by urgency.
    
    Task T043: Alert Extractor & Sorter
    
    Args:
        stock (list): List of product dicts with 'qty', 'min_qty', 'product', 'sku' keys
        
    Returns:
        list: Sorted list of alert dicts (highest urgency first), each containing:
              - product: product name
              - sku: SKU identifier
              - qty: current quantity
              - min_qty: minimum threshold
              - status: one of 'critical', 'out', 'low'
              - urgency: percentage (0–100) indicating how critical the shortage is
              
    Urgency calculation:
        urgency = ((min_qty - qty) / min_qty) × 100
        - 0% = just barely below minimum
        - 100% = completely out of stock
        
    Example:
        >>> alerts = get_alerts([
        ...     {'sku': 'S1', 'product': 'Item A', 'qty': 5, 'min_qty': 20},
        ...     {'sku': 'S2', 'product': 'Item B', 'qty': 100, 'min_qty': 50}
        ... ])
        >>> len(alerts)
        1
        >>> alerts[0]['urgency']
        75.0
    """
    alerts = []
    
    for item in stock:
        # Normalize field names (support both "qty"/"current_stock" and "min_qty"/"reorder_point")
        qty = item.get("qty") or item.get("current_stock", 0)
        min_qty = item.get("min_qty") or item.get("reorder_point", 0)
        
        # Only include items below minimum threshold
        if qty < min_qty:
            # Avoid division by zero
            if min_qty > 0:
                urgency = ((min_qty - qty) / min_qty) * 100
            else:
                urgency = 0.0
            
            alert = {
                "product": item.get("product") or item.get("product_name", "Unknown"),
                "sku": item.get("sku") or item.get("sku_id", "Unknown"),
                "qty": qty,
                "min_qty": min_qty,
                "status": get_status(item),
                "urgency": round(urgency, 2),
            }
            alerts.append(alert)
    
    # Sort by urgency descending (highest percentage first = most urgent)
    alerts.sort(key=lambda x: x["urgency"], reverse=True)
    
    return alerts


def compute_stats(stock, transfers):
    """
    Compute dashboard KPI stats from stock and transfer data.
    
    Task T044: Dashboard KPI Calculator
    
    Args:
        stock (list): List of product dicts with 'sku'/'sku_id', 'qty'/'current_stock', 
                     and 'min_qty'/'reorder_point' keys
        transfers (list): List of transfer dicts with 'state' and 'due' keys
        
    Returns:
        dict: KPI stats with keys:
              - total_skus: count of unique SKUs in stock
              - pending: count of transfers in 'draft' or 'waiting' state
              - due_today: count of transfers due today
              - alerts: count of products with qty < min_qty
              - critical: count of products with qty <= 0 (out of stock)
              
    Example:
        >>> stats = compute_stats(
        ...     stock=[
        ...         {'sku': 'S1', 'qty': 5, 'min_qty': 20},    # alert
        ...         {'sku': 'S2', 'qty': 0, 'min_qty': 10},     # critical
        ...         {'sku': 'S3', 'qty': 100, 'min_qty': 50}    # ok
        ...     ],
        ...     transfers=[
        ...         {'state': 'draft', 'due': '2026-09-04'},
        ...         {'state': 'done', 'due': '2026-09-04'}
        ...     ]
        ... )
        >>> stats['total_skus']
        3
        >>> stats['alerts']
        1
        >>> stats['critical']
        1
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # ========== Count unique SKUs ==========
    skus = set()
    for item in stock:
        sku = item.get("sku") or item.get("sku_id")
        if sku:
            skus.add(sku)
    total_skus = len(skus)
    
    # ========== Count alerts (qty < min_qty) ==========
    alerts_count = 0
    for item in stock:
        qty = item.get("qty") or item.get("current_stock", 0)
        min_qty = item.get("min_qty") or item.get("reorder_point", 0)
        if qty < min_qty:
            alerts_count += 1
    
    # ========== Count critical (qty <= 0) ==========
    critical_count = 0
    for item in stock:
        qty = item.get("qty") or item.get("current_stock", 0)
        if qty <= 0:
            critical_count += 1
    
    # ========== Count pending transfers (draft or waiting state) ==========
    pending_count = 0
    for transfer in transfers:
        state = transfer.get("state", "").lower()
        if state in ["draft", "waiting"]:
            pending_count += 1
    
    # ========== Count transfers due today ==========
    due_today_count = 0
    for transfer in transfers:
        due_date_str = transfer.get("due")
        if due_date_str:
            try:
                # Handle both string and date formats
                if isinstance(due_date_str, str):
                    # Try ISO format first (YYYY-MM-DD)
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
                else:
                    # If it's already a date object, convert to string
                    due_date = due_date_str.strftime("%Y-%m-%d")
                
                if due_date == today:
                    due_today_count += 1
            except (ValueError, TypeError, AttributeError):
                # Skip entries that can't be parsed
                pass
    
    return {
        "total_skus": total_skus,
        "pending": pending_count,
        "due_today": due_today_count,
        "alerts": alerts_count,
        "critical": critical_count,
    }
