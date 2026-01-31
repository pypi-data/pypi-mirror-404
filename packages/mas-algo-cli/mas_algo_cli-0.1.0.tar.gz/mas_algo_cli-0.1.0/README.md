# mas-algo-cli

华为云盘古大模型服务算法包开发和打包 CLI 工具。

## 要求

- Python >= 3.9（托管环境使用 Python 3.9）

## 安装

```bash
pip install -e .
```

## 使用

### 创建新项目

```bash
algo new my-algo
```

模板选项：
- `basic` - 最小服务骨架
- `predict` - 预测/ML（使用 pandas）
- `cv` - 计算机视觉（使用 OpenCV）

`algo new` 会自动：
1. 创建项目目录和文件
2. 创建虚拟环境 (`.venv`)
3. 安装 `rest-stubs` 包（提供 IDE 支持）

### 本地运行

```bash
cd my-algo
# 激活虚拟环境并安装依赖
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 MODEL_URL

# 运行服务
algo run
```

**注意：**
- `algo new` 已自动创建 `.venv` 并安装 `rest-stubs`
- `algo run` 会自动检测并使用项目目录中的 `.venv` 虚拟环境
- 如果没有找到 `.venv`，将使用当前 Python 解释器

### 调试

1. 生成 VS Code 调试配置：
   ```bash
   algo debug
   ```

2. 以调试模式运行：
   ```bash
   algo run --debug
   ```

3. 在 VS Code 中附加调试器：
   - 打开项目文件夹
   - 按 `Cmd+Shift+D` 打开调试面板
   - 选择 **"Attach to Algo Service"**
   - 按 `F5`

4. 在 `main.py` 中设置断点，然后发送请求：
   ```bash
   curl -X POST http://localhost:8080/ -H "Content-Type: application/json" -d '{"value": "test"}'
   ```

### 打包部署

```bash
algo pack
```

生成 `.tar.gz` 文件用于上传。

## 项目结构

```
my-algo/
├── .venv/            # 虚拟环境（本地开发）
├── main.py           # AlgoProcessor 类（必需）
├── requirements.txt  # 基础镜像中未包含的依赖
├── dependency/       # 离线 .whl 包
├── lib/              # .so 动态库（可选）
└── .env              # 环境变量
```

## 基础镜像依赖

托管环境已预装约 150 个包：

| 类别 | 包 |
|------|-----|
| 核心库 | numpy 1.26.4, pandas 2.1.2, scipy 1.11.2 |
| 机器学习 | scikit-learn 1.0.2, xgboost 1.6.2, lightgbm 3.3.5 |
| 深度学习 | tensorflow 2.16.1, keras 3.9.0, torch 1.13.1 |
| 图像处理 | opencv-python 4.7.0.72, pillow 11.2.1 |
| 网络框架 | flask 3.0.0, requests 2.32.0, aiohttp 3.12.11 |
| 分布式 | ray 2.46.0 |

完整列表见 `host_env.txt`。

## 添加依赖

对于基础镜像中未包含的包：

1. 下载 `.whl` 文件
2. 放入 `dependency/` 目录
3. 在 `requirements.txt` 中添加：
   ```
   dependency/your-package-1.0.0-py3-none-any.whl
   ```
