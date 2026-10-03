from typing import List, Dict, Tuple, Any

# Hierarchy of confidentiality levels
CONFIDENTIALITY_LEVELS = {
    "PUBLIC": 1,
    "INTERNAL": 2,
    "CONFIDENTIAL": 3,
    "HIGHLY_CONFIDENTIAL": 4
}

ROLE_BASE_PERMISSIONS = {
    "Admin": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"],
    "Hospital Manager": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
    "Doctor": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
    "Nurse": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],  # Nurse can access selected CONFIDENTIAL documents if allowed in allowed_roles
    "Receptionist": ["PUBLIC", "INTERNAL"],
    "Intern": ["PUBLIC", "INTERNAL"]
}

ROLE_MAX_CONFIDENTIALITY = {
    "Admin": "HIGHLY_CONFIDENTIAL",
    "Hospital Manager": "CONFIDENTIAL",
    "Doctor": "CONFIDENTIAL",
    "Nurse": "CONFIDENTIAL",
    "Receptionist": "INTERNAL",
    "Intern": "INTERNAL"
}

def can_role_access_level(role: str, level: str) -> bool:
    """Checks if a user role can access a given document confidentiality level."""
    allowed = ROLE_BASE_PERMISSIONS.get(role, ["PUBLIC"])
    return level in allowed

def check_document_access(user_role: str, user_dept: str, document: Any) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates whether a user with `user_role` and `user_dept` is authorized to access `document`.
    Returns (is_allowed, reason_message, explanation_dict)
    """
    doc_level = document.confidentiality_level
    doc_allowed_roles = document.allowed_roles if hasattr(document, 'allowed_roles') else []

    max_level = ROLE_MAX_CONFIDENTIALITY.get(user_role, "PUBLIC")
    
    # 1. Check confidentiality level hierarchy
    if CONFIDENTIALITY_LEVELS.get(doc_level, 1) > CONFIDENTIALITY_LEVELS.get(max_level, 1):
        reason = f"Your role ({user_role}) does not have permission to view {doc_level} documents."
        rule = f"{doc_level} documents can only be accessed by authorized senior roles ({', '.join([r for r, l in ROLE_MAX_CONFIDENTIALITY.items() if CONFIDENTIALITY_LEVELS.get(l,1) >= CONFIDENTIALITY_LEVELS.get(doc_level,1)])})."
        evidence = f"Document Classification = {doc_level}. User Role = {user_role}. Max Allowed Level = {max_level}."
        return False, reason, {
            "recommendation": "Deny Access",
            "reason": reason,
            "rule": rule,
            "evidence": evidence,
            "confidence_status": "BLOCKED",
            "required_action": "Access Denied"
        }

    # 2. Check document explicit allowed roles if defined
    if doc_allowed_roles and user_role not in doc_allowed_roles and "Admin" not in user_role:
        reason = f"Document is restricted to specific roles ({', '.join(doc_allowed_roles)}) and does not explicitly include {user_role}."
        rule = "Role-specific document restrictions supersede baseline department access."
        evidence = f"Document ID = {document.document_id}. Allowed Roles = {doc_allowed_roles}. User Role = {user_role}."
        return False, reason, {
            "recommendation": "Deny Access",
            "reason": reason,
            "rule": rule,
            "evidence": evidence,
            "confidence_status": "BLOCKED",
            "required_action": "Access Denied"
        }

    # 3. Check protocol version status
    if hasattr(document, 'status') and document.status == "SUPERSEDED":
        reason = "This protocol document version has been superseded by a newer active version."
        rule = "Staff must use current active protocol versions for patient safety."
        evidence = f"Document Version = {document.protocol_version}. Status = {document.status}. Active Version ID = {getattr(document, 'current_active_version_id', 'N/A')}."
        return True, "Allowed (Superseded Warning)", {
            "recommendation": "Use Active Version",
            "reason": reason,
            "rule": rule,
            "evidence": evidence,
            "confidence_status": "SUPERSEDED_WARNING",
            "required_action": "Switch to active version recommended"
        }

    reason = f"User role {user_role} is authorized to access {doc_level} document in department {document.department}."
    rule = "Access granted based on role hierarchy and document permission matrix."
    evidence = f"Document Classification = {doc_level}. User Role = {user_role}."
    return True, "Authorized", {
        "recommendation": "Allow Access",
        "reason": reason,
        "rule": rule,
        "evidence": evidence,
        "confidence_status": "AUTHORIZED",
        "required_action": "None"
    }

def check_section_access(user_role: str, section: Any) -> Tuple[bool, str]:
    """Checks if a specific section can be viewed by the user's role."""
    if not section.is_sensitive:
        return True, "Public/Internal standard section"

    restricted_roles = section.restricted_roles if hasattr(section, 'restricted_roles') else []
    if user_role in restricted_roles:
        return False, f"Section explicitly restricts role: {user_role}"

    section_level = getattr(section, 'confidentiality_level', 'INTERNAL')
    max_level = ROLE_MAX_CONFIDENTIALITY.get(user_role, "PUBLIC")

    if CONFIDENTIALITY_LEVELS.get(section_level, 1) > CONFIDENTIALITY_LEVELS.get(max_level, 1):
        return False, f"Section requires {section_level} level, but user role is {user_role}"

    return True, "Authorized for section"
