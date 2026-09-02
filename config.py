import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres.swlrysmkmtovstgmfkst:530121Lianghuan@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = False

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}
