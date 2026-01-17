# Quick Start Guide

This guide will help you get started with the Open Source HLR/HSS system quickly.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Kaimeliax/Open-Source-HLR-HSS.git
cd Open-Source-HLR-HSS
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

## Quick Start

### 1. Start the HLR/HSS server

```bash
# Start with sample data
python -m hlr_hss.main --init-db
```

The server will start with:
- REST API on http://localhost:8080
- In-memory database (no external database required)
- Sample subscriber already configured

### 2. Test the API

**Health check:**
```bash
curl http://localhost:8080/health
```

**Get subscriber information:**
```bash
curl http://localhost:8080/api/v1/subscribers/001010000000001
```

**Generate authentication vector:**
```bash
curl -X POST http://localhost:8080/api/v1/subscribers/001010000000001/auth
```

**Create a new subscriber:**
```bash
curl -X POST http://localhost:8080/api/v1/subscribers/001010000000002 \
  -H "Content-Type: application/json" \
  -d '{
    "msisdn": "1234567891",
    "ki": "465B5CE8B199B49FAA5F0A2EE238A6BC",
    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
    "roaming_allowed": true
  }'
```

### 3. Run Examples

**Subscriber management:**
```bash
python examples/subscriber_management.py
```

**Authentication:**
```bash
python examples/authentication_example.py
```

**Roaming configuration:**
```bash
python examples/roaming_example.py
```

### 4. Run Tests

```bash
pytest hlr_hss/tests/ -v
```

## Configuration

### Using a Different Database

Edit `config/config.yaml` and change the database type:

**For PostgreSQL:**
```yaml
database:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "hlr_hss"
    username: "hlr_user"
    password: "your_password"
```

**For MySQL:**
```yaml
database:
  type: "mysql"
  mysql:
    host: "localhost"
    port: 3306
    database: "hlr_hss"
    username: "hlr_user"
    password: "your_password"
```

**For MongoDB:**
```yaml
database:
  type: "mongodb"
  mongodb:
    host: "localhost"
    port: 27017
    database: "hlr_hss"
    username: "hlr_user"
    password: "your_password"
```

### Configure eNB Profiles

```yaml
ran:
  enb_profiles:
    - enb_id: "srsenb-b210mini"
      model: "LibreSDR B210mini"
      downlink_modulation: "1024QAM"
      uplink_modulation: "256QAM"
      mimo: "2x2"
      max_transmission_mode: "TM9"
      contiguous_bandwidth_mhz: 30
      carrier_bandwidth_options: ["15+15", "20+10"]
      sample_rate_msps: 61.44
      duplex_modes: ["TDD", "FDD"]
      qos_enforcement: true
      cell_broadcast_supported: false
```

Use `/api/v1/enb` and `/api/v1/enb/{enb_id}` to manage profiles, and include `qos_profile` plus `ambr_uplink`/`ambr_downlink` when creating subscribers.

### Custom Configuration

1. Copy the default configuration:
```bash
cp config/config.yaml config/config.local.yaml
```

2. Edit `config/config.local.yaml` with your settings

3. Start with custom config:
```bash
python -m hlr_hss.main -c config/config.local.yaml
```

## Features Overview

### Core HLR/HSS
- Subscriber management (CRUD operations)
- Authentication (Milenage, XOR, TUAK)
- Location management
- Multi-generation support (2G-5G)

### Network Interfaces
- **S6a**: LTE MME to HSS
- **S6d**: 3G SGSN to HSS
- **Cx/Dx**: IMS CSCF to HSS
- **5G interfaces**: Framework ready

### Online Charging System (OCS)
- Real-time credit control
- Prepaid and postpaid charging
- Service-specific rating (data, voice, SMS)
- Quota management

### Diameter Routing Agent (DRA)
- Message routing
- Load balancing
- Peer management
- Failover support

### Roaming
- Partner configuration
- Roaming agreements and rates
- National and international roaming
- Per-subscriber policies

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review the [API Reference](README.md#api-reference) section
- Explore examples in the `examples/` directory
- Check the configuration options in `config/config.yaml`

## Support

- GitHub Issues: https://github.com/Kaimeliax/Open-Source-HLR-HSS/issues
- Documentation: See `docs/` directory

## License

MIT License - See [LICENSE](LICENSE) file for details
