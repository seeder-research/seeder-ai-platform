from app.models.audit_log import AuditLog


async def log_action(db, actor_id, action: str, target_type: str, target_id=None, metadata: dict | None = None):
    db.add(AuditLog(actor_id=actor_id, action=action, target_type=target_type,
                     target_id=target_id, extra_metadata=metadata))
    await db.commit()
