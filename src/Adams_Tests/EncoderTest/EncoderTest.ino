/*
This script made by Adam is for checking if the motor encoder is working.
Connect the wires as described below, open the serial monitor, and twist the encoder by hand.
The first two numbers show the two hall effect states (0 or 1)
The third number shows the count
The count should go up and down as you twist the enocder.
*/

const int encoderPinB = 2; //purple wire connect to DIGITAL 2
const int encoderPinA = 3; //blue wire connect to DIGITAL 3
const int encoderGND = -1; //green wire connect to GND
const int encoderVCC = -1; //brown wire connect to 5V
//red wire, do not connect
//black wire, do not connect

volatile long counter = 0;
int aLastState;


void setup() {
  // put your setup code here, to run once:
  pinMode(MotorPWR, OUTPUT);
  pinMode(encoderPinA, INPUT_PULLUP);
  pinMode(encoderPinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoderPinA), updateEncoder, CHANGE);
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(MotorPWR, LOW);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}

void updateEncoder() {
  // Code to update counter_m1 based on the state of the encoder pins
  // Read current states of channels A and B
  int aState = digitalRead(encoderPinA);
  int bState = digitalRead(encoderPinB);


  // Check if the state of channel A has changed
  if (aState != aLastState) {
    // Determine the direction of rotation by comparing A and B states
    if (aState != bState) {
      counter++;  // Clockwise rotation
    } else {
      counter--;  // Counterclockwise rotation
    }
  }

  // Update the last known state of channel A
  aLastState = aState;
  Serial.print(aState);
  Serial.print(" ");
  Serial.print(bState);
  Serial.print("  ");
  Serial.print(counter);
  Serial.print("\n");
}
