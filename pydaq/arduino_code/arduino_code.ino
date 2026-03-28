/* * Code that should be loaded in arduino in order to acquire and send data
 * Author:    Samir Angelo Milani Martins
 * - https://www.samirmartins.com.br
 * - https://www.github.com/samirmartins/
 */

/* * Multichannel Arduino DAQ firmware
 * Stream-based, PyDAQ compatible (bidirectional)
 *
 * Compatible with:
 * - Multichannel get_data (CSV streaming)
 * - Multichannel send_data (CSV digital frame)
 * - Multichannel step_response
 * - PID and LQR control (PWM support)
 */

void setup() {
  // Baud rate must match the one configured in Python (e.g., 115200 or 9600)
  Serial.begin(115200); 
}

void loop() {
  
  // 1. Continuous Analog Reading (A0 to A5) - Maximum speed streaming
  String out = "";
  out += String(analogRead(A0)) + ",";
  out += String(analogRead(A1)) + ",";
  out += String(analogRead(A2)) + ",";
  out += String(analogRead(A3)) + ",";
  out += String(analogRead(A4)) + ",";
  out += String(analogRead(A5));
  
  Serial.println(out);
  
  // 2. Parse Incoming Control Commands
  // Expected format: "8:255,9:128\n" (Pin:Value) OR "0\n" (Stop/Warmup)
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "0") {
       // Stop command: Turn off all commonly used actuator pins (D2 to D13)
       for(int i = 2; i <= 13; i++) {
          pinMode(i, OUTPUT);
          digitalWrite(i, LOW);
       }
    } else {
       int startIndex = 0;
       while (startIndex < command.length()) {
          int commaIndex = command.indexOf(',', startIndex);
          if (commaIndex == -1) {
             commaIndex = command.length();
          }
          
          String pair = command.substring(startIndex, commaIndex);
          int colonIndex = pair.indexOf(':');
          
          if (colonIndex != -1) {
             int pin = pair.substring(0, colonIndex).toInt();
             int val = pair.substring(colonIndex + 1).toInt();
             
             // Dynamically configure the pin and actuate (PWM or Digital)
             pinMode(pin, OUTPUT);
             analogWrite(pin, val);
          }
          startIndex = commaIndex + 1;
       }
    }
  }
}
