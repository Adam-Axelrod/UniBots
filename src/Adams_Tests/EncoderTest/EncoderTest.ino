const float GR = 297.924;

const int MotorPin = 11;
const int encoderPinA = 2;
const int encoderPinB = 3;

volatile long counter = 0;
int aLastState;

float currentPositionInDegrees;
float demandPositionInDegrees = -90.0;

float errorPositionInDegrees_prev = 0, errorPositionInDegrees_sum = 0;

float Kp = 50, Kd = 35, Ki = 0;

unsigned long currentTime;
unsigned long previousTime = 0;
unsigned long deltaT;

void setup() {
  // put your setup code here, to run once:
  pinMode(MotorPin, OUTPUT);
  pinMode(encoderPinA, INPUT_PULLUP);
  pinMode(encoderPinB, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoderPinA), updateEncoder, CHANGE);
  Serial.begin(9600);

  delay(3000);

  previousTime = micros();
  
}

void loop() {

  // put your main code here, to run repeatedly:

  currentPositionInDegrees = ((counter * 360) / (GR * 6));

  if (currentPositionInDegrees >= 360 || currentPositionInDegrees <= -360){
    counter -= ((GR * 6) * ((int)(currentPositionInDegrees / 360)));
  }

  currentTime = micros();
  deltaT = currentTime - previousTime;


  if (deltaT > 20) {
    // Task 4: Compute error (P,I,D), and ensure that the previous error is updated
    float errorPositionInDegrees = currentPositionInDegrees - demandPositionInDegrees; 
    float errorPositionInDegrees_diff = (errorPositionInDegrees - errorPositionInDegrees_prev) / deltaT;
    errorPositionInDegrees_sum += errorPositionInDegrees;
    errorPositionInDegrees_prev = errorPositionInDegrees;

    // Task 5: Compute the PID output
    float controllerOutput = errorPositionInDegrees * Kp + errorPositionInDegrees_diff * Kd + errorPositionInDegrees_sum * Ki * deltaT;
    controllerOutput = constrain(controllerOutput, -255, 255);

    if ((0 < controllerOutput) && (controllerOutput < 130)) {
      controllerOutput = 130;
    }
    if ((0 > controllerOutput) && (controllerOutput > -130)) {
      controllerOutput = -130;
    }



    // Task 6: Send voltage to 
    if (controllerOutput > 0) {
      analogWrite(MotorPin, controllerOutput);
    } else {
      analogWrite(MotorPin, 0);
    }

    // Task 7: Print the current position and demand for plotting
    Serial.print("CurrentPosition:");
    Serial.print(currentPositionInDegrees);
    Serial.print("  ");
    Serial.print("DemandPosition:");
    Serial.print(demandPositionInDegrees);
    Serial.print(" ");
    Serial.print("ControllerOutput:");
    Serial.print(controllerOutput);
    Serial.print(" ");
    Serial.print("Error:");
    Serial.print(errorPositionInDegrees);
    Serial.print('\n');

    previousTime = currentTime;
    
  }

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
}