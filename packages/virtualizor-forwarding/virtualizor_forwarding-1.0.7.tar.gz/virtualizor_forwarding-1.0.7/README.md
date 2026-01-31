# Virtualizor Forwarding Tool (vf)

<p align="center">
  <img src="https://img.shields.io/pypi/v/virtualizor-forwarding.svg" alt="PyPI Version">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey" alt="Platform">
</p>

<p align="center">
  <a href="https://sonarqube.rizzcode.id/dashboard?id=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3"><img src="https://sonarqube.rizzcode.id/api/project_badges/measure?project=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3&metric=alert_status&token=sqb_e60dd5ca23f95574dc0f802335bda3563a86cb81" alt="Quality Gate Status"></a>
  <a href="https://sonarqube.rizzcode.id/dashboard?id=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3"><img src="https://sonarqube.rizzcode.id/api/project_badges/measure?project=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3&metric=software_quality_security_rating&token=sqb_e60dd5ca23f95574dc0f802335bda3563a86cb81" alt="Security Rating"></a>
  <a href="https://sonarqube.rizzcode.id/dashboard?id=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3"><img src="https://sonarqube.rizzcode.id/api/project_badges/measure?project=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3&metric=software_quality_reliability_rating&token=sqb_e60dd5ca23f95574dc0f802335bda3563a86cb81" alt="Reliability Rating"></a>
  <a href="https://sonarqube.rizzcode.id/dashboard?id=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3"><img src="https://sonarqube.rizzcode.id/api/project_badges/measure?project=iam-rizz_python-domain-forwarding-virtualizor_288276e0-63bb-476b-a1a6-14ae07eee7a3&metric=ncloc&token=sqb_e60dd5ca23f95574dc0f802335bda3563a86cb81" alt="Lines of Code"></a>
</p>

### Recommended VPS, NAT VPS (Virtualizor) & Hosting

<div align="center">

