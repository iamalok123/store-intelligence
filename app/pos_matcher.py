import csv
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db_models import EventDB, PosTransactionDB

def load_and_match_pos(db: Session, csv_path: str = "data/pos_transactions.csv"):
    if not os.path.exists(csv_path):
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            store_id = row.get("store_id")
            tx_id = row.get("transaction_id")
            ts_str = row.get("timestamp")
            basket_val = row.get("basket_value_inr")
            
            if not store_id or not tx_id or not ts_str:
                continue
                
            # Check if transaction already exists
            existing = db.query(PosTransactionDB).filter(PosTransactionDB.transaction_id == tx_id).first()
            if existing:
                continue
                
            # Parse timestamp (assuming ISO 8601)
            try:
                # Basic parse
                tx_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                # try another format if needed
                continue
                
            tx = PosTransactionDB(
                transaction_id=tx_id,
                store_id=store_id,
                timestamp=tx_ts,
                basket_value_inr=float(basket_val) if basket_val else 0.0,
                matched_visitor_id=None
            )
            
            # Find matching visitor
            # candidate_events = billing events
            # where store_id = tx.store_id
            # and timestamp between tx.timestamp - 5 min and tx.timestamp
            # and is_staff = false
            window_start = tx_ts - timedelta(minutes=5)
            
            # BILLING_QUEUE_JOIN is inherently billing zone. 
            # For ZONE_ENTER or ZONE_DWELL, usually there's a specific zone_id, but the prompt says 
            # "Visitor must have BILLING_QUEUE_JOIN, ZONE_ENTER, or ZONE_DWELL in billing zone."
            # Since we don't have a strict zone config, we can just match BILLING_QUEUE_JOIN or any event in a zone containing 'billing'.
            
            candidates = db.query(EventDB).filter(
                EventDB.store_id == store_id,
                EventDB.timestamp >= window_start,
                EventDB.timestamp <= tx_ts,
                EventDB.is_staff == False,
                EventDB.event_type.in_(["BILLING_QUEUE_JOIN", "ZONE_ENTER", "ZONE_DWELL"])
            ).all()
            
            # Filter candidates for billing zone (if it's not BILLING_QUEUE_JOIN)
            valid_candidates = []
            for c in candidates:
                if c.event_type == "BILLING_QUEUE_JOIN":
                    valid_candidates.append(c)
                elif c.zone_id and "billing" in c.zone_id.lower():
                    valid_candidates.append(c)
                    
            if valid_candidates:
                # choose candidate with max(timestamp)
                best_candidate = max(valid_candidates, key=lambda c: c.timestamp)
                tx.matched_visitor_id = best_candidate.visitor_id
                
            db.add(tx)
    
    db.commit()

def calculate_conversion_rate(store_id: str, db: Session) -> float:
    # unique visitors
    unique_visitors = db.query(func.count(func.distinct(EventDB.visitor_id)))\
        .filter(EventDB.store_id == store_id)\
        .filter(EventDB.event_type == "ENTRY")\
        .filter(EventDB.is_staff == False)\
        .scalar() or 0
        
    if unique_visitors == 0:
        return 0.0
        
    # matched visitors
    converted = db.query(func.count(func.distinct(PosTransactionDB.matched_visitor_id)))\
        .filter(PosTransactionDB.store_id == store_id)\
        .filter(PosTransactionDB.matched_visitor_id.isnot(None))\
        .scalar() or 0
        
    return converted / unique_visitors
