"""
Cortex MCP - Web Configuration
환경별 설정 (로컬/Cloud Run)
"""

import os

# 환경 변수 (기본값: local)
ENV = os.getenv("ENV", "local")  # local | production

# Cloud Run 환경 감지 (K_SERVICE 환경 변수 존재 여부)
IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None

# 환경 자동 설정
if IS_CLOUD_RUN and ENV == "local":
    ENV = "production"

# 환경별 설정
if ENV == "production":
    # Cloud Run (Firestore)
    STORAGE_BACKEND = "firestore"
    print("[INFO] Running in PRODUCTION mode (Firestore)")
else:
    # 로컬 개발 (SQLite)
    STORAGE_BACKEND = "sqlite"
    print("[INFO] Running in LOCAL mode (SQLite)")


def get_database():
    """환경에 맞는 Database 인스턴스 반환"""
    if STORAGE_BACKEND == "firestore":
        from models_firestore import get_db
    else:  # sqlite
        from models import get_db

    return get_db()
