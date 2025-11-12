# 🚨 Corrections Prioritaires - AutoCut

Ce document liste les corrections à faire **immédiatement** avant tout déploiement.

---

## 🔴 CRITIQUE - À CORRIGER MAINTENANT

### 1. Ajouter l'Authentification

**Fichier:** `backend/api/auth.py` (nouveau)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Générer avec: openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str
    disabled: bool = False

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Récupérer l'utilisateur de la DB
    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user

# Route de login
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

**Utilisation dans les routes:**

```python
from .auth import get_current_user, User

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),  # ✅ Auth requise
    ...
):
    # Associer le job à l'utilisateur
    JobRepository.create_job(
        db=db,
        job_id=job_id,
        user_id=current_user.id,  # ✅ Traçabilité
        ...
    )
```

**Dépendances à ajouter:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

---

### 2. Corriger CORS

**Fichier:** `backend/main.py`

```python
# ❌ AVANT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ APRÈS
from .config import settings

CORS_ORIGINS = {
    "development": ["http://localhost:5173"],
    "production": [
        "https://autocut.com",
        "https://www.autocut.com"
    ]
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.get(settings.ENVIRONMENT, ["http://localhost:5173"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**Ajouter dans settings.py:**
```python
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
```

---

### 3. Valider Taille des Fichiers

**Fichier:** `backend/api/routes.py`

```python
@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    ...
):
    # ✅ Ajouter validation de taille
    total_size = 0
    temp_file = settings.UPLOAD_DIR / f"temp_{job_id}"

    try:
        async with aiofiles.open(temp_file, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)

                # Vérifier la limite
                if total_size > settings.MAX_FILE_SIZE:
                    # Nettoyer
                    if temp_file.exists():
                        temp_file.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"Fichier trop volumineux. Taille max: {settings.MAX_FILE_SIZE / (1024**3):.1f}GB"
                    )

                await f.write(chunk)

        # Renommer si succès
        upload_path = settings.UPLOAD_DIR / f"{job_id}_{file.filename}"
        temp_file.rename(upload_path)

    except HTTPException:
        raise
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise
```

---

### 4. Valider tous les Inputs

**Fichier:** `backend/api/models.py` (nouveau)

```python
from pydantic import BaseModel, Field, validator
from typing import Literal
from uuid import UUID

class UploadSettings(BaseModel):
    """Validation stricte des paramètres d'upload"""

    silence_threshold: int = Field(
        default=-40,
        ge=-60,
        le=-20,
        description="Silence threshold in dB"
    )

    min_silence_duration: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Minimum silence duration in ms"
    )

    padding: int = Field(
        default=100,
        ge=0,
        le=1000,
        description="Padding in ms"
    )

    fps: int = Field(
        default=30,
        description="Frames per second"
    )

    detect_filler_words: bool = False

    filler_sensitivity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0
    )

    whisper_model: Literal["tiny", "base", "small", "medium", "large"] = "base"

    enable_audio_enhancement: bool = False

    noise_reduction_strength: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0
    )

    processing_mode: Literal["local", "gpt4"] = "local"

    @validator('fps')
    def validate_fps(cls, v):
        allowed_fps = [23, 24, 25, 29, 30, 50, 60, 120]
        if v not in allowed_fps:
            raise ValueError(f'FPS must be one of {allowed_fps}')
        return v

class JobIdPath(BaseModel):
    """Validation UUID pour job_id"""
    job_id: UUID
```

**Utilisation:**
```python
from .models import UploadSettings, JobIdPath
from uuid import UUID

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    settings: UploadSettings = Depends()  # ✅ Validation auto
):
    # Les paramètres sont déjà validés
    pass

@router.get("/job/{job_id}")
async def get_job_status(job_id: UUID):  # ✅ Validation UUID auto
    job_id_str = str(job_id)
    # ...
