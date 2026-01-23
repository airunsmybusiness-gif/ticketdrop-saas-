import sys
sys.path.insert(0, '/Users/lilibethsejera/Downloads/ticketdrop_saas')
from db import execute, fetch_scalar

LOAD_TRANSITIONS = {
    'REQUESTED': ['ASSIGNED', 'CANCELLED'],
    'ASSIGNED': ['ACCEPTED', 'DECLINED', 'CANCELLED'],
    'ACCEPTED': ['IN_PROGRESS', 'CANCELLED'],
    'DECLINED': ['ASSIGNED'],
    'IN_PROGRESS': ['COMPLETED', 'CANCELLED'],
    'COMPLETED': [],
    'CANCELLED': [],
}

TICKET_TRANSITIONS = {
    'DRAFT': ['SUBMITTED'],
    'SUBMITTED': ['VERIFIED', 'DISPUTED'],
    'VERIFIED': ['READY_FOR_INVOICE', 'DISPUTED'],
    'READY_FOR_INVOICE': ['INVOICED'],
    'INVOICED': [],
    'DISPUTED': ['SUBMITTED'],
}

ROLE_PERMISSIONS = {
    'dispatch': {'load': ['REQUESTED', 'ASSIGNED', 'CANCELLED'], 'ticket': []},
    'driver': {'load': ['ACCEPTED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED'], 'ticket': ['DRAFT', 'SUBMITTED']},
    'ar': {'load': [], 'ticket': ['VERIFIED', 'READY_FOR_INVOICE', 'INVOICED', 'DISPUTED']},
    'admin': {'load': ['REQUESTED', 'ASSIGNED', 'ACCEPTED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'],
              'ticket': ['DRAFT', 'SUBMITTED', 'VERIFIED', 'READY_FOR_INVOICE', 'INVOICED', 'DISPUTED']}
}

class StatusError(Exception):
    pass

def validate_load_transition(current_status, new_status, role):
    allowed = LOAD_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise StatusError(f"Cannot move load from {current_status} to {new_status}")
    if new_status not in ROLE_PERMISSIONS.get(role, {}).get('load', []):
        raise StatusError(f"Role '{role}' cannot set load status to {new_status}")
    return True

def validate_ticket_transition(current_status, new_status, role):
    allowed = TICKET_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise StatusError(f"Cannot move ticket from {current_status} to {new_status}")
    if new_status not in ROLE_PERMISSIONS.get(role, {}).get('ticket', []):
        raise StatusError(f"Role '{role}' cannot set ticket status to {new_status}")
    return True

def update_load_status(load_id, new_status, user_id, user_name, role, reason=None):
    current = fetch_scalar("SELECT status FROM loads WHERE id = :id", {"id": load_id})
    if not current:
        raise StatusError(f"Load {load_id} not found")
    validate_load_transition(current, new_status, role)
    execute("UPDATE loads SET status = :status, status_changed_at = NOW(), status_changed_by = :user_id, updated_at = NOW() WHERE id = :id",
            {"status": new_status, "user_id": user_id, "id": load_id})
    execute("INSERT INTO load_status_history (load_id, old_status, new_status, changed_by, changed_by_name, reason) VALUES (:load_id, :old, :new, :user_id, :user_name, :reason)",
            {"load_id": load_id, "old": current, "new": new_status, "user_id": user_id, "user_name": user_name, "reason": reason})
    return True

def update_ticket_status(ticket_id, new_status, user_id, user_name, role, reason=None):
    current = fetch_scalar("SELECT status FROM tickets WHERE id = :id", {"id": ticket_id})
    if not current:
        raise StatusError(f"Ticket {ticket_id} not found")
    validate_ticket_transition(current, new_status, role)
    execute("UPDATE tickets SET status = :status, status_changed_at = NOW(), status_changed_by = :user_id, updated_at = NOW() WHERE id = :id",
            {"status": new_status, "user_id": user_id, "id": ticket_id})
    execute("INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, changed_by_name, reason) VALUES (:ticket_id, :old, :new, :user_id, :user_name, :reason)",
            {"ticket_id": ticket_id, "old": current, "new": new_status, "user_id": user_id, "user_name": user_name, "reason": reason})
    return True
