# 使用 Python 3.10 官方轻量镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量（避免 Python 缓冲输出，便于实时查看日志）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件并安装（使用阿里云镜像加速，避免超时）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制项目所有代码到容器（包括 app.py, config.py, models.py 等）
COPY . .

# 创建图片上传目录（防止运行时报错目录不存在）
RUN mkdir -p static/uploads

# 暴露端口（微信云托管默认使用 5000）
EXPOSE 5000

# 启动命令：使用 gunicorn 运行 app 实例（-w 4 表示 4 个工作进程，可根据性能调整）
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]