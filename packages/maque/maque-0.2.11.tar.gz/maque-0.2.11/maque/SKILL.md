---
name: maque
description: >
  当用户需要文本嵌入、向量检索、聚类分析、模型部署或常用 ML 工具时使用此 skill。
  提供 CLI 工具 `maque` 和 Python API。
  适用场景：(1) 文本嵌入：TextEmbedding 支持本地模型或 API，embed()/embed_batch()；
  (2) 向量检索：ChromaRetriever/MilvusRetriever 支持 upsert_batch、search、增量更新；
  (3) 聚类分析：ClusterAnalyzer 支持 hdbscan/kmeans/dbscan + ClusterVisualizer 可视化；
  (4) 模型部署：maque serve 启动 embedding/LLM 服务(vLLM 后端)；
  (5) MLLM 批量处理：maque mllm call-table/call-images 批量调用多模态模型；
  (6) 通用工具：yaml_load/json_load/jsonl_load IO、MeasureTime 计时、relp 相对路径；
  (7) 模型量化：maque quant auto-round/llmcompressor。
  注意：LLM 文本生成调用请用 flexllm，数据文件处理请用 dtflow。
---

# maque - ML 工具包

## 设计理念

- **模块化架构**：各组件独立可用，组合使用更强大
- **KISS 原则**：API 简洁直观，开箱即用
- **CLI 优先**：丰富的命令行工具，适合快速验证和脚本化

## Python API

### 文本嵌入

```python
from maque.embedding import TextEmbedding

# 初始化（支持本地模型或 API）
embedding = TextEmbedding(
    base_url="http://localhost:8001/v1",  # embedding 服务地址
    model="BAAI/bge-m3"
)

# 单文本嵌入
vector = embedding.embed("Hello world")

# 批量嵌入
vectors = embedding.embed_batch(["text1", "text2", "text3"])
```

### 向量检索 (ChromaDB)

```python
from maque.embedding import TextEmbedding
from maque.retriever import ChromaRetriever, Document

# 初始化
embedding = TextEmbedding(base_url="...", model="...")
retriever = ChromaRetriever(
    embedding,
    persist_dir="./chroma_db",
    collection_name="my_docs"
)

# 构建文档
docs = [
    Document(id="1", content="Python 是一种编程语言", metadata={"category": "tech"}),
    Document(id="2", content="机器学习改变世界", metadata={"category": "ai"}),
]

# 批量入库（支持增量更新）
retriever.upsert_batch(docs, batch_size=32, skip_existing=True)

# 检索
results = retriever.search("什么是 Python", top_k=5)
for r in results:
    print(f"{r.score:.3f} - {r.document.content}")
```

### 向量检索 (Milvus)

```python
from maque.retriever import MilvusRetriever

retriever = MilvusRetriever(
    embedding,
    uri="http://localhost:19530",
    collection_name="my_collection"
)

# API 与 ChromaRetriever 一致
retriever.upsert_batch(docs)
results = retriever.search("query", top_k=10)
```

### 聚类分析

```python
from maque.clustering import ClusterAnalyzer

# 初始化分析器
analyzer = ClusterAnalyzer(
    algorithm="hdbscan",     # hdbscan/kmeans/dbscan
    min_cluster_size=15
)

# 直接从 ChromaDB 分析
result = analyzer.analyze_chroma(
    persist_dir="./chroma_db",
    collection_name="my_docs",
    output_dir="./results",
    sample_size=10000,       # 大数据集采样
    where={"category": "ai"} # 可选过滤
)

# 结果包含
print(result.n_clusters)     # 聚类数
print(result.labels)         # 每个样本的聚类标签
print(result.cluster_sizes)  # 各聚类大小
```

### 聚类可视化

```python
from maque.clustering import ClusterVisualizer

visualizer = ClusterVisualizer(method="umap")  # umap/tsne/pca

# 生成可视化
visualizer.plot(
    embeddings=result.embeddings,
    labels=result.labels,
    output_path="clusters.html",
    interactive=True  # 交互式 HTML
)
```

## CLI 命令

```bash
# 启动 Embedding 服务
maque embedding serve --model=BAAI/bge-m3 --port=8001

# 启动 LLM 服务
maque llm serve Qwen/Qwen2.5-7B-Instruct --port=8000

# 模型统一服务（自动检测类型）
maque serve <model_name> --port=8000

# 表格数据可视化
maque data table-viewer data.xlsx

# MLLM 批量处理表格
maque mllm call-table data.xlsx --image_col="image_path"

# MLLM 批量处理文件夹
maque mllm call-images ./photos --recursive=True

# 系统工具
maque system kill 8000 8001      # 杀死端口进程
maque system pack ./folder       # 压缩文件夹
maque system split large.tar.gz  # 分割大文件

# 配置管理
maque config show                # 显示配置
maque config edit                # 编辑配置

# 模型量化
maque quant auto-round <model>   # AutoRound 量化
maque quant llmcompressor <model> # LLMCompressor 量化

# Skill 管理
maque install-skill              # 安装 skill 到 Claude Code
maque uninstall-skill            # 卸载 skill
maque skill-status               # 查看安装状态
```

## 常用工具

### IO 工具

```python
from maque import yaml_load, yaml_dump, json_load, json_dump
from maque import jsonl_load, jsonl_dump, save, load

# YAML
config = yaml_load("config.yaml")
yaml_dump("output.yaml", config)

# JSON
data = json_load("data.json")
json_dump("output.json", data)

# JSONL（流式）
for item in jsonl_load("data.jsonl"):
    process(item)
jsonl_dump("output.jsonl", items)

# 通用接口（自动识别格式）
data = load("file.yaml")  # 或 .json, .jsonl
save("output.json", data)
```

### 性能计时

```python
from maque import MeasureTime

with MeasureTime("数据处理"):
    process_data()
# 输出: 数据处理: 1.23s

# 支持 GPU 同步
with MeasureTime("模型推理", sync_cuda=True):
    model.forward(x)
```

### 路径工具

```python
from maque import relp, ls, rel_path_join

# 相对路径转绝对路径（相对于调用文件）
config_path = relp("../config/settings.yaml")

# 列出目录文件
files = ls("./data", pattern="*.jsonl")

# 相对路径拼接
path = rel_path_join(__file__, "../models", "bert")
```

## 配置文件

配置文件搜索路径（按优先级）：
1. 当前目录: `./maque_config.yaml`
2. 项目根目录: `<project>/maque_config.yaml`
3. 用户目录: `~/.maque/config.yaml`

```yaml
# ~/.maque/config.yaml
mllm:
  default: "gpt4"  # 默认使用的模型名称
  models:
    - name: "gpt4"
      id: "gpt-4o"
      base_url: "https://api.openai.com/v1"
      api_key: "sk-xxx"
      provider: "openai"
    - name: "local"
      id: "Qwen/Qwen2.5-7B-Instruct"
      base_url: "http://localhost:8000/v1"
      api_key: "EMPTY"
```

## 依赖安装

```bash
# 基础安装
pip install maque

# 带特定功能
pip install maque[embedding]     # 文本嵌入
pip install maque[retriever]     # 向量检索
pip install maque[clustering]    # 聚类分析
pip install maque[torch]         # PyTorch 支持
pip install maque[all]           # 全部功能
```
