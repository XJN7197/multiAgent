# 图片审核系统后端 (Python Flask)

这是一个使用 Python Flask 框架构建的图片审核系统后端。它接收前端上传的图片，并调用智谱 AI 大模型进行内容审核。

## 启动流程

请按照以下步骤启动后端服务：

### 1. 进入后端项目目录

```bash
cd image_moderation_backend
```

### 2. 创建并激活 Python 虚拟环境

建议使用虚拟环境来管理项目依赖，以避免与系统其他 Python 环境冲突。

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

安装项目所需的 Python 库，包括 `zai-sdk` (智谱 AI SDK) 和 `Flask`。

```bash
pip install zai-sdk Flask Flask-Cors
```

### 4. 设置智谱 AI API Key

为了安全起见，API Key 不应直接硬编码在代码中。请将其设置为环境变量。

```bash
export ZHIPU_AI_API_KEY="your-api-key"
```

**请将 `your-api-key` 替换为您实际的 API Key：`46f176ccfbae4c65b96486b63641559e.GGoe1Lchz2zEJBI1`**

### 5. 运行 Flask 应用

```bash
python app.py
```

后端服务将默认在 `http://127.0.0.1:5001` 启动。您可以在终端中看到类似以下的输出：

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
```

现在，后端服务已成功启动并等待前端请求。