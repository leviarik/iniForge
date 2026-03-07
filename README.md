# iniForge: Bulk Settings Precision

**iniForge** is a tool designed for precision management of bulk settings.

<img src="screenshots/iniForge - look and layout.png" width="800">

## Description
iniForge is a Python based configuration GUI tool, designed for managing large-scale .ini ecosystems.

It features a Bulk Change Editor for simultaneous multi-file updates and Advanced Filtering to navigate high-volume data. The tool harnesses Meld comparison tool (if installed) for diff-validation, ensuring structural and syntax integrity across complex projects.

Key Features:
- Bulk attribute editing
- Multi-variable directory filtering
- Meld-powered diff validation

---

## License & Commercial Use

**iniForge** is free for all internal use, but requires a paid license for commercial distribution.

### Free Internal Use
Any individual, non-profit, or **commercial organization** may download and use iniForge **free of charge** for their own internal operations, development, and configuration management.

### Paid Commercial Licensing
A paid license and express written permission are **strictly required** if you intend to:
* **Redistribute:** Include iniForge as part of a product, service, or software package you sell or distribute to others.
* **Resell/Lease:** Sell access to the tool or rent it out as a service (SaaS).
* **White-Label:** Modify and sell the tool under your own brand name.
* **Commercial Integration:** Embed the tool's logic into a commercial offering for third parties.

#### Commercial Rates for Redistribution:
* **Base License:** $300 / year (covers initial integration/redistribution).
* **Scalable Tier:** $79 / year per end-user/seat provided to your customers.

For commercial redistribution inquiries, please contact: **ariklevi@gmail.com**
*See the [LICENSE](LICENSE) file for the full legal terms.*

---

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
python iniforge_runner.py &
```

### Standard Execution
Once installed as a package:
```bash
source ~/iniforge_env/bin/activate
iniforge &
```
