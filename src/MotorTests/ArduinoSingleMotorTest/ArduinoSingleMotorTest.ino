/*
This script made by Adam is for checking differnt motor speeds
Connect the wires as described below, upload the script and open the serial monitor
The motor should start spinning at full speed (255)
The motor should decrease in speed in a stewise fashion
At a certain signal the motor should stop spinning (usually around 130)
*/

//purple wire, do not connect
//blue wire, do not connect
//green wire, do not connect
//brown wire , do not connect
const int motorPWR = 11; //red wire connect to pin 11 (can modify to any pin with ~ ie. 3,5,6,9,10,11)
const int motorGND = -1; //black wire connect to GND

float pwmSignal; //PWM signal sent to the motor (0-255)

void setup() {
  // put your setup code here, to run once:
  pinMode(motorPWR, OUTPUT);
  Serial.begin(9600);
  Serial.print("Starting in 3");
  Serial.print('\n');
  delay(1000);
  Serial.print("2");
  Serial.print('\n');
  delay(1000);
  Serial.print("1");
  Serial.print('\n');
  delay(1000);
}

void loop() {
  // put your main code here, to run repeatedly:
  for (int i = 255; i > 0; i=i-32) {
    pwmSignal = i;
    Serial.print("PWM Signal:");
    Serial.print(pwmSignal);
    Serial.print('\n');
    analogWrite(motorPWR, pwmSignal);
    delay(3000);
  }


}
