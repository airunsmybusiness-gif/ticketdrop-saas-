import sys
sys.path.insert(0, '/Users/lilibethsejera/Downloads/ticketdrop_saas')
import pandas as pd
import hashlib
from datetime import datetime
from db import execute, fetch_all

AXON_COLUMNS = ['TicketNumber','CustomerTicketNumber','TicketDate','CustomerName','LoadedAt','OffloadedAt','Operator','TruckNumber','TrailerNumber','Product','EstimatedVolume','ActualVolume','HoursCharged','Density','BSW','RoadBan','ArriveLoad','DepartLoad','ArriveOffload','DepartOffload','DriverSignature','SignatureDateTime']

def generate_axon_csv(company_id, user_id=None, user_name="System"):
    tickets = fetch_all("""
        SELECT t.id, t.ticket_number, t.customer_ticket_number, t.ticket_date, t.customer_name, t.loaded_at, t.offloaded_at,
               t.operator_name, t.truck_number, t.trailer_number, t.product_description, t.estimated_volume, t.actual_volume,
               t.hours_charged, t.density, t.bsw_cut, t.road_ban, t.arrive_load_datetime, t.depart_load_datetime,
               t.arrive_offload_datetime, t.depart_offload_datetime, t.driver_signature, t.signature_datetime
        FROM tickets t WHERE t.company_id = :company_id AND t.status = 'READY_FOR_INVOICE' ORDER BY t.ticket_date, t.id
    """, {"company_id": company_id})
    if not tickets:
        return None, None, 0, 0, None
    data, ticket_ids, total_volume = [], [], 0
    for t in tickets:
        ticket_ids.append(t[0])
        total_volume += float(t[12] or 0)
        data.append({'TicketNumber': t[1] or '', 'CustomerTicketNumber': t[2] or '', 'TicketDate': str(t[3]) if t[3] else '',
                     'CustomerName': t[4] or '', 'LoadedAt': t[5] or '', 'OffloadedAt': t[6] or '', 'Operator': t[7] or '',
                     'TruckNumber': t[8] or '', 'TrailerNumber': t[9] or '', 'Product': t[10] or '', 'EstimatedVolume': t[11] or 0,
                     'ActualVolume': t[12] or 0, 'HoursCharged': t[13] or 0, 'Density': t[14] or 0, 'BSW': t[15] or 0,
                     'RoadBan': 'Y' if t[16] else 'N', 'ArriveLoad': str(t[17]) if t[17] else '', 'DepartLoad': str(t[18]) if t[18] else '',
                     'ArriveOffload': str(t[19]) if t[19] else '', 'DepartOffload': str(t[20]) if t[20] else '',
                     'DriverSignature': t[21] or '', 'SignatureDateTime': str(t[22]) if t[22] else ''})
    df = pd.DataFrame(data, columns=AXON_COLUMNS)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"AXON_Export_{timestamp}.csv"
    csv_content = df.to_csv(index=False)
    checksum = hashlib.sha256(csv_content.encode()).hexdigest()
    execute("INSERT INTO axon_exports (company_id, filename, ticket_count, ticket_ids, total_volume, checksum, exported_by) VALUES (:company_id, :filename, :count, :ids, :volume, :checksum, :user_id)",
            {"company_id": company_id, "filename": filename, "count": len(ticket_ids), "ids": ticket_ids, "volume": total_volume, "checksum": checksum, "user_id": user_id})
    for ticket_id in ticket_ids:
        execute("UPDATE tickets SET status = 'INVOICED', invoiced_at = NOW(), status_changed_at = NOW() WHERE id = :id", {"id": ticket_id})
        execute("INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by_name, reason) VALUES (:tid, 'READY_FOR_INVOICE', 'INVOICED', :name, :reason)",
                {"tid": ticket_id, "name": user_name, "reason": f"AXON Export: {filename}"})
    return filename, csv_content, len(ticket_ids), total_volume, checksum

def get_export_history(company_id, limit=50):
    return fetch_all("SELECT id, filename, ticket_count, total_volume, checksum, exported_at, status FROM axon_exports WHERE company_id = :company_id ORDER BY exported_at DESC LIMIT :limit",
                     {"company_id": company_id, "limit": limit})
