import sys
import os
import json

# Add parent directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.extraction import extract_pre_bid_analysis

ocr_text = """
this is the text inside this pre bid analysis : Project Manta Ray Pre-Bid Analysis 
 Herff Jones 
 USD in Thousands 
 
 Summary 
 Atar Equity 
   Equity @ Close                         $17,106 
   Capital Call                                - 
   Total Atar Equity                      $17,106 
 
 
 Sources & Uses 
 
 Sources 
   Equity @ Close                         $17,106 
   AR                                       21,184 
   Inventory                                40,916 
   PP&E                                          - 
   Other                                         - 
   Earnout                                       - 
   Seller Roll                                   - 
 
   Total Sources                            ######## 
 
   Seller Proceeds @ Close by Source       $69,000 
     > ABL Financing                         62,100 
     > Atar Equity                            6,900 
 
 
 Uses 
   Purchase Price                          $69,000 
   WC Availability                           9,000 
   Transaction Fees                          1,206 
 
   Total Uses                               ######## 
 
 
 Shareholder Returns 
 
 Exit 
   EV @ Exit                              $105,000 
   + Cash                                  33,314 
   - Debt                                       - 
   - Expenses                                (3,150) 
   - Mgmt LTIP                               (6,758) 
   - Seller Equity                                - 
 
   Atar Equity                              ######## 
 
 
 Distribution of Proceeds 
   Return of Equity                          17,106 
   Interest on Preferred Shares               6,842 
   LP Split of Proceeds                      83,566 
 
   LP Total Distribution                    ######## 
   LP MOIC                                      6.3x 
   GP Split of Proceeds                      20,892 
"""

if __name__ == "__main__":
    print("Running Pre-Bid Analysis Extraction Test...")
    try:
        data = extract_pre_bid_analysis(ocr_text, deal_id="TEST_DEAL_001")
        print("\nSUCCESS! Extracted Data:")
        print(json.dumps(data, indent=2))
        
        # Verify file creation
        from backend.config import PRE_BID_DATA_DIR
        files = os.listdir(PRE_BID_DATA_DIR)
        print(f"\nFiles in {PRE_BID_DATA_DIR}:")
        for f in files:
            print(f" - {f}")
            
    except Exception as e:
        print(f"\nFAILED: {e}")
