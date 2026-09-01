import os
<<<<<<< HEAD
from dotenv import load_dotenv
from pathlib import Path

# 定位 .env 文件
env_path = Path(__file__).parent / '.env'

# ========== 调试打印 ==========
#print("【调试】当前 config.py 所在目录：", Path(__file__).parent)
#print("【调试】期望的 .env 路径：", env_path)
#print("【调试】该路径是否存在？", env_path.exists())
# ==============================

# 强制加载，并指定编码（避免中文乱码问题）
load_dotenv(dotenv_path=env_path, encoding='utf-8')

# 读取环境变量
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
print("【调试】从环境变量读取到的 DATABASE_URL：", SQLALCHEMY_DATABASE_URI)  # 看看是 None 还是有内容

if not SQLALCHEMY_DATABASE_URI:
    raise ValueError("错误：未找到 DATABASE_URL 环境变量，请在 .env 文件中配置！")

# ===== 以下内容保持不变 =====
=======

# ===== 关键：变量名必须是 SQLALCHEMY_DATABASE_URI（与 app.py 一致） =====
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:530121@10.0.0.17:3306/repair_system?charset=utf8mb4'
)
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = False

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}