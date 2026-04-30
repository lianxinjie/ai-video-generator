# AI 视频生成 - Docker 部署配置
# 支持 GPU 和 CPU 两种模式

# ==================== GPU 模式 ====================
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS base-gpu

LABEL maintainer="AI Video Generator"
LABEL description="Text-to-Video GPU Deployment"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/cache/huggingface
ENV MODELSCOPE_CACHE=/app/cache/modelscope
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && ln -sf /usr/bin/pip3.10 /usr/bin/pip3

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip3 install --break-system-packages \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install --break-system-packages -r requirements.txt

# 复制应用代码
COPY generation.py .
COPY download_models.py .
COPY scanner.py .

# 创建输出目录
RUN mkdir -p /app/outputs /app/models /app/cache

# 挂载点
VOLUME ["/app/outputs", "/app/models", "/app/cache"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)"

# 默认命令
ENTRYPOINT ["python3", "generation.py"]
CMD ["--help"]


# ==================== CPU 模式 ====================
FROM ubuntu:22.04 AS base-cpu

LABEL maintainer="AI Video Generator"
LABEL description="Text-to-Video CPU Deployment"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/cache/huggingface
ENV MODELSCOPE_CACHE=/app/cache/modelscope
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && ln -sf /usr/bin/pip3.10 /usr/bin/pip3

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（CPU 版本）
RUN pip3 install --break-system-packages torch torchvision torchaudio

RUN pip3 install --break-system-packages -r requirements.txt

# 复制应用代码
COPY generation.py .
COPY download_models.py .
COPY scanner.py .

# 创建输出目录
RUN mkdir -p /app/outputs /app/models /app/cache

# 挂载点
VOLUME ["/app/outputs", "/app/models", "/app/cache"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; exit(0)"

# 默认命令
ENTRYPOINT ["python3", "generation.py"]
CMD ["--help"]


# ==================== 精简模式（推荐生产使用） ====================
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS slim

LABEL maintainer="AI Video Generator"
LABEL description="Text-to-Video Slim Deployment"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/cache/huggingface

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 只安装必要依赖
COPY requirements.txt .
RUN pip3 install --break-system-packages \
    torch --index-url https://download.pytorch.org/whl/cu121 \
    && pip3 install --break-system-packages \
    diffusers transformers accelerate modelscope \
    opencv-python imageio imageio-ffmpeg numpy pillow tqdm

COPY generation.py .

RUN mkdir -p /app/outputs

VOLUME ["/app/outputs"]

ENTRYPOINT ["python3", "generation.py"]
CMD ["--help"]
