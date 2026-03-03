from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

# Load env
load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

# Supabase Client Init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Schemas
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Endpoints
@router.post("/signup")
def signup(user: UserSignup):
    try:
        # Sign up with Supabase Auth
        # Optionally add metadata like 'full_name'
        res = supabase.auth.sign_up(
            {
                "email": user.email,
                "password": user.password,
                "options": {"data": {"full_name": user.name}},
            }
        )

        # If email confirmation is enabled, user/session might be None until confirmed.
        return {
            "message": "Signup successful. Check email for confirmation if required.",
            "user": res.user,
        }

    except Exception as e:
        error_str = str(e).lower()

        # 한국어 에러 메시지 매핑
        if (
            "already registered" in error_str
            or "already exists" in error_str
            or "user already" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다. 다른 이메일을 사용하거나 로그인해주세요.",
            )
        elif (
            "invalid email" in error_str
            or "email" in error_str
            and "valid" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="올바른 이메일 형식이 아닙니다. 이메일 주소를 확인해주세요.",
            )
        elif "password" in error_str and (
            "weak" in error_str or "short" in error_str or "length" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="비밀번호가 너무 약합니다. 6자 이상의 비밀번호를 사용해주세요.",
            )
        elif (
            "network" in error_str
            or "connection" in error_str
            or "timeout" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="네트워크 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            )
        elif "rate limit" in error_str or "too many" in error_str:
            raise HTTPException(
                status_code=400,
                detail="너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.",
            )
        else:
            # 기본 에러 메시지
            raise HTTPException(
                status_code=400,
                detail=f"회원가입에 실패했습니다. 입력하신 정보를 다시 확인해주세요. ({str(e)})",
            )


@router.post("/login")
def login(user: UserLogin):
    try:
        res = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password,
            }
        )

        # Return access token and user info
        # Convert user object to dict with explicit fields
        user_dict = {
            "id": str(res.user.id),
            "email": res.user.email,
            "user_metadata": res.user.user_metadata or {},
        }

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "user": user_dict,
        }

    except Exception as e:
        error_str = str(e).lower()

        # 한국어 에러 메시지 매핑
        if (
            "invalid login" in error_str
            or "invalid credentials" in error_str
            or "password" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="이메일 또는 비밀번호가 올바르지 않습니다. 다시 확인해주세요.",
            )
        elif "user not found" in error_str or "not found" in error_str:
            raise HTTPException(
                status_code=400,
                detail="등록되지 않은 이메일입니다. 회원가입을 먼저 진행해주세요.",
            )
        elif "email not confirmed" in error_str or "not confirmed" in error_str:
            raise HTTPException(
                status_code=400,
                detail="이메일 인증이 완료되지 않았습니다. 메일함을 확인해주세요.",
            )
        elif (
            "network" in error_str
            or "connection" in error_str
            or "timeout" in error_str
        ):
            raise HTTPException(
                status_code=400,
                detail="네트워크 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            )
        elif "rate limit" in error_str or "too many" in error_str:
            raise HTTPException(
                status_code=400,
                detail="너무 많은 로그인 시도가 발생했습니다. 잠시 후 다시 시도해주세요.",
            )
        elif "blocked" in error_str or "disabled" in error_str:
            raise HTTPException(
                status_code=400,
                detail="계정이 비활성화되었습니다. 관리자에게 문의해주세요.",
            )
        else:
            # 기본 에러 메시지
            raise HTTPException(
                status_code=400,
                detail="로그인에 실패했습니다. 이메일과 비밀번호를 다시 확인해주세요.",
            )

# Dependency to get current user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Verify token with Supabase
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
