
<div align="center">

# 📦 Universal Agent File (UAF) Compiler & Protocol

**The Standard Binary Format for Plug-and-Play AI Agents**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Active-success)]()

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Protocol](#-protocol-specification) •
[Integration](#-langgraph-integration)

</div>

---

## 🚀 Overview

The **Universal Agent File (UAF)** is a standardized binary format and protocol designed to solve the fragmentation in AI agent distribution. It packages agent implementation code, dependencies, metadata, and tool definitions into a single, portable, and verifiable `.uaf` artifact (gzip-compressed tarball).

The **UAF Compiler** is the CLI toolchain that empowers developers to **build**, **validate**, **inspect**, and **run** these agents, making them truly "plug-and-play" across diverse runtime environments like LangChain and LangGraph.

## ✨ Features

- **📦 Standardized Packaging**: Bundles code, assets, and definitions into a unified signed-like `.uaf` binary.
- **🛡️ Strict Validation**: Enforces schema compliance (`agent.yaml`) and ensures all dependencies and entrypoints are valid before build.
- **🔍 Deep Inspection**: Introspect agent metadata, versioning, and capabilities without needing to extract or run code.
- **🔌 Runtime Loader**: Dynamic Python API to load execution graphs directly from `.uaf` files into host applications.
- **🖥️ Cross-Platform**: Native installers for **Windows** (MSI with PATH integration) and **Linux** (DEB packages).

## 🛠️ Installation

### 🪟 Windows
Download and run the MSI installer. It automatically configures your system `PATH`.
*Default Location:* `C:\Program Files\UAFCompiler`

### 🐧 Linux (Debian/Ubuntu)
Install via the standardized DEB package:
```bash
sudo apt install ./uaf-compiler_0.1.0-1_all.deb
```
*Note: Automatically resolves dependencies like `python3-pydantic`.*

### 🐍 From Source
```bash
git clone https://github.com/your-username/uaf-compiler.git
cd uaf-compiler
pip install .
```

## ⚡ Quick Start: Zero to Agent

How to turn your local python files into a portable, plug-and-play **Universal Agent**.

### 1. Prepare Your Folder
Assume you have a directory with your agent code:

```text
my-agent/
├── agent.py                # Your logic (LangGraph, LangChain, etc.)
├── requirements.txt        # Dependencies
├── agent.yaml              # Metadata (Name, version, tools)
└── uaf_setup.yaml          # Build instructions
```

### 2. Configure the Build
Create a `uaf_setup.yaml` to tell the compiler what files to include. This is the **bridge** between your folder and the UAF binary.

```yaml
# uaf_setup.yaml
output: my-agent.uaf
files:
  agent.yaml: ./agent.yaml
  agent.py: ./agent.py
  requirements.txt: ./requirements.txt
  # Add any other folders or assets:
  # tools/: ./tools/
```

### 3. Compile
Run the compiler in your terminal. This validates your schema, checks paths, and signs the bundle.

```bash
uaf compile -f uaf_setup.yaml
```

**✅ Success!** You now have `my-agent.uaf`. 
This single file contains everything needed to run your agent anywhere the UAF runtime is installed.

---

## 💻 CLI Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| **`compile`** | `uaf compile -f <config>` | **Convert folder → .uaf**. Builds the binary artifact. |
| **`validate`** | `uaf validate <file.uaf>` | Checks if a `.uaf` file is valid and safe to load. |
| **`inspect`** | `uaf inspect <file.uaf>` | Peek inside a UAF file (view metadata/files) without extracting. |
| **`run`** | `uaf run <file.uaf>` | Spin up the agent in a sandbox for immediate testing. |

---

## 🔗 LangGraph Integration

Plug your compiled agent directly into your application.

```python
from uaf_compiler.loader import UAFLoader
from langgraph.graph import StateGraph

# Load from file - no loose scripts required
loader = UAFLoader("my-agent.uaf")

# Load and inject dependencies in one step
agent_node = loader.load(llm=llm)

# Add to graph
graph.add_node("agent", agent_node)
```

---

## 📝 Configuration Reference

### The Manifest (`agent.yaml`)
Required file describing the agent's identity.

```yaml
version: "1.0"
format: "uaf"
name: "math-solver"
type: "langgraph"
runtime: "python"
entrypoint: "agent.py:create_agent"
tools: [] 
metadata:
    author: "Me"
    version: "1.0.0"
```

## 🏗️ Development

### Build Artifacts
**Windows (MSI)**
```bash
python setup_win.py bdist_msi
```

**Linux (DEB)**
```bash
./build_deb.sh
```

---

<div align="center">
    <sub>Built with ❤️ by Vaibhav Haswani as a part of DefaultLoop Project. Released under Apache 2.0 License.</sub>
</div>
