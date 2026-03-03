/* 
Multichannel Arduino DAQ firmware
  Stream-based, PyDAQ compatible

Code that should be loaded in arduino in order to acquire data from a specific port (analogInputPort) and
 send data from another one (digitalOutputPort)
 Author:    Samir Angelo Milani Martins
             - https://www.samirmartins.com.br
             - https://www.github.com/samirmartins/

 */
 
/* 
Multichannel Arduino DAQ firmware
Stream-based, PyDAQ compatible (bidirectional)

Compatible with:
- Multichannel get_data (CSV streaming)
- Multichannel send_data (CSV digital frame)

*/

const int digitalOutputPorts[] = {8, 9, 10};   // Digital outputs (must match Python channels)
const int analogInputPorts[]   = {A0, A1, A2}; // Analog inputs

const int nOutputs  = sizeof(digitalOutputPorts) / sizeof(digitalOutputPorts[0]);
const int nChannels = sizeof(analogInputPorts)  / sizeof(analogInputPorts[0]);

int analogValues[nChannels];

String incomingFrame = "";

void setup()
{
  Serial.begin(115200);

  for (int i = 0; i < nOutputs; i++)
  {
    pinMode(digitalOutputPorts[i], OUTPUT);
    digitalWrite(digitalOutputPorts[i], LOW);
  }
}

void loop()
{
  /* ----------------------------------------
     1) Read digital multichannel frame
     ---------------------------------------- */
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    if (c == '\n')
    {
      processFrame(incomingFrame);
      incomingFrame = "";
    }
    else
    {
      incomingFrame += c;
    }
  }

  /* ----------------------------------------
     2) Read all analog channels
     ---------------------------------------- */
  for (int i = 0; i < nChannels; i++)
  {
    analogValues[i] = analogRead(analogInputPorts[i]);
  }

  /* ----------------------------------------
     3) Send multichannel analog frame
     ---------------------------------------- */
  Serial.print(analogValues[0]);

  for (int i = 1; i < nChannels; i++)
  {
    Serial.print(",");
    Serial.print(analogValues[i]);
  }

  Serial.println();
}


/* ----------------------------------------
   Frame parser
   Expected format: 1,0,1\n
---------------------------------------- */
void processFrame(String frame)
{
  int index = 0;
  int lastPos = 0;

  for (int i = 0; i < frame.length(); i++)
  {
    if (frame[i] == ',' || i == frame.length() - 1)
    {
      int value;

      if (i == frame.length() - 1)
        value = frame.substring(lastPos).toInt();
      else
        value = frame.substring(lastPos, i).toInt();

      if (index < nOutputs)
      {
        digitalWrite(digitalOutputPorts[index], value == 1 ? HIGH : LOW);
      }

      index++;
      lastPos = i + 1;
    }
  }
}