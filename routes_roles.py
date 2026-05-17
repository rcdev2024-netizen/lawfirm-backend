from fastapi import APIRouter, HTTPException, Depends, status
from database import supabase
import auth as auth_utils
import schemas

router = APIRouter(prefix="/api/roles", tags=["Roles & User Management"])


# ── ADMIN GUARD ───────────────────────────────────────────────

def require_admin(current_user: dict = Depends(auth_utils.get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ── ROLE CRUD ─────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[schemas.RoleOut],
    summary="List all roles (Admin only)"
)
def list_roles(admin: dict = Depends(require_admin)):
    result = supabase.table("roles").select("*").order("id").execute()
    return result.data or []


@router.post(
    "",
    response_model=schemas.RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new custom role (Admin only)"
)
def create_role(payload: schemas.RoleCreate, admin: dict = Depends(require_admin)):
    existing = supabase.table("roles").select("id").eq("name", payload.name).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.name}' already exists"
        )

    result = supabase.table("roles").insert({
        "name":         payload.name,
        "display_name": payload.display_name,
        "description":  payload.description,
        "is_system":    False,
        "is_active":    True
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )
    return result.data[0]


@router.patch(
    "/{role_name}",
    response_model=schemas.RoleOut,
    summary="Update a role's display name or description (Admin only)"
)
def update_role(role_name: str, payload: schemas.RoleUpdate, admin: dict = Depends(require_admin)):
    existing = supabase.table("roles").select("*").eq("name", role_name).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role = existing.data[0]

    update_data: dict = {}
    if payload.display_name is not None:
        update_data["display_name"] = payload.display_name
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.is_active is not None:
        if role["is_system"] and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate a system role"
            )
        update_data["is_active"] = payload.is_active

    if not update_data:
        return role

    update_data["updated_at"] = "now()"

    result = supabase.table("roles").update(update_data).eq("name", role_name).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )
    return result.data[0]


@router.delete(
    "/{role_name}",
    summary="Delete a custom role (Admin only — system roles are protected)"
)
def delete_role(role_name: str, admin: dict = Depends(require_admin)):
    existing = supabase.table("roles").select("*").eq("name", role_name).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role = existing.data[0]
    if role["is_system"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a system role"
        )

    in_use = supabase.table("users").select("id").eq("role", role_name).limit(1).execute()
    if in_use.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_name}' is assigned to one or more users and cannot be deleted"
        )

    supabase.table("roles").delete().eq("name", role_name).execute()
    return {"message": f"Role '{role_name}' deleted successfully"}


# ── ROLE PERMISSIONS ──────────────────────────────────────────

@router.get(
    "/{role_name}/permissions",
    response_model=list[schemas.RolePermissionOut],
    summary="List permissions for a role (Admin only)"
)
def list_role_permissions(role_name: str, admin: dict = Depends(require_admin)):
    existing = supabase.table("roles").select("id").eq("name", role_name).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    result = supabase.table("role_permissions").select("*").eq("role_name", role_name).execute()
    return result.data or []


@router.post(
    "/{role_name}/permissions",
    response_model=schemas.RolePermissionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a permission to a role (Admin only)"
)
def add_role_permission(
    role_name: str,
    payload: schemas.RolePermissionCreate,
    admin: dict = Depends(require_admin)
):
    existing_role = supabase.table("roles").select("id").eq("name", role_name).execute()
    if not existing_role.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    result = supabase.table("role_permissions").insert({
        "role_name":  role_name,
        "permission": payload.permission
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists for this role or insert failed"
        )
    return result.data[0]


@router.delete(
    "/{role_name}/permissions/{permission}",
    summary="Remove a permission from a role (Admin only)"
)
def remove_role_permission(role_name: str, permission: str, admin: dict = Depends(require_admin)):
    existing = supabase.table("role_permissions") \
        .select("id") \
        .eq("role_name", role_name) \
        .eq("permission", permission) \
        .execute()

    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    supabase.table("role_permissions") \
        .delete() \
        .eq("role_name", role_name) \
        .eq("permission", permission) \
        .execute()

    return {"message": f"Permission '{permission}' removed from role '{role_name}'"}


# ── USER ROLE MANAGEMENT ──────────────────────────────────────

@router.get(
    "/users",
    response_model=list[schemas.UserRoleOut],
    summary="List all users with their roles (Admin only)"
)
def list_users_with_roles(
    role: str | None = None,
    admin: dict = Depends(require_admin)
):
    query = supabase.table("users").select(
        "id, full_name, email, role, phone, is_active, created_at"
    )
    if role:
        query = query.eq("role", role)
    result = query.order("created_at", desc=True).execute()
    return result.data or []


@router.get(
    "/users/{user_id}",
    response_model=schemas.UserRoleOut,
    summary="Get a specific user's role info (Admin only)"
)
def get_user_role(user_id: int, admin: dict = Depends(require_admin)):
    result = supabase.table("users") \
        .select("id, full_name, email, role, phone, is_active, created_at") \
        .eq("id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return result.data[0]


@router.patch(
    "/users/{user_id}/role",
    response_model=schemas.UserRoleOut,
    summary="Update a user's role (Admin only)"
)
def update_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdate,
    admin: dict = Depends(require_admin)
):
    user_result = supabase.table("users") \
        .select("id, role, full_name, email, phone, is_active, created_at") \
        .eq("id", user_id) \
        .execute()

    if not user_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = user_result.data[0]
    old_role = user["role"]

    valid_role = supabase.table("roles") \
        .select("name") \
        .eq("name", payload.role) \
        .eq("is_active", True) \
        .execute()

    if not valid_role.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role}' does not exist or is inactive"
        )

    if old_role == payload.role:
        return user

    update_result = supabase.table("users") \
        .update({"role": payload.role}) \
        .eq("id", user_id) \
        .execute()

    if not update_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

    supabase.table("role_audit_log").insert({
        "user_id":    user_id,
        "changed_by": admin["id"],
        "old_role":   old_role,
        "new_role":   payload.role,
        "reason":     payload.reason
    }).execute()

    return update_result.data[0]


# ── ROLE AUDIT LOG ────────────────────────────────────────────

@router.get(
    "/audit",
    response_model=list[schemas.RoleAuditOut],
    summary="View role change audit log (Admin only)"
)
def get_role_audit_log(
    user_id: int | None = None,
    limit: int = 50,
    admin: dict = Depends(require_admin)
):
    query = supabase.table("role_audit_log").select("*")
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.order("changed_at", desc=True).limit(limit).execute()
    return result.data or []
