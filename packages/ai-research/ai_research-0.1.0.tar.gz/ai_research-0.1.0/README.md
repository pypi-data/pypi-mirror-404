# AIR SDK

Python SDK for the AIR Backend API.

## Installation

```bash
pip install air-sdk
```

## Quick Start

```python
import air

client = air.AIR(api_key="air_k1_...", base_url="http://localhost:8000")

# Standalone tools
keywords = client.keywords("dark matter and lensing", n=5, kw_type="aas")
enhanced = client.enhance("My research with https://arxiv.org/abs/2301.12345")

# Full research workflow
project = client.create_project("my-research", data_description="We study...")
idea = project.idea()
project.literature()
project.methods()
project.paper(journal="AAS")
review = project.review()

# File access
print(project.get_file("Iteration0/input_files/idea.md"))
print(project.list_files())
```

## Configuration

Set `AIR_API_KEY` and optionally `AIR_BASE_URL` as environment variables, or pass them directly:

```python
client = air.AIR(api_key="air_k1_...", base_url="https://api.example.com")
```

## API Reference

### `AIR` class

| Method | Description |
|--------|-------------|
| `keywords(text, n=5, kw_type="unesco")` | Extract keywords |
| `arxiv(text)` | Download arXiv papers from URLs in text |
| `enhance(text, max_workers=2, max_depth=10)` | Enhance text with arXiv context |
| `ocr(file_path)` | Process PDF with OCR (server path) |
| `create_project(name, data_description, iteration)` | Create a project |
| `get_project(name)` | Get existing project |
| `list_projects()` | List all projects |
| `delete_project(name)` | Delete a project |

### `Project` class

| Method | Description |
|--------|-------------|
| `idea(mode="fast", timeout=600)` | Generate research idea |
| `literature(timeout=600)` | Run literature search |
| `methods(mode="fast", timeout=600)` | Develop methods |
| `paper(journal="NONE", timeout=900)` | Write paper |
| `review(timeout=600)` | Run review |
| `get_file(path)` | Read a project file |
| `list_files()` | List all project files |
| `write_file(path, content)` | Write a file |
| `delete()` | Delete the project |
