# ERROR DICTIONARY

Quick reference for common PYDAQ errors and how to fix them.

---

## General Configuration Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Empty Save Path | Missing configuration: Please ensure device, channel, and path are properly defined. | [PYDAQ] Missing configuration: Empty save path. | All (except Send Data) | Define a valid save path before running. |
| Empty Data Path | Missing configuration: Please ensure device, channel, and path are properly defined. | [PYDAQ] Missing configuration: Empty data path. | Send Data | Provide a valid data file path. |
| No Channel Selected | Missing configuration: Please ensure device, channel, and path are properly defined. | [PYDAQ] Missing configuration: Please ensure device and channel are properly defined. | ALL NIDAQ | Select at least one input channel. |
| Invalid COM Port | Missing configuration: Please ensure device, channel, and path are properly defined. | [PYDAQ] Missing configuration: No valid COM port selected. | ALL Arduino | Select the correct COM port and ensure the device is connected. |

---

## Dimension Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Dimension Mismatch | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: The number of selected channels does not match the data structure. | Multiple | Ensure selected channels match data dimensions. |
| LQR Matrix Dimension Mismatch | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: Matrix A must be (n_states x n_states). | LQR Control | Verify A, B matrices dimensions follow state-space rules. |

---

## LQR Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Matrices Not Defined | Missing configuration: Matrices are not defined. | [PYDAQ] Missing configuration: Matrices are not defined. Cannot simulate or run control. | LQR Control | Define A, B, Q, R matrices before running. |
| Reference Error | Missing configuration: Reference Tracking enabled but X_ref or U_ref are empty. | [PYDAQ] Missing configuration: Reference Tracking is enabled but X_ref or U_ref are empty. | LQR Control | Provide valid reference vectors or disable tracking. |

---

## Hardware Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Firmware Not Detected | Firmware not detected on this board. | [PYDAQ] PyDAQ Firmware not detected on this board. | ALL Arduino | Upload the correct firmware via the Arduino menu. |
| NI-DAQmx Driver Missing | NI-DAQmx drivers not found. | [PYDAQ] NI-DAQmx drivers not found. Cannot start hardware acquisition. | ALL NIDAQ | Install NI-DAQmx drivers (NI-MAX). |

---

## File Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| File Mismatch | Trajectory File Mismatch | [PYDAQ] Trajectory File Mismatch: Session duration must match trajectory file. | LQR Control | Ensure trajectory length matches experiment duration. |
| Invalid File Format | Missing configuration: Unsupported file format. | [PYDAQ] Missing configuration: Unsupported file format. | Send Data | Use a supported format (e.g., CSV). |