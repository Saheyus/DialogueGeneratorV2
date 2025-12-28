"""Service d'authentification pour l'API."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from api.exceptions import AuthenticationException
from api.config.security_config import get_security_config

logger = logging.getLogger(__name__)

# Configuration JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    """Service pour gérer l'authentification et les tokens JWT."""
    
    def __init__(self):
        """Initialise le service d'authentification."""
        security_config = get_security_config()
        self.secret_key = security_config.jwt_secret_key
        self.algorithm = ALGORITHM
        self.access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # TODO: En production, utiliser une vraie base de données
        # Pour l'instant, utilisateurs en dur (à remplacer)
        # Hash pré-calculé pour "admin123" (généré avec bcrypt.hashpw(b'admin123', bcrypt.gensalt()))
        # On utilise bcrypt directement au lieu de passlib pour éviter les problèmes de compatibilité
        admin_password_hash = "$2b$12$U975No5LwfSx0GpHZmMwXeJYUyMGsVdEgaLfOgAqDSd.qgPHt4V/i"
        
        self._users_db = {
            "admin": {
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": admin_password_hash,
                "id": "1"
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe.
        
        Args:
            plain_password: Mot de passe en clair.
            hashed_password: Mot de passe hashé.
            
        Returns:
            True si le mot de passe correspond, False sinon.
        """
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe.
        
        Args:
            password: Mot de passe en clair.
            
        Returns:
            Mot de passe hashé.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authentifie un utilisateur.
        
        Args:
            username: Nom d'utilisateur.
            password: Mot de passe.
            
        Returns:
            Dictionnaire avec les informations de l'utilisateur si authentifié, None sinon.
        """
        user = self._users_db.get(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email")
        }
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token d'accès JWT.
        
        Args:
            data: Données à encoder dans le token.
            expires_delta: Durée de validité du token (optionnel).
            
        Returns:
            Token JWT encodé.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.access_token_expire
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Crée un token de rafraîchissement JWT.
        
        Args:
            data: Données à encoder dans le token.
            
        Returns:
            Token JWT encodé.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + self.refresh_token_expire
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """Vérifie et décode un token JWT.
        
        Args:
            token: Token JWT à vérifier.
            token_type: Type de token attendu ("access" ou "refresh").
            
        Returns:
            Données décodées du token si valide, None sinon.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Vérifier le type de token
            if payload.get("type") != token_type:
                return None
            
            return payload
        except JWTError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Récupère un utilisateur par son nom d'utilisateur.
        
        Args:
            username: Nom d'utilisateur.
            
        Returns:
            Dictionnaire avec les informations de l'utilisateur ou None.
        """
        user = self._users_db.get(username)
        if user:
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email")
            }
        return None

