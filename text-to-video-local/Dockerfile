# Nvidia CUDA Base Image
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装 Python 和系统依赖
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.11 为默认
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 创建工作目录
WORKDIR /app

# 复制 requirements
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制应用程序
COPY generation.py ./
COPY config.yaml ./

# 创建模型目录
RUN mkdir -p /app/models /app/outputs

# 设置卷挂载点
VOLUME /app/models
VOLUME /app/outputs

# 设置入口点
ENTRYPOINT ["python3", "generation.py"]

# 默认命令
CMD ["--help"]
