# ERROR DICTIONARY

Quick reference for common PYDAQ errors and how to fix them.

---

## General Configuration Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Empty Save Path | Missing configuration: Please ensure device, channels, and save path are properly defined. | [PYDAQ] Missing configuration: Empty save path. | All (except Send Data) | Define a valid save path before running. |
| Empty Data Path | Missing configuration: Please ensure device, channels, and save path are properly defined. | [PYDAQ] Missing configuration: Empty data path. | Send Data | Provide a valid data file path. |
| Invalid COM Port | Missing configuration: Please ensure device, channels, and save path are properly defined. | [PYDAQ] Missing configuration: No valid COM port selected. | ALL Arduino | Select the correct COM port and ensure the device is connected. |

---

## Dimension Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Channel Not Defined | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: Please ensure device and channel are properly defined. | Get Model | Select at least one input and output channel. |
| Invalid Channel Format | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: Invalid channel format selected. | PID Control | Ensure the channel format follows the device standard. |
| Channel Dimension Mismatch | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: The number of selected channels does not match the data structure. | Send Data | Ensure selected AI and AO channels match data dimensions. |
| PID Tuning Mismatch | Dimension mismatch: Number of selected channels incorrect. | [PYDAQ] Dimension mismatch: PID tuning requires exactly 1 AI channel and 1 AO channel (SISO). | Step Response | Select exactly one AI and one AO channel when "Calculate PID" is enabled. |
| LQR Matrix Dimension Mismatch | Dimension mismatch: Number of selected channels or matrix dimensions are incorrect. | [PYDAQ] Dimension mismatch: Matrix A must be {n_states}x{n_states} / Matrix B must be {n_states}x{n_inputs}. | LQR Control | Verify A and B matrices dimensions follow state-space rules for the selected AI/AO channels. |
| LQR Reference Dimension Mismatch | Dimension mismatch: Number of selected channels or matrix dimensions are incorrect. | [PYDAQ] Dimension mismatch: Reference X_ref must have {n_states} columns / U_eq must have {n_inputs} columns. | LQR Control | Ensure reference state and input vectors match the dimensions of matrices A and B. |

---

## LQR Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Matrices Not Defined | Missing configuration: LQR Matrices (A, B, Q, R) must be defined before running. | [PYDAQ] Missing configuration: Matrices are not defined. Cannot simulate or run control. | LQR Control | Define A, B, Q, R matrices before running. |
| Reference Error | Missing configuration: Please ensure device, channels, and save path are properly defined. | [PYDAQ] Missing configuration: Reference Tracking is enabled but X_ref or U_eq are empty. | LQR Control | Provide valid reference vectors or disable tracking. |

---

## Hardware Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Firmware Not Detected | Firmware not detected on this board. Please go to the top menu and click on 'Arduino - Firmware' to upload the correct code. | [PYDAQ] PyDAQ Firmware not detected on this board! Please go to the top menu... | ALL Arduino | Upload the correct firmware via the Arduino menu. |
| NI-DAQmx Driver Missing | NI-DAQmx drivers not found. | [PYDAQ] NI-DAQmx drivers not found. Cannot start hardware acquisition. | ALL NI-DAQ | Install NI-DAQmx drivers (NI-MAX). |

---

## File Errors

| Error Reference | GUI Message | Terminal Message | Module | How to Fix |
|----------------|------------|-----------------|--------|------------|
| Trajectory File Mismatch | Trajectory File Mismatch: Session duration must match the uploaded trajectory file. | [PYDAQ] Trajectory File Mismatch: Session duration must be exactly {expected}s to match the uploaded trajectory file. | LQR Control | Ensure the GUI session duration matches the (number of rows * sample period) of the uploaded file. |
| Invalid File Format | Missing configuration: Unsupported file format. | [PYDAQ] Missing configuration: Unsupported file format. | Send Data | Use a supported format (e.g., CSV). |

---

## Code-Level Errors and Support

If you are using PYDAQ via the Command Line Interface (CLI) or as an API in your own Python scripts, you bypass the Graphical User Interface (GUI) safety locks. In these cases, invalid parameters will not trigger a friendly GUI pop-up. Instead, you will encounter standard Python tracebacks (e.g., `ValueError`, `TypeError`, or `IndexError`) directly in your terminal.

If an error occurs without a clear `[PYDAQ]` warning tag, or if you encounter unexpected behavior during pure code execution, it is highly likely a code-level implementation issue or an edge case not covered by our current checks.

Do not hesitate to reach out! We encourage users and developers to report these issues, open pull requests, or contact the core development team through our GitHub repository. Your feedback is essential to making PYDAQ more robust.
