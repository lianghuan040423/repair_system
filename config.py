import os

# ===== 关键：变量名必须是 SQLALCHEMY_DATABASE_URI（与 app.py 一致） =====
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:530121@127.0.0.1:3306/repair_system?charset=utf8mb4'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = False

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}