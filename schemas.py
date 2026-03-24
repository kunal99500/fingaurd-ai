from pydantic import BaseModel
from typing import Dict, Optional, List


class transaction_input(BaseModel):
    User_id: float
    Merchant: str
    Amount: float


class transaction(BaseModel):
    Id: float                                   # the id which given by mongo db
    User_Id: Optional[float] = None             # the id of user who made the expense
    Account_number: Optional[str] = None        # Bank account number 
    
    Date: str                                   # the date of expense example: 2023-01-01
    Time: Optional[str] = None                  # the time of expense example: 14:30:00
    
    Description: str                            # like where the expense occur example: grocery store
    Merchant: Optional[str] = None              # like amazon, walmart etc
    Location: Optional[str] = None              # like new york, san francisco etc
    
    Amount: float                               # how much the expense was example:  $100.50
    Currency: str                               # like USD, EUR, INR etc
    Type_of_Payment: str                        # like cash, card, upi etc 
    
    Category: Optional[str] = None              # like food, travel, shopping etc
    Sub_Category: Optional[str] = None          # like "fast food","Restaurant","Online_shopping" etc
    
    Status_of_Transaction: Optional[str] = None # like completed, pending, failed etc
    Reference_Id: Optional[str] = None          # any reference id provided by bank or payment gateway
    
    Notes: Optional[str] = None                 # any additional notes or comments about the transaction
    
    Over_Threshold: Optional[bool] = False      # whether the transaction amount exceeded a predefined threshold
    Blocked: Optional[bool] = False             # whether the transaction was blocked due to suspected fraud


class Category_Summary(BaseModel):
    Category: str                               # like food, travel, shopping etc
    Total_Amount: float                         # total_amount spent in this category
    Transaction_Count: int                      # number of transactions in this category


class Transaction_Summary(BaseModel):
    Total_Income: float                                        # total income amount
    Total_Expense: float                                       # total expense amount
    Net_Savings: float                                         # total savings (income - expense)
    
    Category_Breakdown: List[Category_Summary]                 # breakdown of expenses by category
    Top_Merchants: Optional[Dict[str, float]] = None           # top merchants where most expenses occurred
    monthly_Trends: Optional[Dict[str, float]] = None          # monthly trends in expenses
    
    Largest_Transaction: Optional[transaction] = None          # details of the largest transaction
    Recent_Transaction: Optional[List[transaction]] = None     # list of recent transactions


class Anomaly_Detection(BaseModel):
    Suspicious_Transactions: Optional[List[transaction]] = None  # list of suspicious transactions
    Anomaly_Type: Optional[str] = None                           # e.g. "High Amount", "Unusual Category"
    Severity_Level: Optional[str] = None                         # e.g. "Low", "Medium", "High"
    Reason: Optional[str] = None                                 # explanation for the anomaly
    Suggested_Action: Optional[str] = None                       # e.g. "Review Transaction", "Contact Bank"


class Anomaly_Report(BaseModel):
    Total_Transaction: int
    Anomalies_found: int
    Anomalies: List[Anomaly_Detection]


class User_Settings(BaseModel):
    User_id: float
    Monthly_Limit: Optional[float]
    Current_Spent: Optional[float]
    Alert_Preferences: Optional[Dict]
    Block_Transactions: Optional[bool]
    Category_Limits: Optional[Dict[str, float]] = None


class Threshold_Report(BaseModel):
    User_id: float
    Monthly_Limit: float
    Current_Spent: float
    Remaining_Balance: float
    Limit_Exceeded: bool
    Suggested_Action: Optional[str]


class Daily_Summary(BaseModel):
    User_Id: float
    Date: str
    Total_Spent: float
    Transaction_Today: List[transaction]
    Category_Breakdown: Dict[str, float]
    Top_Merchant: Optional[str] = None
    Notes: Optional[str] = None
