#include <Servo.h>

Servo servo1;  // create servo object to control a servo
Servo servo2;

const int motorPin1 = 5;
const int motorPin2 = 10;
const int val1 = 90;
const int val2 = 90;

void setup() {
  // put your setup code here, to run once:
  servo1.attach(motorPin1);
  servo2.attach(motorPin2);
  servo1.writeMicroseconds(1500);
  servo2.writeMicroseconds(1500);
  delay(2000);
  Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:
  //servo1.writeMicroseconds(2000);
  //servo2.writeMicroseconds(2000);
}
