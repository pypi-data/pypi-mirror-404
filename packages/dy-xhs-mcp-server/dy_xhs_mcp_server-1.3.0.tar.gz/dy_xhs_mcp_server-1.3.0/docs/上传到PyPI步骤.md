# 将本项目上传到 PyPI

## 一、前置准备

### 1. 注册 PyPI 并创建 Token

- 注册账号：<https://pypi.org/account/register/>
- 创建 API Token：<https://pypi.org/manage/account/token/>
- 复制 Token（格式：`pypi-xxxxx`），**只显示一次，请妥善保存**

### 2. 配置上传凭证（二选一）

**方式 A：环境变量（推荐，CI 或临时使用）**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-你的token
```

**方式 B：本地配置文件**

创建或编辑 `~/.pypirc`：

```ini
[pypi]
username = __token__
password = pypi-你的token
```

---

## 二、上传步骤

### 步骤 1：安装构建与上传工具

```bash
pip install build twine
```

### 步骤 2：在项目根目录构建

```bash
cd /path/to/dy-xhs-mcp-server-main
python -m build
```

构建成功后会在 `dist/` 下生成 `.whl` 和 `.tar.gz` 文件。

### 步骤 3：先传到 TestPyPI（可选，建议第一次时做）

```bash
python -m twine upload --repository testpypi dist/*
```

测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ douyin-xhs-mcp-server
```

### 步骤 4：上传到正式 PyPI

```bash
python -m twine upload dist/*
```

按提示输入用户名（填 `__token__`）和密码（填 Token），或已配置好则直接上传。

---

## 三、使用脚本上传（可选）

项目自带脚本，在**项目根目录**执行：

```bash
cd /path/to/dy-xhs-mcp-server-main
python scripts/upload_to_pypi.py
```

脚本会检查 `dist/` 是否已有当前版本的构建产物，确认后执行上传。

---

## 四、验证是否上传成功

```bash
# 查看包信息
pip show douyin-xhs-mcp-server

# 或安装一次
pip install douyin-xhs-mcp-server
```

浏览器访问：<https://pypi.org/project/douyin-xhs-mcp-server/>

---

## 五、发布新版本时

1. 在 `pyproject.toml` 中修改 `version`（如 `1.3.0` → `1.3.1`）
2. 重新执行「二、上传步骤」中的构建和上传命令
3. PyPI **不允许覆盖或删除已发布版本**，只能发布更高版本；若误发可到 PyPI 该版本页选择 “Yank” 撤回

---

## 常见问题

| 问题 | 处理 |
|------|------|
| `Invalid or non-existent authentication information` | 检查 `TWINE_USERNAME=__token__` 和 Token 是否正确 |
| `File already exists` | 该版本已存在，需在 `pyproject.toml` 中提高版本号后再传 |
| `command not found: python` | 使用 `python3` 替代，或先 `pip install build twine` |
| 上传后 pip 仍装到旧版 | 等 1～2 分钟再试，或使用 `pip install douyin-xhs-mcp-server==x.y.z` 指定版本 |

更多细节见：`docs/UPLOAD_TO_PYPI.md`、`docs/VERIFY_UPLOAD.md`。
