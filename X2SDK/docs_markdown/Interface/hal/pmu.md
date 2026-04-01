# 5.4.2 Power Management Unit (PMU)

**The Power Management Unit interface provides monitoring and management of the robot’s power system, including battery status, voltage and current monitoring, and more.**

## Core Features

### Battery Monitoring

- **Battery Voltage**: Real-time monitoring of battery voltage
- **Battery Current**: Monitors battery charging/discharging current
- **Battery Health**: Tracks overall battery health status

### Power Management

- **Multi-channel Power Rails**: Monitors 48V, 12V, 5V and other power rails
- **Current Monitoring**: Tracks current consumption of each module
- **Voltage Monitoring**: Tracks voltage status of each module

### System Monitoring

- **Module Power Status**: Power status of RK3588, ORIN, etc.
- **Over-current Protection**: Detects and protects against over-current conditions

## Power Management Topic

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/pmu/state` | `PmuState` | Power management data | - | 0.2Hz |

- `PmuState` ros2-msg @ hal/msg/PmuState.msg

  ```
  # PMU State
  string pmu_software_version     # PMU software version
  string pmu_hardware_version     # PMU hardware version
  string pmu_protocol_version     # PMU protocol version
  uint32 pmu_bool_status          # Boolean status bits

  # Current info (A)
  float64 head_power_current      # Head module current
  float64 output_48v_current      # 48V output current
  float64 rk3588_current          # RK3588 current
  float64 output_12v_current      # 12V output current
  float64 bus_48v_current         # 48V bus current
  float64 orin_current            # ORIN current

  # Voltage info (V)
  float64 bus_48v_pmos_voltage    # 48V PMOS voltage
  float64 battery_voltage         # Battery voltage
  float64 fan_voltage             # Fan voltage
  float64 output_12v_voltage      # 12V output voltage
  float64 output_48v_voltage      # 48V output voltage
  float64 bus_48v_voltage         # 48V bus voltage
  float64 head_power_voltage      # Head module voltage
  float64 orin_voltage            # ORIN voltage
  float64 rk3588_voltage          # RK3588 voltage

  # BMS info
  string bms_manufacturer         # BMS manufacturer
  string bms_serial_number        # BMS serial number
  string bms_hardware_version     # Hardware version
  string bms_software_version     # Software version

  uint32 bms_status_bits                      # Status bits

  uint16 battery_balance_line_resistance      # Cell balancing line resistance (mΩ)
  float64 battery_pack_voltage                # Pack voltage (V)
  float64 battery_current                     # Pack current (A, +charge / –discharge)
  float64 battery_output_power                # Pack output power (W)
  float64 battery_temperature                 # Pack temperature (°C)
  uint32 battery_remaining_capacity           # Remaining capacity (mAh)
  uint8 battery_remaining_capacity_percentage # Remaining capacity (%)
  uint16 battery_cycle_count                  # Cycle count
  uint32 battery_cycle_total_capacity         # Accumulated capacity (Ah)
  ```

  `pmu_bool_status` Boolean Bit Definitions:

  | Bit | Name | Description |
  | --- | --- | --- |
  | 0 | rk3588PowerGood | RK3588 power good |
  | 1 | rk3588Monitor1 | RK3588 monitor status 1 |
  | 2 | rk3588Monitor2 | RK3588 monitor status 2 |
  | 3 | orinPowerGood | ORIN power good |
  | 4 | orinMonitor1 | ORIN monitor status 1 |
  | 5 | orinMonitor2 | ORIN monitor status 2 |
  | 6 | bus48vOverCurrent | 48V bus over-current |
  | 7 | bus48vOverTemperature | 48V bus over-temperature |
  | 8 | rk3588PlugDetect | RK3588 plug detect |
  | 9 | orinNXPlugDetect | ORIN NX plug detect |
  | 10–31 | reserved | reserved bits |

  `bms_status_bits` Bit Definitions:

  | Bit | Name | Description |
  | --- | --- | --- |
  | 0 | chargeFlag | Charging flag |
  | 1 | chargeOverCurrentFlag | Charge over-current flag |
  | 2 | dischargeFlag | Discharging flag |
  | 3 | dischargeOverCurrentFlag | Discharge over-current flag |
  | 4 | shortCircuitFlag | Battery short-circuit flag |
  | 5 | cellOverVoltageFlag | Cell over-voltage flag |
  | 6 | cellUnderVoltageFlag | Cell under-voltage flag |
  | 7 | batteryOverVoltageFlag | Pack over-voltage flag |
  | 8 | batteryUnderVoltageFlag | Pack under-voltage flag |
  | 9 | cellOpenCircuitFlag | Cell open-circuit detected |
  | 10 | ntcOpenCircuitFlag | Temperature sensor open-circuit detected |
  | 11 | cellDischargeOverTemperatureFlag | Cell temperature above discharge upper limit |
  | 12 | cellChargeOverTemperatureFlag | Cell temperature above charge upper limit |
  | 13 | cellDischargeUnderTemperatureFlag | Cell temperature below discharge lower limit |
  | 14 | cellChargeUnderTemperatureFlag | Cell temperature below charge lower limit |
  | 15 | reserved\_1 | reserved bits |
  | 16 | cellMaxVoltageDiffOverHighFlag | Max cell voltage difference above limit |
  | 17 | mosfetChargeDisableFlag | MOSFET charge disabled |
  | 18 | mosfetDischargeDisableFlag | MOSFET discharge disabled |
  | 19 | mosfetOverTemperatureFlag | MOSFET over-temperature flag |
  | 20 | balanceLineResistanceOverHighFlag | Balancing line resistance over limit |
  | 21–31 | reserved\_11 | reserved bits |

## Safety Notes

Warning

**Power Management Limitations**

- Power management affects system safety; operate with caution
- Do not modify power parameters arbitrarily — may cause system damage
- Power-related operations should be performed under expert guidance

Note

**Best Practices**

- Monitor power status regularly to detect abnormalities early
- Implement monitoring and alert mechanisms for power status
- Implement power protection strategies
- Pay attention to temperature and current limits of power modules
