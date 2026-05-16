from fastapi import APIRouter, HTTPException, status, Depends
from database import supabase
import schemas
import auth as auth_utils

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, summary="Register a new user", security=[])
def register(user_data: schemas.UserRegister):
    # Check if email already exists
    existing = supabase.table("users").select("id").eq("email", user_data.email).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_pw = auth_utils.get_password_hash(user_data.password)
    result = supabase.table("users").insert({
        "full_name": user_data.full_name,
        "email": user_data.email,
        "hashed_password": hashed_pw,
        "is_active": True
    }).execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    user = result.data[0]
    access_token = auth_utils.create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=schemas.Token, summary="Login and get JWT token", security=[])
def login(credentials: schemas.UserLogin):
    result = supabase.table("users").select("*").eq("email", credentials.email).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    user = result.data[0]
    if not auth_utils.verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    access_token = auth_utils.create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserOut, summary="Get current logged-in user")
def get_me(current_user: dict = Depends(auth_utils.get_current_user)):
    return current_user


@router.post("/logout", summary="Logout", security=[])
def logout():
    return {"message": "Logged out successfully. Please delete your token on the client side."}
