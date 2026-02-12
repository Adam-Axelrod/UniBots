# UniBots Design

## Process loop

The main loop in [brain/main.py](brain/main.py) runs at full rate:

```
1. Create sensors and actuators; init executor, frame_sink
2. Loop:
   - Read all inputs (front_frame, rear_frame, distance, encoders, heading)
   - ball_centers, annotated_base = vision.get_detections(front_frame)
   - Update WorldModel from inputs + ball_centers
   - _, cmd = fsm.update(world_model)
   - executor.execute(cmd)
   - annotated = annotator(annotated_base, ball_centers)
   - frame_sink.send(annotated)
3. finally: stop/close all
```

Inputs feed WorldModel; FSM produces Command; Executor drives motor/speaker.

---

## Codebase structure

```
src/
  brain/           # Control logic
    main.py        # Entry point: inputs → world_model → fsm → executor
    config.py      # Load config.yaml
    world_model.py # WorldModel dataclass
    command.py     # Command dataclass
    process.py     # VisionModule (YOLO, PyTorch or NCNN) + Annotator (path drawings)
    fsm.py         # FSM: WorldModel in, (State, Command) out

  input/           # Sensors (sim/real per folder)
    base.py        # Sensor ABC: init(), get_data(), stop()
    camera/        # create_front_camera, create_rear_camera
    ultrasonic/    # create_ultrasonic
    encoders/      # create_encoders
    imu/           # create_imu

  output/          # Actuators (sim/real per folder)
    base.py        # Actuator ABC: init(), stop()
    executor.py    # Executor: execute(Command) → motor, speaker
    motor_controller/  # create_motor_controller, drive()
    speaker/       # create_speaker, beep()

  debugger/        # Debug frame viewing
    base.py        # FrameSink ABC
    tcp.py         # TCP stream (headless)
    local.py       # OpenCV window
    viewer.py      # Client to connect to TCP stream

  config.yaml      # input_mode, actuator_mode, etc.
```

Sensors and actuators use creators that branch on `INPUT_MODE` / `ACTUATOR_MODE` internally; main never branches on config.

### Data flow

1. All inputs (including camera) feed into the brain.
2. Brain updates world model, FSM state, and produces a decision (command).
3. Output executes the command on hardware.

```mermaid
flowchart TB
  subgraph input [Input]
    Cam[Camera]
    US[Ultrasonic]
    Enc[Encoders]
    IMU[IMU]
  end

  subgraph brain [Brain]
    WM[WorldModel]
    Proc[Process]
    FSM[FSM]
  end

  subgraph output [Output]
    Exec[Execute]
    Motor[Motor]
    Speaker[Speaker]
  end

  subgraph debugger [Debugger]
    Sink[FrameSink]
  end

  Cam --> Proc
  Proc --> WM
  US --> WM
  Enc --> WM
  IMU --> WM
  WM --> FSM
  FSM --> Exec
  Exec --> Motor
  Exec --> Speaker
  Proc --> Sink
```

---

## Core behavior (locked-in assumptions)

* Intake always ON
* Ball collection is **drive-through**
* Robot collects continuously
* **Exactly one** drop-off
* After drop → park → stop forever

---

## FSM States

```
INIT
SEARCH_BALL
DRIVE_TO_BALL
GO_TO_WALL
ALIGN_AND_DROP
PARK
AVOID_OBSTACLE
```

---

## State Responsibilities (high level)

### INIT

* Wait for physical start
* Reset ball counter and timers
* Enable intake

---

### SEARCH_BALL

* Wander / sweep arena
* Look for balls using front camera

**Transitions**

* Ball detected → `DRIVE_TO_BALL`
* Balls full OR time low → `GO_TO_WALL`

---

### DRIVE_TO_BALL

* Face detected ball
* Drive forward so ball rolls into intake
* Maintain heading with IMU
* Intake always ON

**Transitions**

* Ball collected (counter increments) → `SEARCH_BALL`
* Ball lost → `SEARCH_BALL`
* Balls full → `GO_TO_WALL`

---

### GO_TO_WALL

* Rotate toward own wall using IMU heading
* Drive forward continuously
* Avoid obstacles reactively
* Use AprilTag opportunistically for orientation correction

**Transition**

* Wall / net visible → `ALIGN_AND_DROP`

---

### ALIGN_AND_DROP

* Switch to rear camera
* Align parallel to wall
* Stop
* Drop all balls

**Transition**

* Drop complete → `PARK`

---

### PARK

* Drive slowly until touching wall
* Stop permanently

Terminal state.

---

### AVOID_OBSTACLE (interrupt-style)

* Triggered from any motion state
* Local turn + short move
* Resume previous state

---

## Main Control Loop (Skeleton)

```
loop @ fixed rate:

  read sensors
  update IMU heading
  update encoder-based motion
  update ball counter
  update time remaining

  if ultrasonic detects obstacle:
    run AVOID_OBSTACLE
    continue

  switch FSM state:

    SEARCH_BALL:
      if ball_detected:
        state = DRIVE_TO_BALL
      else:
        wander()

      if balls_full or time_low:
        state = GO_TO_WALL

    DRIVE_TO_BALL:
      drive_toward_ball()

      if ball_collected or ball_lost:
        state = SEARCH_BALL

      if balls_full:
        state = GO_TO_WALL

    GO_TO_WALL:
      orient_toward_wall()
      drive_forward()

      if wall_visible:
        state = ALIGN_AND_DROP

    ALIGN_AND_DROP:
      align_with_wall()
      drop_balls()
      state = PARK

    PARK:
      drive_forward_slow()
      stop_forever()
```

---

## Final FSM Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> SEARCH_BALL : start

    SEARCH_BALL --> DRIVE_TO_BALL : ball_detected
    DRIVE_TO_BALL --> SEARCH_BALL : ball_collected
    DRIVE_TO_BALL --> SEARCH_BALL : ball_lost

    SEARCH_BALL --> GO_TO_WALL : balls_full OR time_low
    DRIVE_TO_BALL --> GO_TO_WALL : balls_full

    GO_TO_WALL --> ALIGN_AND_DROP : wall_visible
    ALIGN_AND_DROP --> PARK : drop_complete

    PARK --> [*]

    SEARCH_BALL --> AVOID_OBSTACLE : obstacle
    DRIVE_TO_BALL --> AVOID_OBSTACLE : obstacle
    GO_TO_WALL --> AVOID_OBSTACLE : obstacle
    AVOID_OBSTACLE --> SEARCH_BALL : cleared
```