```

---

### 5. Sécuriser les Subprocess

**Fichier:** `backend/utils/path_utils.py` (nouveau)

```python
import re
from pathlib import Path
from typing import Union

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Nettoie un nom de fichier de manière sécurisée

    Args:
        filename: Nom de fichier original
        max_length: Longueur maximale

    Returns:
        Nom de fichier sécurisé

    Raises:
        ValueError: Si le nom est invalide ou extension non supportée
    """
    # Extraire l'extension
    path = Path(filename)
    stem = path.stem
    ext = path.suffix.lower()

    # Validation stricte de l'extension
    ALLOWED_EXTENSIONS = {'.mp4', '.mov'}
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension non autorisée: {ext}")

    # Supprimer caractères dangereux
    stem = re.sub(r'[^\w\s-]', '', stem)
    # Remplacer espaces multiples et caractères de contrôle
    stem = re.sub(r'[\s\x00-\x1f]+', '_', stem)
    # Limiter la longueur
    stem = stem[:max_length]

    # Vérifier qu'il reste quelque chose
    if not stem or stem.isspace():
        stem = "video"

    return f"{stem}{ext}"


def safe_path(base_dir: Path, user_input: str, create_dirs: bool = False) -> Path:
    """
    Crée un chemin sûr sans directory traversal

    Args:
        base_dir: Répertoire de base autorisé
        user_input: Entrée utilisateur
        create_dirs: Créer les répertoires parents si nécessaire

    Returns:
        Chemin absolu sécurisé

    Raises:
        ValueError: Si directory traversal détecté
    """
    # Résoudre le chemin absolu
    base_resolved = base_dir.resolve()
    full_path = (base_dir / user_input).resolve()

    # Vérifier que le chemin est bien dans base_dir
    try:
        full_path.relative_to(base_resolved)
    except ValueError:
        raise ValueError(
            f"Directory traversal détecté: {user_input} sort de {base_dir}"
        )

    # Créer les répertoires si demandé
    if create_dirs and not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)

    return full_path
```

**Utilisation:**
```python
from ..utils.path_utils import sanitize_filename, safe_path

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), ...):
    # ✅ Nettoyer le nom de fichier
    try:
        safe_filename = sanitize_filename(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ✅ Créer un chemin sûr
    upload_path = safe_path(
        settings.UPLOAD_DIR,
        f"{job_id}_{safe_filename}"
    )

    # Maintenant safe pour subprocess
    # ...
```

---

## 🟠 IMPORTANT - À FAIRE RAPIDEMENT

### 6. Ajouter Rate Limiting

```bash
pip install slowapi
```

```python
# backend/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# backend/api/routes.py
from ..main import limiter

@router.post("/upload")
@limiter.limit("10/hour")
async def upload_video(request: Request, ...):
    pass

@router.post("/transcribe/{job_id}")
@limiter.limit("5/hour")
async def transcribe_video(request: Request, job_id: str):
    pass
```

---

### 7. Logging Structuré

```python
# backend/utils/logger.py
import logging
import json
from datetime import datetime
from typing import Any

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_event(self, event_type: str, level: str = "info", **kwargs: Any):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **kwargs
        }

        log_method = getattr(self.logger, level)
        log_method(json.dumps(log_entry))

# Utilisation
from ..utils.logger import StructuredLogger

logger = StructuredLogger("autocut.api")

@router.post("/upload")
async def upload_video(...):
    logger.log_event(
        "video_upload",
        user_id=current_user.id,
        filename=file.filename,
        size=total_size
    )
```

---

### 8. Exception Handling Uniforme

```python
# backend/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

class AutoCutException(Exception):
    def __init__(self, message: str, user_message: str = None, status_code: int = 500):
        self.message = message
        self.user_message = user_message or "Une erreur est survenue"
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(AutoCutException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "Authentification échouée", 401)

class ValidationError(AutoCutException):
    def __init__(self, message: str):
        super().__init__(message, "Données invalides", 400)

class VideoProcessingError(AutoCutException):
    def __init__(self, message: str):
        super().__init__(message, "Erreur de traitement vidéo", 500)

# Handler global
@app.exception_handler(AutoCutException)
async def autocut_exception_handler(request: Request, exc: AutoCutException):
    logger.error(f"Error: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.user_message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

---

## 📝 Checklist Avant Déploiement

```markdown
### Sécurité Critique
- [ ] Authentification JWT implémentée
- [ ] CORS configuré avec origines spécifiques
- [ ] Validation de taille de fichier active
- [ ] Tous les inputs validés avec Pydantic
- [ ] Chemins de fichiers sécurisés (sanitize_filename + safe_path)

### Sécurité Importante
- [ ] Rate limiting activé
- [ ] Logging structuré en place
- [ ] Exception handling uniforme
- [ ] Variables d'environnement sécurisées (.env non commité)
- [ ] OPENAI_API_KEY dans secrets manager

### Configuration
- [ ] ENVIRONMENT=production dans .env
- [ ] JWT_SECRET_KEY générée (openssl rand -hex 32)
- [ ] MAX_FILE_SIZE vérifié
- [ ] CORS_ORIGINS configuré

### Tests
- [ ] Tests des endpoints critiques
- [ ] Test de validation des inputs
- [ ] Test d'authentification
- [ ] Test de rate limiting

### Déploiement
- [ ] HTTPS/TLS configuré
- [ ] Nginx reverse proxy
- [ ] Firewall configuré
- [ ] Backup automatique
- [ ] Monitoring actif
```

---

## 🚀 Commandes Rapides

```bash
# Installer nouvelles dépendances
pip install python-jose[cryptography] passlib[bcrypt] slowapi

# Mettre à jour requirements.txt
pip freeze > requirements.txt

# Générer JWT secret
openssl rand -hex 32

# Tester l'API
pytest tests/ -v --cov=backend

# Vérifier la sécurité
pip install safety bandit
safety check
bandit -r backend/

# Lancer en production
ENVIRONMENT=production uvicorn backend.main:app --host 0.0.0.0 --port 8765 --workers 4
```

---

## ⏱️ Temps Estimé

- **Corrections critiques (1-5):** 2-3 jours
- **Corrections importantes (6-8):** 1-2 jours
- **Tests et validation:** 1 jour
- **Total:** ~1 semaine

---

**IMPORTANT:** Ne pas déployer en production sans ces corrections !
