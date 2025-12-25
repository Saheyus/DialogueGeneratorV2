"""Router pour l'authentification."""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest
)
from api.services.auth_service import AuthService
from api.exceptions import AuthenticationException
from api.dependencies import get_request_id

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Retourne le service d'authentification.
    
    Returns:
        Instance de AuthService.
    """
    return auth_service


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    request: Request
) -> dict:
    """Dépendance pour obtenir l'utilisateur courant depuis le token JWT.
    
    Args:
        credentials: Credentials HTTP (token).
        request: La requête HTTP.
        
    Returns:
        Dictionnaire avec les informations de l'utilisateur.
        
    Raises:
        AuthenticationException: Si le token est invalide ou expiré.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    token = credentials.credentials
    
    payload = auth_service.verify_token(token, token_type="access")
    if payload is None:
        raise AuthenticationException(
            message="Token invalide ou expiré",
            request_id=request_id
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise AuthenticationException(
            message="Token invalide",
            request_id=request_id
        )
    
    user = auth_service.get_user_by_username(username)
    if user is None:
        raise AuthenticationException(
            message="Utilisateur non trouvé",
            request_id=request_id
        )
    
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    request: Request
) -> TokenResponse:
    """Endpoint de connexion.
    
    Args:
        login_data: Données de connexion (username, password).
        request: La requête HTTP.
        
    Returns:
        Tokens d'authentification (access + refresh).
        
    Raises:
        AuthenticationException: Si les identifiants sont invalides.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise AuthenticationException(
            message="Nom d'utilisateur ou mot de passe incorrect",
            request_id=request_id
        )
    
    # Créer les tokens
    access_token = auth_service.create_access_token(data={"sub": user["username"]})
    refresh_token = auth_service.create_refresh_token(data={"sub": user["username"]})
    
    logger.info(f"Utilisateur '{user['username']}' connecté (request_id: {request_id})")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire.total_seconds()
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    response: Response
) -> TokenResponse:
    """Endpoint de rafraîchissement de token.
    
    Args:
        refresh_data: Données de rafraîchissement (peut être dans cookie).
        request: La requête HTTP.
        response: La réponse HTTP.
        
    Returns:
        Nouveau token d'accès.
        
    Raises:
        AuthenticationException: Si le refresh token est invalide.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Chercher le refresh token dans les cookies ou dans le body
    refresh_token = refresh_data.refresh_token
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise AuthenticationException(
            message="Refresh token manquant",
            request_id=request_id
        )
    
    payload = auth_service.verify_token(refresh_token, token_type="refresh")
    if payload is None:
        raise AuthenticationException(
            message="Refresh token invalide ou expiré",
            request_id=request_id
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise AuthenticationException(
            message="Refresh token invalide",
            request_id=request_id
        )
    
    # Créer un nouveau access token
    access_token = auth_service.create_access_token(data={"sub": username})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire.total_seconds()
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> UserResponse:
    """Endpoint pour obtenir les informations de l'utilisateur courant.
    
    Args:
        current_user: Utilisateur courant (injecté via dépendance).
        
    Returns:
        Informations de l'utilisateur.
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email")
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response
) -> None:
    """Endpoint de déconnexion.
    
    Args:
        current_user: Utilisateur courant (injecté via dépendance).
        response: La réponse HTTP.
        
    Note:
        En production, on pourrait invalider le token côté serveur (blacklist).
        Pour l'instant, on supprime juste le cookie refresh_token.
    """
    response.delete_cookie("refresh_token")
    logger.info(f"Utilisateur '{current_user['username']}' déconnecté")

