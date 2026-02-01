# 🌟 Shine2MQTT

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/bremme/shine2mqtt/actions/workflows/main.yaml/badge.svg)](https://github.com/bremme/shine2mqtt/actions/workflows/main.yaml)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=bugs)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=coverage)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=bremme_shine2mqtt&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=bremme_shine2mqtt)

[![Docker Pulls](https://img.shields.io/docker/pulls/bremme/shine2mqtt)](https://hub.docker.com/r/bremme/shine2mqtt)
[![PyPI version](https://img.shields.io/pypi/v/shine2mqtt)](https://pypi.org/project/shine2mqtt/)
[![License](https://img.shields.io/badge/license-GNU_v3-green.svg)](LICENSE)

> **A local Growatt server which listens to your Shine Wifi-X datalogger and publishes to MQTT**

Shine2MQTT acts as a local server for your Growatt Shine Wifi-X datalogger, capturing data that would normally be sent to Growatt's cloud servers. It publishes this data via MQTT in a Home Assistant-friendly format, giving you complete local control of your solar inverter data.

## ✨ Features

- 🏠 **Home Assistant Integration** - Native MQTT discovery support
- 🔒 **Local Control** - Keep your data private, no cloud dependency
- 🐳 **Docker Support** - Easy deployment with Docker/Docker Compose
- ⚡ **Real-time Data** - Instant solar production metrics
- 🛠️ **RESTful API** - Built-in API for monitoring and control (Alpha)
- 📊 **Comprehensive Metrics** - Power, voltage, current, energy totals, and more

## 🔌 Compatibility

| Component      | Tested Models |
| -------------- | ------------- |
| **Datalogger** | Shine WiFi-X  |
| **Inverter**   | MIC 3000TL-X  |

> 💡 Other Growatt models using the Shine protocol may work but haven't been tested.
> There is some functionality to capture raw data frames for integrating other models. Please open an issue so I can check if its easy to integrate, most likely it is.

## 📦 Installation

### Option 1: Docker (Recommended)

**Using Docker CLI:**

Use plain Docker to run the `shine2mqtt` container:

```bash
docker run -d \
  --name shine2mqtt \
  -p 5279:5279 \
  -p 8000:8000 \
  bremme/shine2mqtt:latest \
    --mqtt-server-host your-mqtt-broker \
    --mqtt-server-port 1883 \
    --mqtt-server-username username \
    --mqtt-server-password password \
    --mqtt-discovery-inverter-model "MIC 3000TL-X" \
    --mqtt-discovery-datalogger-model "Shine WiFi-X"
```

**Using Docker Compose:**

Create a `docker-compose.yaml` file, a basic example would look like this:

```yaml
services:
  shine2mqtt:
    image: bremme/shine2mqtt:latest
    container_name: shine2mqtt
    ports:
      - "5279:5279"
      - "8000:8000"
    environment:
      SHINE2MQTT_MQTT__CLIENT__HOST: "your-mqtt-broker"
      SHINE2MQTT_MQTT__CLIENT__PORT: "1883"
      SHINE2MQTT_MQTT__CLIENT__USERNAME: "username"
      SHINE2MQTT_MQTT__CLIENT__PASSWORD: "password"
      SHINE2MQTT_MQTT__DISCOVERY__INVERTER__MODEL: "MIC 3000TL-X"
      SHINE2MQTT_MQTT__DISCOVERY__DATALOGGER__MODEL: "Shine WiFi-X"
    restart: unless-stopped
```

Run the container:

```shell
docker compose up
```

> 💡 See [docker-compose.example.yaml](docker-compose.example.yaml) for all available options.

### Option 2: UV (Python Package Manager)

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly with UV
uv run shine2mqtt

# Or install globally
uv tool install shine2mqtt
# And run
shine2mqtt
```

### Option 3: Python Module from src

```bash
# Clone the repository
git clone https://github.com/bremme/shine2mqtt.git
cd shine2mqtt

# Install dependencies
uv sync --no-dev

# Run the application
uv run shine2mqtt
```

## ⚙️ Configuration

Shine2MQTT can be configured through **CLI arguments**, **environment variables**, or a **YAML configuration file**. Options are applied in this priority order (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

### Configuration options

| Option                            | Default         | Description                                        |
| --------------------------------- | --------------- | -------------------------------------------------- |
| `log_level`                       | `INFO`          | Logging level (DEBUG, INFO, WARNING, ERROR)        |
| `log_color`                       | `false`         | Force colored logging output                       |
| `capture_data`                    | `false`         | Capture raw frames and store in `captured_frames/` |
| `mqtt.base_topic`                 | `solar`         | Base MQTT topic for publishing data                |
| `mqtt.availability_topic`         | `solar/state`   | MQTT topic for availability status                 |
| `mqtt.server.host`                | `localhost`     | MQTT broker host                                   |
| `mqtt.server.port`                | `1883`          | MQTT broker port                                   |
| `mqtt.server.username`            |                 | MQTT broker username                               |
| `mqtt.server.password`            |                 | MQTT broker password                               |
| `mqtt.server.client_id`           | `shine2mqtt`    | MQTT client identifier                             |
| `mqtt.discovery.enabled`          | `false`         | Enable Home Assistant MQTT discovery               |
| `mqtt.discovery.prefix_topic`     | `homeassistant` | MQTT discovery topic prefix                        |
| `mqtt.discovery.inverter.model`   |                 | Inverter model for Home Assistant                  |
| `mqtt.discovery.datalogger.model` |                 | Datalogger model for Home Assistant                |
| `server.host`                     | `0.0.0.0`       | TCP server host                                    |
| `server.port`                     | `5279`          | TCP server port                                    |
| `api.enabled`                     | `false`         | Enable RESTful API                                 |
| `api.host`                        | `0.0.0.0`       | RESTful API host                                   |
| `api.port`                        | `8000`          | RESTful API port                                   |
| `simulated_client`                | `false`         | Enable simulated client for testing                |
| `simulated_client.server_host`    | `localhost`     | Simulated client server host                       |
| `simulated_client.server_port`    | `5279`          | Simulated client server port                       |

All options can be set via any of the configuration methods.

### CLI Arguments

For cli arguments `_`, or `.` need to be converted to `-`. For example:

- `log_level` becomes `--log-level`
- `mqtt.base_topic` becomes `--mqtt-base-topic`

For all available options run:

```shell
uv run shine2mqtt --help
```

### Environment Variables

For environmental variables prefix with `SHINE2MQTT_`, use uppercase, convert `-` to `_` and `.` to `__`. For example:

- `log_level` becomes `SHINE2MQTT_LOG_LEVEL`
- `mqtt.base_topic` becomes `SHINE2MQTT_MQTT__BASE_TOPIC`

### YAML Configuration File

To use a configuration file, have a look at the [config.example.yaml](config.example.yaml) file and create your own `config.yaml`. The file will be automatically picked up in the default location (`./config.yaml`), but you can also specify a custom path with the `--config-file` CLI argument or `SHINE2MQTT_CONFIG_FILE` environment variable.

## 🚀 Usage

### 1. Configure Your Shine Datalogger

Point your Shine datalogger to the IP address where Shine2MQTT is running:

1. Connect to your datalogger's WiFi network
   1. Press the button on the bottom, and wait for the blue LED.
2. Access your datalogger's web interface (usually at `http://192.168.10.100`)
3. Login using default credentials (typically admin and 12345678)
4. Navigate to **Advanced Settings** > **Server IP**
5. Change the server IP to your Shine2MQTT host address
6. Set the port to `5279` (default)
7. Save and reboot the datalogger

### 2. Verify Connection

Check the logs to confirm the datalogger is connecting:

```bash
# Docker
docker logs -f shine2mqtt

# Docker compose  (if running detached)
docker compose logs -f shine2mqtt

# UV/Python
# Logs will appear in stdout
```

You should see a message like:

```shell
11:48:15 | INFO     | server - Accepted new TCP connection from ('<ip-address>', <random-port>)
```

### 3. Home Assistant Integration

If MQTT discovery is enabled, your inverter will automatically appear in Home Assistant under:

- **Settings** → **Device & Services** → **MQTT** -> **Devices**
- You should see a new entry for both the inverter as well as the datalogger:
  - **Inverter Name**: `Growatt MIC 3000TL-X` (or your specified model)
  - **Datalogger Name**: `Shine WiFi-X` (or your specified model)  

All sensors will be automatically created with appropriate device classes and units.

## 📊 Published Data

Shine2MQTT publishes the following metrics via MQTT:

### Inverter Sensors

| Metric                        | Topic                                     | Unit |
| ----------------------------- | ----------------------------------------- | ---- |
| **DC Metrics**                |                                           |      |
| Total DC Power Input          | `solar/inverter/sensor/power_dc`          | W    |
| DC Voltage String 1           | `solar/inverter/sensor/voltage_dc_1`      | V    |
| DC Current String 1           | `solar/inverter/sensor/current_dc_1`      | A    |
| DC Power String 1             | `solar/inverter/sensor/power_dc_1`        | W    |
| DC Voltage String 2           | `solar/inverter/sensor/voltage_dc_2`      | V    |
| DC Current String 2           | `solar/inverter/sensor/current_dc_2`      | A    |
| DC Power String 2             | `solar/inverter/sensor/power_dc_2`        | W    |
| **AC Metrics**                |                                           |      |
| AC Power Output               | `solar/inverter/sensor/power_ac`          | W    |
| Grid Frequency                | `solar/inverter/sensor/frequency_ac`      | Hz   |
| AC Voltage Phase 1            | `solar/inverter/sensor/voltage_ac_1`      | V    |
| AC Current Phase 1            | `solar/inverter/sensor/current_ac_1`      | A    |
| AC Apparent Power Phase 1     | `solar/inverter/sensor/power_ac_1`        | VA   |
| **AC Line Voltages**          |                                           |      |
| AC Line Voltage L1-L2         | `solar/inverter/sensor/voltage_ac_l1_l2`  | V    |
| AC Line Voltage L2-L3         | `solar/inverter/sensor/voltage_ac_l2_l3`  | V    |
| AC Line Voltage L3-L1         | `solar/inverter/sensor/voltage_ac_l3_l1`  | V    |
| **Energy Production**         |                                           |      |
| Today's AC Energy Production  | `solar/inverter/sensor/energy_ac_today`   | kWh  |
| Lifetime AC Energy Production | `solar/inverter/sensor/energy_ac_total`   | kWh  |
| Lifetime DC Energy Production | `solar/inverter/sensor/energy_dc_total`   | kWh  |
| Today's DC Energy String 1    | `solar/inverter/sensor/energy_dc_1_today` | kWh  |
| Lifetime DC Energy String 1   | `solar/inverter/sensor/energy_dc_1_total` | kWh  |
| Today's DC Energy String 2    | `solar/inverter/sensor/energy_dc_2_today` | kWh  |
| Lifetime DC Energy String 2   | `solar/inverter/sensor/energy_dc_2_total` | kWh  |

### Inverter Diagnostic Sensors

| Metric                            | Topic                                               | Unit |
| --------------------------------- | --------------------------------------------------- | ---- |
| Inverter Serial Number            | `solar/inverter/sensor/inverter_serial`             | -    |
| Inverter Firmware Version         | `solar/inverter/sensor/inverter_fw_version`         | -    |
| Inverter Control Firmware Version | `solar/inverter/sensor/inverter_control_fw_version` | -    |
| Maximum Active AC Power           | `solar/inverter/sensor/active_power_ac_max`         | %    |
| Maximum Reactive AC Power         | `solar/inverter/sensor/reactive_power_ac_max`       | %    |
| Power Factor                      | `solar/inverter/sensor/power_factor`                | -    |
| Power Factor Control Mode         | `solar/inverter/sensor/power_factor_control_mode`   | -    |
| Rated AC Power                    | `solar/inverter/sensor/rated_power_ac`              | VA   |
| Rated DC Voltage                  | `solar/inverter/sensor/rated_voltage_dc`            | V    |
| AC Voltage Low Limit              | `solar/inverter/sensor/voltage_ac_low_limit`        | V    |
| AC Voltage High Limit             | `solar/inverter/sensor/voltage_ac_high_limit`       | V    |
| AC Frequency Low Limit            | `solar/inverter/sensor/frequency_ac_low_limit`      | Hz   |
| AC Frequency High Limit           | `solar/inverter/sensor/frequency_ac_high_limit`     | Hz   |

### Datalogger Diagnostic Sensors

| Metric                      | Topic                                           | Unit |
| --------------------------- | ----------------------------------------------- | ---- |
| Datalogger Serial Number    | `solar/datalogger/sensor/datalogger_serial`     | -    |
| Datalogger Software Version | `solar/datalogger/sensor/datalogger_sw_version` | -    |
| Datalogger Hardware Version | `solar/datalogger/sensor/datalogger_hw_version` | -    |
| Data Update Interval        | `solar/datalogger/sensor/update_interval`       | min  |
| Datalogger IP Address       | `solar/datalogger/sensor/ip_address`            | -    |
| Datalogger MAC Address      | `solar/datalogger/sensor/mac_address`           | -    |
| Network Netmask             | `solar/datalogger/sensor/netmask`               | -    |
| Gateway IP Address          | `solar/datalogger/sensor/gateway_ip_address`    | -    |
| Server IP Address           | `solar/datalogger/sensor/server_ip_address`     | -    |
| Server Port                 | `solar/datalogger/sensor/server_port`           | -    |
| WiFi Network Name (SSID)    | `solar/datalogger/sensor/wifi_ssid`             | -    |

## 🛠️ Development

### Prerequisites

- Python 3.14+
- [UV](https://docs.astral.sh/uv/) - Fast Python package manager
- [Pre-commit](https://pre-commit.com/) - Git hooks

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/bremme/shine2mqtt.git
cd shine2mqtt

# Install dependencies (including dev dependencies)
uv sync

# Install pre-commit hooks
pre-commit install
```

### Project Structure

```shell
shine2mqtt/
├── src/shine2mqtt/          # Main application code
│   ├── growatt/             # Growatt protocol implementation
│   │   ├── protocol/        # Protocol decoders/encoders
│   │   ├── server/          # TCP server
│   │   └── client/          # Simulated client (testing)
│   ├── mqtt/                # MQTT bridge
│   ├── hass/                # Home Assistant discovery
│   └── api/                 # REST API
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
└── docs/                    # Documentation
```

### Development Tools

The project uses modern Python development tools:

- **UV** - Fast dependency management and task running
- **Ruff** - Lightning-fast linting and formatting
- **Pytest** - Testing framework
- **Ty** - Type checking
- **Pre-commit** - Automated code quality checks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/growatt/protocol/decoders/test_data_request_decoder.py
```

### Code Quality

```bash
# Run linter (auto-fix)
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests

# Type checking
uv run ty check src

# Run all pre-commit hooks
pre-commit run --all-files
```

### Building

```bash
# Build wheel and sdist
uv build

# Build Docker image
docker build -t bremme/shine2mqtt:latest .
```

### Running Locally

```bash
# Run application
uv run shine2mqtt

# Run  with simulated client

# run shine2mqtt on different port (to prevent datalogger conflicts)
uv run shine2mqtt --server-port 4000
# run simulated client
uv run shine2mqtt --simulate-client --simulated-client-server-port 4000
```

## 📚 Resources

### Related Projects

This project took inspiration from various other open-source Growatt projects:

- [sciurius/Growatt-WiFi-Tools](https://github.com/sciurius/Growatt-WiFi-Tools)
  - [Growatt WiFi Module Protocol by Johan Vromans](https://www.vromans.org/johan/software/sw_growatt_wifi_protocol.html)
- [johanmeijer/grott](https://github.com/johanmeijer/grott)
- [jaakkom/ha-growatt-local-server](https://github.com/jaakkom/ha-growatt-local-server)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and code quality checks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the GNU General Public License V3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Johan Vromans for the excellent protocol documentation
- The Home Assistant community
- All contributors to related Growatt projects

---

**⚠️ Disclaimer**: This project is not affiliated with or endorsed by Growatt. Use at your own risk.
