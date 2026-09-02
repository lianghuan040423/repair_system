import os
from pathlib import Path
from dotenv import load_dotenv


SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres.swlrysmkmtovstgmfkst:530121Lianghuan@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
)

=======
# 定位 .env 文件（与 config.py 同级）
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ===== 数据库连接配置 =====
# 优先从环境变量 DATABASE_URL 读取，若未设置则使用默认值（本地 MySQL）
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:530121lh@localhost:3306/repair_system?charset=utf8mb4'
)

# 关闭 SQLAlchemy 事件跟踪（提高性能）
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 确保 Flask 返回的 JSON 使用 UTF-8 编码（支持中文）
JSON_AS_ASCII = False


SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}
# ===== 其他可选配置（可根据需要添加） =====
# SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
# DEBUG = False
