from schemas import Anomaly_Detection, Anomaly_Report
from collections import defaultdict
import statistics

def get_anomalies(transactions_db):
    if not transactions_db:
        return []

    anomalies = []
    category_amounts = defaultdict(list)
    for txn in transactions_db:
        category_amounts[txn.Category].append(abs(txn.Amount))

    for txn in transactions_db:
        amounts = category_amounts[txn.Category]
        if len(amounts) > 1:
            mean_val = statistics.mean(amounts)
            std_val = statistics.stdev(amounts)
            threshold = mean_val + 2 * std_val

            if abs(txn.Amount) > threshold:
                anomalies.append(
                    Anomaly_Detection(
                        Suspicious_Transactions=[txn],
                        Anomaly_Type="High Amount",
                        Severity_Level="High",
                        Reason=f"Transaction ₹{txn.Amount} exceeds threshold ₹{threshold:.2f}",
                        Suggested_Action="Review transaction"
                    )
                )
    return anomalies

def get_anomaly_report(transactions_db):
    anomalies = get_anomalies(transactions_db)
    return Anomaly_Report(
        Total_Transaction=len(transactions_db),
        Anomalies_found=len(anomalies),
        Anomalies=anomalies
    )
