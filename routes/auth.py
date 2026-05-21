from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Request
from database import supabase
import schemas
import auth as auth_utils
from limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, summary="Register a new user")
@limiter.limit("10/minute")
def register(request: Request, user_data: schemas.UserRegister):
    existing = supabase.table("users").select("id").eq("email", user_data.email).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    role_name = user_data.role or "client"
    role_id = auth_utils.get_role_id(role_name)
    if not role_id:
        role_id = auth_utils.get_role_id("client")
        role_name = "client"

    hashed_pw = auth_utils.get_password_hash(user_data.password)
    approval_status = "pending" if role_name == "client" else "approved"

    result = supabase.table("users").insert({
        "full_name":        user_data.full_name,
        "email":            user_data.email,
        "hashed_password":  hashed_pw,
        "phone":            user_data.phone,
        "role_id":          role_id,
        "is_active":        True,
        "approval_status":  approval_status
    }).execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    user = auth_utils._normalize_user(result.data[0])
    if "role" not in user:
        user["role"] = role_name

    try:
        from routes.audit_logs import log_action
        log_action(user["id"], user["full_name"], "register", "user", user["id"], f"New {role_name} registered: {user['email']}")
    except Exception:
        pass

    access_token = auth_utils.create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=schemas.Token, summary="Login and get JWT token")
@limiter.limit("10/minute")
def login(request: Request, credentials: schemas.UserLogin, background_tasks: BackgroundTasks):
    result = (
        supabase.table("users")
        .select("id, full_name, email, hashed_password, phone, role_id, is_active, approval_status, created_at, roles!users_role_id_fkey(name)")
        .eq("email", credentials.email)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    user = auth_utils._normalize_user(result.data[0])

    if not auth_utils.verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    approval = user.get("approval_status", "approved")
    if user.get("role") == "client" and approval == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval. Please wait for approval before logging in."
        )
    if user.get("role") == "client" and approval == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account registration has been rejected. Please contact the office for assistance."
        )

    try:
        from routes.audit_logs import log_action
        background_tasks.add_task(
            log_action,
            user["id"],
            user["full_name"],
            "login",
            "user",
            user["id"],
            f"User logged in: {user['email']}"
        )
    except Exception:
        pass

    access_token = auth_utils.create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserOut, summary="Get current logged-in user")
def get_me(current_user: dict = Depends(auth_utils.get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut, summary="Update current user profile")
def update_me(body: schemas.UserUpdate, current_user: dict = Depends(auth_utils.get_current_user)):
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        return current_user

    result = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    updated = auth_utils._normalize_user(result.data[0])

    try:
        from routes.audit_logs import log_action
        fields = ", ".join(update_data.keys())
        log_action(current_user["id"], current_user["full_name"], "update_profile", "user", current_user["id"], f"Updated profile fields: {fields}")
    except Exception:
        pass

    return updated


@router.post("/logout", summary="Logout")
def logout(current_user: dict = Depends(auth_utils.get_current_user)):
    try:
        from routes.audit_logs import log_action
        log_action(current_user["id"], current_user["full_name"], "logout", "user", current_user["id"], f"User logged out: {current_user['email']}")
    except Exception:
        pass
    return {"message": "Logged out successfully. Please delete your token on the client side."}
