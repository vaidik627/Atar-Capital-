import re
from typing import Dict, Any, Optional

class FallbackResolver:
    """
    A 4-step safety net to ensure Extracted JSON data is complete and mathematically sound.
    Intercepts data between AI extraction and final JSON save.
    
    Steps:
    1. AI Check: Is it valid?
    2. Regex OCR: Can we find it in the raw text?
    3. Math Derivation: Can we calculate it from other metrics?
    4. Safe Default: Inject "N/A" or "-" to prevent crashes.
    """
    
    def __init__(self, ocr_text: str):
        self.ocr_text = ocr_text.lower()
        self.raw_text = ocr_text

    def apply_resolution(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        print("\n🛡️  Running Fallback Resolver Layer...")
        
        data = dict(extracted_data)
        
        # We need to secure the core profit metrics (Revenue, GP, OpEx, EBITDA)
        profit_metrics = data.get("profit_metrics", {})
        revenue = data.get("revenue", {})
        
        # Ensure base structures exist
        if not isinstance(profit_metrics, dict): profit_metrics = {}
        if not isinstance(revenue, dict): revenue = {}
        
        self._resolve_revenue(revenue)
        self._resolve_profit_metrics(profit_metrics, revenue)
        
        # Save back to main dict
        data["profit_metrics"] = profit_metrics
        data["revenue"] = revenue
        
        print("🛡️  Fallback Resolution Complete.")
        return data

    def _resolve_revenue(self, revenue_data: Dict[str, Any]):
        # Revenue history often comes as a list of dicts: [{"period": "FY22", "value": 100}, ...]
        history = revenue_data.get("history", [])
        if isinstance(history, list):
            for item in history:
                if isinstance(item, dict):
                    self._safeguard_metric(item, "Revenue")

    def _resolve_profit_metrics(self, profit_metrics: Dict[str, Any], revenue: Dict[str, Any]):
        # These are usually lists of dictionaries
        gp_list = profit_metrics.get("gross_profit", [])
        opex_list = profit_metrics.get("operating_expenses", [])
        ebitda_list = profit_metrics.get("ebitda", [])
        
        # Map periods to values for easier math derivation
        rev_map = self._build_period_map(revenue.get("history", []))
        gp_map = self._build_period_map(gp_list)
        opex_map = self._build_period_map(opex_list)
        ebitda_map = self._build_period_map(ebitda_list)
        
        # Collect all active periods to ensure every metric has an entry
        all_periods = set(list(rev_map.keys()) + list(gp_map.keys()) + list(opex_map.keys()) + list(ebitda_map.keys()))
        
        # Reconstruct the lists to ensure complete mathematical harmony
        new_gp, new_opex, new_ebitda = [], [], []
        
        for p in sorted(all_periods):
            r_val = rev_map.get(p)
            g_val = gp_map.get(p)
            o_val = opex_map.get(p)
            e_val = ebitda_map.get(p)
            
            # --- MATH DERIVATION LAYER ---
            
            # 1. GP = Revenue - COGS (If we had COGS, but usually we just calculate OpEx/EBITDA)
            
            # 2. EBITDA = GP - OpEx
            if e_val is None and g_val is not None and o_val is not None:
                # OpEx is often negative. EBITDA = GP + OpEx (if OpEx is negative) or GP - OpEx
                e_val = g_val - abs(o_val)
                print(f"   [Math Derivation] Derived EBITDA for {p} = {e_val}")
                
            # 3. OpEx = GP - EBITDA (Accounting plug)
            if o_val is None and g_val is not None and e_val is not None:
                o_val = -(g_val - e_val) # OpEx is traditionally negative
                print(f"   [Math Derivation] Derived OpEx for {p} = {o_val}")
                
            # 4. GP = EBITDA + OpEx (If GP is missing)
            if g_val is None and e_val is not None and o_val is not None:
                g_val = e_val + abs(o_val)
                print(f"   [Math Derivation] Derived Gross Profit for {p} = {g_val}")

            # Rebuild individual metrics with safe defaults if all else fails
            new_gp.append({"period": p, "value": g_val if g_val is not None else "N/A"})
            new_opex.append({"period": p, "value": o_val if o_val is not None else "N/A"})
            new_ebitda.append({"period": p, "value": e_val if e_val is not None else "N/A"})
            
        profit_metrics["gross_profit"] = new_gp
        profit_metrics["operating_expenses"] = new_opex
        profit_metrics["ebitda"] = new_ebitda

    def _build_period_map(self, metric_list: list) -> Dict[str, float]:
        """Convert [{"period": "FY21", "value": 100}] into {"FY21": 100.0}"""
        m = {}
        if not isinstance(metric_list, list): return m
        for item in metric_list:
            if isinstance(item, dict):
                p = item.get("period")
                v = item.get("value")
                if p and v is not None and v != "N/A" and v != "-":
                    try:
                        m[str(p)] = float(v)
                    except ValueError:
                        pass
        return m

    def _safeguard_metric(self, item_dict: Dict[str, Any], metric_name: str):
        """
        Applies Step 1 (Check), Step 2 (Regex), and Step 4 (Safe Default)
        on a specific dictionary item (e.g. {"period": "FY22", "value": null})
        """
        val = item_dict.get("value")
        period = item_dict.get("period", "")
        
        # Step 1: AI Check
        if val is not None and val != "null" and str(val).strip() != "":
            return # Healthy
            
        print(f"   [AI Check Failed] Missing {metric_name} for period {period}. Attempting regex recovery...")
        
        # Step 2: Regex OCR Extraction
        recovered_val = self._regex_search_metric(metric_name, period)
        if recovered_val is not None:
            item_dict["value"] = recovered_val
            print(f"   [Regex OCR] Recovered {metric_name} for {period} = {recovered_val}")
            return
            
        # Step 4: Safe Default (Step 3 happens at the aggregate loop level)
        item_dict["value"] = "N/A"
        print(f"   [Safe Default] Applied N/A to {metric_name} for {period}")

    def _regex_search_metric(self, metric_name: str, period: str) -> Optional[float]:
        """
        Attempts to find a metric directly in the OCR text using regex.
        Very basic implementation that looks for "MetricName ... 2022 ... $100"
        """
        if not period: return None
        
        # Extract just the year from "FY22A" -> "22" or "2022"
        year_match = re.search(r'\d{2,4}', str(period))
        if not year_match: return None
        year = year_match.group(0)
        if len(year) == 2: year = "20" + year # Simple assumption for 2000s
        
        # Build a flexible regex pattern. 
        # Example: look for "ebitda" followed by some text (up to 200 chars), 
        # followed by the year, followed by a number.
        term = metric_name.lower().replace(" ", r"\s*")
        
        # Pattern 1: Table row style: "Revenue 100 120 150" where columns are years.
        # This is extremely complex to reliably regex without coordinate data.
        
        # Pattern 2: Narrative style: "EBITDA in 2022 was $15.5M"
        pattern = rf"{term}[\s\w\.\,]{{0,100}}{year}[\s\w]{{0,30}}\$?([\d\,\.]+)"
        
        try:
            matches = re.findall(pattern, self.ocr_text)
            if matches:
                # Take the first plausible number
                raw_num = matches[0].replace(",", "")
                if raw_num.replace(".", "").isdigit():
                    return float(raw_num)
        except Exception:
            pass
            
        return None

def apply_fallback_resolution(extracted_data: Dict[str, Any], ocr_text: str) -> Dict[str, Any]:
    resolver = FallbackResolver(ocr_text)
    return resolver.apply_resolution(extracted_data)
