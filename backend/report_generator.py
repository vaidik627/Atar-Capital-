import os
import csv
import time
import json
from .config import REPORTS_DIR

def generate_csv_report(deal_id, deal_name, data):
    """
    Generates a CSV report for the deal.
    
    Layout:
    1. Financial Matrix
    2. (Empty Line)
    3. Cash Flow Table
    
    Returns:
        str: The filename of the generated report.
    """
    
    timestamp = int(time.time())
    # Clean deal name for filename
    safe_deal_name = "".join([c for c in deal_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
    filename = f"{safe_deal_name}_{deal_id}_Analysis_{timestamp}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    financial_matrix = data.get('financial_matrix', [])
    cash_flow = data.get('cash_flow_matrix', []) # Check if it's 'cash_flow' or 'cash_flow_matrix'
    
    # Fallback if cash_flow_matrix is empty, check cash_flow
    if not cash_flow:
        cash_flow = data.get('cash_flow', [])

    # Define fixed periods to match frontend exactly
    actual_years = ['2019A', '2020A', '2021A', '2022A']
    atar_years = ['2023R', '2024R', '2025R', '2026R', '2027R']
    mgmt_years = ['2023M', '2024M', '2025M', '2026M', '2027M']
    
    # Combined sorted periods (fixed structure)
    sorted_periods = actual_years + atar_years + mgmt_years
    
    # Helper to format Financial Matrix values (Millions)
    def format_millions(val):
        if val == '-' or val is None or val == 'N/A':
            return '-'
        try:
            # Clean string
            clean_val = str(val).replace('$', '').replace(',', '').replace(' ', '')
            if not clean_val or clean_val == '-': return '-'
            
            # Handle negatives
            is_negative = False
            if '(' in clean_val and ')' in clean_val:
                is_negative = True
                clean_val = clean_val.replace('(', '').replace(')', '')
            elif clean_val.startswith('-'):
                is_negative = True
                clean_val = clean_val.lstrip('-')
                
            num = float(clean_val)
            
            # Convert to Millions
            num = num / 1000000.0
            
            # Format to 1 decimal place
            formatted = "{:.1f}".format(num)
            
            if is_negative:
                return f"({formatted})"
            return formatted
        except:
            return str(val)

    # Helper to format cash flow values (Thousands)
    def format_cash_flow_value(val):
        if val == '-' or val is None or val == 'N/A':
            return '-'
        try:
            # Clean string
            clean_val = str(val).replace('$', '').replace(',', '').replace(' ', '')
            if not clean_val or clean_val == '-': return '-'
            
            # Handle negatives
            is_negative = False
            if '(' in clean_val and ')' in clean_val:
                is_negative = True
                clean_val = clean_val.replace('(', '').replace(')', '')
            elif clean_val.startswith('-'):
                is_negative = True
                clean_val = clean_val.lstrip('-')
                
            num = float(clean_val)
            
            # Always divide by 1000 to show in Thousands (matching frontend)
            num = num / 1000.0
                
            # Format with commas, no decimals
            formatted = "{:,.0f}".format(num)
            
            if is_negative:
                return f"({formatted})"
            return formatted
        except:
            return str(val)

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # --- Financial Matrix Section ---
        writer.writerow(["FINANCIAL METRICS ($ in Millions)"])
        writer.writerow([]) # Spacer
        
        # Category Headers
        # Actuals (4 cols), Atar (5 cols), Mgmt (5 cols)
        # Col 1 is Metric name
        # We need to construct the header row carefully
        
        #              Metric,   2019A...2022A,        2023R...2027R,             2023M...2027M
        # Cat Header:  "",       Actuals, "", "", "",  Atar Projections, ...      Management Projections...
        
        cat_header_row = [""] # Metric col
        
        # Actuals
        cat_header_row.append("Actuals")
        cat_header_row.extend([""] * (len(actual_years) - 1))
        
        # Atar
        cat_header_row.append("Atar Projections")
        cat_header_row.extend([""] * (len(atar_years) - 1))
        
        # Mgmt
        cat_header_row.append("Management Projections")
        cat_header_row.extend([""] * (len(mgmt_years) - 1))
        
        writer.writerow(cat_header_row)
        
        # Period Header
        header = ["Metric"] + sorted_periods
        writer.writerow(header)
        
        for item in financial_matrix:
            metric_name = item.get('metric', 'Unknown')
            values = item.get('values', {})
            row = [metric_name]
            for p in sorted_periods:
                val = values.get(p, '-')
                # Apply Millions formatting
                row.append(format_millions(val))
            writer.writerow(row)
            
            # Check for sub-metrics (Growth, Margin)
            sub_metric = item.get('sub_metric')
            sub_values = item.get('sub_values')
            if sub_metric: # Even if no values, show the row if metric exists? 
                           # Frontend checks if (sub_metric) and renders.
                # Indent sub-metric name
                sub_row = [f"   {sub_metric}"]
                for p in sorted_periods:
                    val = sub_values.get(p, '-') if sub_values else '-'
                    # Sub-metrics are usually percentages (Growth/Margin), so we don't divide by Million?
                    # Let's check frontend.
                    # Frontend: sub_values are rendered directly: `val = row.sub_values[year]`.
                    # It does NOT use formatMillions for sub-metrics (Growth/Margin are usually %).
                    sub_row.append(val)
                writer.writerow(sub_row)
            
        writer.writerow([])
        writer.writerow([])
        
        # --- Cash Flow Section ---
        writer.writerow(["CASH FLOW ANALYSIS ($ in Thousands)"])
        writer.writerow([]) # Spacer
        
        # Write Category Header again
        writer.writerow(cat_header_row)
        
        # Use same periods
        writer.writerow(header)
        
        for item in cash_flow:
            metric_name = item.get('metric', 'Unknown')
            values = item.get('values', {})
            row = [metric_name]
            for p in sorted_periods:
                val = values.get(p, '-')
                formatted_val = format_cash_flow_value(val)
                row.append(formatted_val)
            writer.writerow(row)

            
    return filename
