# iniForge: Bulk Settings Precision

**iniForge** is a tool designed for precision management of bulk settings.

## Description
iniForge is a Python based configuration GUI tool, designed for managing large-scale .ini ecosystems.

It features a Bulk Change Editor for simultaneous multi-file updates and Advanced Filtering to navigate high-volume data. The tool harnesses Meld comparison tool (if installed) for diff-validation, ensuring structural and syntax integrity across complex projects.

Key Features:
- Bulk attribute editing
- Multi-variable directory filtering
- Meld-powered diff validation

## License & Pricing

iniForge is **free for personal and educational use**. 

For professional and commercial use, a paid license is required:
* **Small Team (1-3 users):** $300/year
* **Enterprise (4+ users):** $300 + $79 per additional user/year

For commercial licensing inquiries, please contact **ariklevi@gmail.com**.
See the [LICENSE](LICENSE) file for full details.

## Installation

### Prerequisites
* Python 3.9 or higher

### First Time Setup (Development)

1. Create a Python virtual environment:
   ```bash
   # Ensure Python 3.9+ is installed
   python3.9 -m venv ~/iniforge_env
   ```

2. Activate the virtual environment:
   ```bash
   source ~/iniforge_env/bin/activate
   ```

3. Install required dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

### Formal Package Installation
Use this method if you are installing from a pre-built wheel file.

1. Activate the virtual environment:
   ```bash
   source ~/iniforge_env/bin/activate
   ```

2. Install the package:
   ```bash
   python -m pip install iniforge-1.0.0-py3-none-any.whl
   ```

## Usage

### Running from Source
```bash
source ~/iniforge_env/bin/activate
python iniforge.py &
```

### Standard Execution
Once installed as a package:
```bash
source ~/iniforge_env/bin/activate
iniforge &
```