Need a VPS to test this script? **[HostData.id](https://hostdata.id)** provides a wide selection of reliable hosting options at affordable prices.

[![HostData.id](https://img.shields.io/badge/HostData.id-VPS%20Trusted-FF6B35?style=flat&logo=server&logoColor=white)](https://hostdata.id) 
[![NAT VPS](https://img.shields.io/badge/NAT%20VPS-Start%20from%2015K/Month-00C851?style=flat)](https://hostdata.id/nat-vps)
[![VPS Indonesia](https://img.shields.io/badge/VPS%20Indonesia-Start%20from%20200K/Month-007ACC?style=flat&logo=server)](https://hostdata.id/vps-indonesia)
[![Dedicated Server](https://img.shields.io/badge/Dedicated%20Server-Enterprise%20Ready-8B5CF6?style=flat&logo=server)](https://hostdata.id/dedicated-server)

</div>

CLI tool for managing domain/port forwarding in Virtualizor VPS environments with multi-host support and Rich TUI.

> [!WARNING]
> This library is still in development, and prone for extreme changes. You have been warned.

**[🇮🇩 Baca dalam Bahasa Indonesia](README_ID.md)**

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration File](#configuration-file)
- [Commands Reference](#commands-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Host Support** | Manage multiple Virtualizor servers from a single interface |
| **Rich TUI** | Beautiful terminal output with tables, panels, spinners, and progress bars |
| **Connection Testing** | Test all hosts at once with API response time display |
| **CRUD Operations** | Easily add, edit, and delete forwarding rules |
| **Batch Operations** | Import/export rules in JSON format |
| **Secure Config** | Passwords stored with base64 encoding |
| **Python 3.8-3.13** | Compatible with various Python versions |
| **Interactive Mode** | Step-by-step mode for beginners |
| **JSON Output** | Export data in JSON format for scripting |

## Requirements

- Python 3.8 or newer
- Access to Virtualizor Panel with API credentials
- Network access to Virtualizor server

## Installation

### From PyPI (Recommended)

```bash
pip install virtualizor-forwarding
```

### From Source

```bash
git clone https://github.com/iam-rizz/python-domain-forwarding-virtualizor.git
cd python-domain-forwarding-virtualizor
pip install -e .
```

### Verify Installation

```bash
vf --help
```

> **Note:** Dependencies (`requests`, `rich`) will be automatically installed.

## Quick Start

```bash
# 1. Add host configuration
vf config add production \
  --url "https://panel.example.com:4083/index.php" \
  --key "YOUR_API_KEY" \
  --pass "YOUR_API_PASSWORD" \
  --default

# 2. Test connection
vf config test

# 3. List VMs
vf vm list

# 4. Add forwarding rule (interactive)
vf forward add -i
```

## Usage

### Version & Update

```bash
# Show version
vf --version
vf -V

# Show detailed about info
vf about

# Check for updates
vf update
```

### 1. Configuration

#### Add Host Profile

```bash
# Basic
vf config add myhost --url "https://panel.com:4083/index.php" --key "apikey" --pass "password"

# Set as default
vf config add myhost --url "https://panel.com:4083/index.php" --key "apikey" --pass "password" --default
```

#### Manage Host Profiles

```bash
# List all hosts
vf config list

# Set default host
vf config set-default production

# Test connection (all hosts)
vf config test

# Test specific host
vf config test staging

# Remove host
vf config remove staging
```

#### Use Specific Host

```bash
# Use --host or -H for operations with specific host
vf --host staging vm list
vf -H production forward list --vpsid 103
```

### 2. Virtual Machines

```bash
# List all VMs
vf vm list

# Filter by status
vf vm list --status up      # Only running VMs
vf vm list --status down    # Only stopped VMs

# List VMs from all hosts (with details per host)
vf vm list --all-hosts

# List running VMs from all hosts
vf vm list --all-hosts --status up

# List stopped VMs from all hosts
vf vm list --all-hosts --status down

# JSON output (for scripting)
vf vm list --json
vf vm list --status up --json
vf vm list --all-hosts --json
```

### 3. Port Forwarding

#### List Forwarding Rules

```bash
# Interactive (select VM from list)
vf forward list

# Direct to specific VM
vf forward list --vpsid 103
vf forward list -v 103

# Auto-select if only 1 VM
vf forward list --auto

# JSON output
vf forward list --vpsid 103 --json
```

#### Add Forwarding Rule

```bash
# Interactive mode (recommended for beginners)
vf forward add -i
vf forward add --interactive

# HTTP Forwarding (auto port 80)
vf forward add --vpsid 103 --protocol HTTP --domain app.example.com

# HTTPS Forwarding (auto port 443)
vf forward add --vpsid 103 --protocol HTTPS --domain secure.example.com

# TCP Forwarding (custom ports)
vf forward add \
  --vpsid 103 \
  --protocol TCP \
  --domain 45.158.126.xxx \
  --src-port 2222 \
  --dest-port 22

# Short options
vf forward add -v 103 -p HTTP -d app.example.com
vf forward add -v 103 -p TCP -d 45.158.126.xxx -s 2222 -t 22
```

#### Edit Forwarding Rule

```bash
# Interactive mode
vf forward edit -i

# Edit protocol (auto-update ports)
vf forward edit --vpsid 103 --vdfid 596 --protocol HTTPS

# Edit domain
vf forward edit --vpsid 103 --vdfid 596 --domain new.example.com

# Edit ports
vf forward edit --vpsid 103 --vdfid 596 --src-port 8080 --dest-port 80

# Short options
vf forward edit -v 103 -f 596 -p HTTPS -d new.example.com
```

#### Delete Forwarding Rule

```bash
# Interactive mode (with confirmation)
vf forward delete -i

# Delete single rule (with confirmation)
vf forward delete --vpsid 103 --vdfid 596

# Delete multiple rules
vf forward delete --vpsid 103 --vdfid 596,597,598

# Delete without confirmation
vf forward delete --vpsid 103 --vdfid 596 --force

# Short options
vf forward delete -v 103 -f 596
vf forward delete -v 103 -f 596,597 --force
```

### 4. Batch Operations

#### Export Rules

```bash
# Export to JSON file
vf batch export --vpsid 103 --to-file rules.json
vf batch export -v 103 -o backup.json
```

#### Import Rules

```bash
# Import from JSON file
vf batch import --vpsid 103 --from-file rules.json

# Dry run (validate without executing)
vf batch import --vpsid 103 --from-file rules.json --dry-run

# Short options
vf batch import -v 103 -f rules.json
vf batch import -v 103 -f rules.json --dry-run
```

## Configuration File

Config file is stored at `~/.config/virtualizor-forwarding/config.json`:

```json
{
  "hosts": {
    "production": {
      "name": "production",
      "api_url": "https://panel.example.com:4083/index.php",
      "api_key": "your_api_key",
      "api_pass": "base64_encoded_password"
    },
    "staging": {
      "name": "staging",
      "api_url": "https://staging.example.com:4083/index.php",
      "api_key": "staging_api_key",
      "api_pass": "base64_encoded_password"
    }
  },
  "default_host": "production",
  "version": "1.0"
}
```

### Batch Import/Export Format

```json
{
  "vpsid": "103",
  "rules": [
    {
      "protocol": "HTTP",
      "src_hostname": "app1.example.com",
      "src_port": 80,
      "dest_ip": "10.0.0.1",
      "dest_port": 80
    },
    {
      "protocol": "HTTPS",
      "src_hostname": "app2.example.com",
      "src_port": 443,
      "dest_ip": "10.0.0.1",
      "dest_port": 443
    },
    {
      "protocol": "TCP",
      "src_hostname": "45.158.126.xxx",
      "src_port": 2222,
      "dest_ip": "10.0.0.1",
      "dest_port": 22
    }
  ]
}
```

## Commands Reference

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version and exit |
| `--host NAME` | `-H` | Use specific host profile |
| `--no-color` | | Disable colored output |
| `--verbose` | `-v` | Verbose output |
| `--debug` | | Debug mode (show stack traces) |
| `--help` | `-h` | Show help |

### General Commands

| Command | Description |
|---------|-------------|
| `vf about` | Show version, author, and contact info |
| `vf update` | Check for new version from PyPI |

### Config Commands

| Command | Description |
|---------|-------------|
| `vf config add NAME` | Add new host profile |
| `vf config remove NAME` | Remove host profile |
| `vf config list` | List all host profiles |
| `vf config set-default NAME` | Set default host |
| `vf config test [NAME]` | Test connection (all hosts if NAME omitted) |

### VM Commands

| Command | Description |
|---------|-------------|
| `vf vm list` | List VMs |
| `vf vm list --status up/down` | Filter VMs by status |
| `vf vm list --all-hosts` | List VMs from all hosts with details |
| `vf vm list --all-hosts --status up` | List running VMs from all hosts |
| `vf vm list --json` | Output in JSON format |

### Forward Commands

| Command | Description |
|---------|-------------|
| `vf forward list` | List forwarding rules |
| `vf forward add` | Add forwarding rule |
| `vf forward edit` | Edit forwarding rule |
| `vf forward delete` | Delete forwarding rule(s) |

### Batch Commands

| Command | Description |
|---------|-------------|
| `vf batch import` | Import rules from JSON file |
| `vf batch export` | Export rules to JSON file |

## Examples

### Workflow: Setup Web Server Forwarding

```bash
# 1. Setup host
vf config add myserver \
  --url "https://virt.myserver.com:4083/index.php" \
  --key "abc123" \
  --pass "secret" \
  --default

# 2. Check available VMs
vf vm list --status up

# 3. Add HTTP forwarding for website
vf forward add -v 103 -p HTTP -d mysite.com

# 4. Add HTTPS forwarding
vf forward add -v 103 -p HTTPS -d mysite.com

# 5. Add SSH access via custom port
vf forward add -v 103 -p TCP -d 45.158.126.xxx -s 2222 -t 22

# 6. Verify
vf forward list -v 103
```

### Workflow: Backup and Restore Rules

```bash
# Backup rules from VM
vf batch export -v 103 -o vm103_backup.json

# Restore to another VM
vf batch import -v 104 -f vm103_backup.json --dry-run  # Test first
vf batch import -v 104 -f vm103_backup.json            # Execute
```

### Workflow: Multi-Host Management

```bash
# Setup multiple hosts
vf config add production --url "https://prod.com:4083/index.php" --key "key1" --pass "pass1" --default
vf config add staging --url "https://staging.com:4083/index.php" --key "key2" --pass "pass2"

# Test all hosts at once
vf config test

# List VMs from all hosts
vf vm list --all-hosts

# Operations on specific host
vf -H staging vm list
vf -H production forward list -v 103
```

## Troubleshooting

### Connection Error

```
✗ Failed to connect to API
```

**Solution:**
1. Ensure API URL is correct (including port 4083)
2. Check network connection to server
3. Make sure firewall is not blocking

### Authentication Error

```
✗ Authentication failed
```

**Solution:**
1. Verify API Key in Virtualizor Panel
2. Ensure API Password is correct
3. Check if API access is enabled in panel

### Port Already Reserved

```
✗ Port 8080 is already reserved/in use
```

**Solution:**
1. Use another available port
2. Check allowed ports in HAProxy config
3. See suggestions displayed

### No VMs Found

```
! No VMs found
```

**Solution:**
1. Ensure host profile is correct
2. Check if there are VMs in Virtualizor panel
3. Verify API credentials have access to VMs

### Debug Mode

To see error details:

```bash
vf --debug vm list
vf --debug forward add -i
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/iam-rizz/python-domain-forwarding-virtualizor.git
cd python-domain-forwarding-virtualizor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=virtualizor_forwarding

# Run specific test
pytest tests/test_models.py -v
```

### Project Structure

```
python-domain-forwarding-virtualizor/
├── virtualizor_forwarding/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI entry point
│   ├── api.py              # Virtualizor API client
│   ├── config.py           # Configuration manager
│   ├── models.py           # Data models
│   ├── tui.py              # Rich TUI components
│   ├── utils.py            # Utility functions
│   └── services/
│       ├── __init__.py
│       ├── vm_manager.py
│       ├── forwarding_manager.py
│       └── batch_processor.py
├── tests/
│   └── __init__.py
├── pyproject.toml
├── README.md
├── README_ID.md
├── LICENSE
└── .gitignore
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Rizz**

- Email: rizkyadhypratama@gmail.com
- GitHub: [@iam-rizz](https://github.com/iam-rizz)

---

<p align="center">
  Made with ❤️ for Virtualizor users
</p>
