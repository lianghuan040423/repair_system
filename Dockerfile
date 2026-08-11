FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件并安装（使用国内镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制所有代码
COPY . .

# 创建上传目录
RUN mkdir -p static/uploads

# 暴露端口（与 app.py 中的 port=5000 一致）
EXPOSE 5000

# 直接用 Python 启动，避免 gunicorn 找不到的问题
CMD ["python", "app.py"]