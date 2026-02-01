# How to Use

## 使用 pyenv + pip 运行
```bash
pyenv shell 3.12.10
python -m venv .venv
source .venv/bin/activate 
pip install .
```

## 使用 uv 运行
```bash
uv sync
source .venv/bin/activate 
uv pip install .
uv run python xxx.py
```

## 打包发布到 pypi
```bash
uv build
export UV_PUBLISH_TOKEN=pypi-xxx
uv publish
```