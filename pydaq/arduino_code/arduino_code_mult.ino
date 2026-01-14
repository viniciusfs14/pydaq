/* 
Multichannel Arduino DAQ firmware
  Stream-based, PyDAQ compatible

Code that should be loaded in arduino in order to acquire data from a specific port (analogInputPort) and
 send data from another one (digitalOutputPort)
 Author:    Samir Angelo Milani Martins
             - https://www.samirmartins.com.br
             - https://www.github.com/samirmartins/

 */
const int digitalOutputPort = 13;
const int analogInputPorts[] = {A0, A1, A2};

const int nChannels = sizeof(analogInputPorts) / sizeof(analogInputPorts[0]);

int inputValue;
int analogValues[nChannels];

void setup()
{
  Serial.begin(115200);
  pinMode(digitalOutputPort, OUTPUT);
}

void loop()
{
  /* ----------------------------------------
     1) Read digital command (non-blocking)
     ---------------------------------------- */
  if (Serial.available() > 0)
  {
    inputValue = Serial.read();

    if (inputValue == '1')
      digitalWrite(digitalOutputPort, HIGH);
    else if (inputValue == '0')
      digitalWrite(digitalOutputPort, LOW);
  }

  /* ----------------------------------------
     2) Read all analog channels
     ---------------------------------------- */
  for (int i = 0; i < nChannels; i++)
  {
    analogValues[i] = analogRead(analogInputPorts[i]);
  }

  /* ----------------------------------------
     3) Send multichannel frame
     ---------------------------------------- */
  Serial.print(analogValues[0]);

  for (int i = 1; i < nChannels; i++)
  {
    Serial.print(",");
    Serial.print(analogValues[i]);
  }

  Serial.println();