
## Easy PID Motor Controller (EPMC) Python Library
Python serial interface for the Easy PID Motor Controller (EPMC). The Library Supports two and four motor EPMC controllers

> you can use it in your microcomputer robotics project (e.g Raspberry Pi, PC, etc.)

#

## Install
- you'll need to pip install the pyserial library
  ```shell
    pip3 install epmc-serial   //linux or mac
    pip install epmc-serial  //windows
  ```

#

## Uninstall
- you'll need to pip install the pyserial library
  ```shell
    pip3 uninstall epmc-serial   //linux or mac
    pip uninstall epmc-serial  //windows
  ```

#

## How to Use the Library
- Ensure you have the **`EPMC MODULE`** interfaced with your preferred motors

- Ensure you've already setup the encoder and PID parameters with the [epmc_setup_application](https://github.com/robocre8/epmc_setup_application).

- check the serial port the driver is connected to:
  ```shell
  ls /dev/ttyA*
  ```
  > you should see /dev/ttyACM0 or /dev/ttyACM1 and so on

- use the serial port in your code

- A simple way to get started is simply to try out the example code below


## Basic Library functions and usage (Two Motor Support Control)

- connect to EPMC module
  > controller = EPMCSerialClient(SupportedNumOfMotors.TWO)
  >
  > controller.connect("port_name or port_path")

- clear speed, position, e.t.c data buffer on the EPMC module
  > controller.clearDataBuffer() # returns bool -> success

- send target angular velocity command
  > controller.writeSpeed(motor0_TargetVel, motor1_TargetVel)

- send PWM command
  > controller.writePWM(motor0_PWM, motor1_PWM)

- set motor command timeout
  > controller.setCmdTimeout(timeout_ms)

- get motor command timeout
  > controller.getCmdTimeout() # returns tuple -> (success, motor_command_timeout_ms): bool, float

- read motors angular position and angular velocity
  > controller.readMotorData() # returns bool, tuple(size=4foats) -> success, (pos0, pos1, vel0, vel1)

- read motors angular position
  > controller.readPos() # returns bool, tuple(size=2floats) -> success, (pos0, pos1)

- read motors angular velocity
  > controller.readVel() # returns bool, tuple(size=2floats) -> success, (vel0, vel1)

- read motor maximum commandable angular velocity
  > controller.getMaxVel(motor_no) # returns tuple -> (success, max_vel): bool, float
  > maxVel0 or maxVel1 based on the specified motor number

- while these function above help communicate with the already configure EPMC module, more examples of advanced funtions usage for parameter tuning can be found in the [epmc_setup_application](https://github.com/robocre8/epmc_setup_application) source code

#

## example code (Two Motor Support Control)
```python
from epmc_serial import EPMCSerialClient, SupportedNumOfMotors
import time

controller = EPMCSerialClient(SupportedNumOfMotors.TWO)

# variable for communication
pos0=0.0; pos1=0.0
vel0=0.0; vel1=0.0

# [4 rev/sec, 2 rev/sec, 1 rev/sec, 0.5 rev/sec]
targetVel = [1.571, 3.142, 6.284, 12.568] 
vel = targetVel[1]
v = 0.0

readTime = None
readTimeInterval = 0.02 # 50Hz

cmdTime = None
cmdTimeInterval = 5.0

# 50Hz comm setup
serial_port = '/dev/ttyACM0'
serial_baudrate = 115200
serial_timeout = 0.018 #value < 0.02 (for 50Hz comm)

controller.connect(serial_port, serial_baudrate, serial_timeout)

success = controller.clearDataBuffer()
controller.writeSpeed(0.0, 0.0)
print('configuration complete')

timeout_ms = 10000
controller.setCmdTimeout(timeout_ms)
success, val0 = controller.getCmdTimeout()
if success: # only update if read was successfull
  timeout_ms = val0
  print("command timeout in ms: ", timeout_ms)
else:
  print("ERROR: could not read motor command timeout")

sendHigh = True

readTime = time.time()
cmdTime = time.time()

while True:
  if time.time() - cmdTime > cmdTimeInterval:
    if sendHigh:
      # print("command high")
      v = vel
      controller.writeSpeed(v, v)
      vel = vel*-1
      sendHigh = False
    else:
      # print("command low")
      v = 0.0
      controller.writeSpeed(v, v)
      sendHigh = True
    
    
    cmdTime = time.time()



  if time.time() - readTime > readTimeInterval:
    try:
      # controller.writeSpeed(v, v)
      success, val = controller.readMotorData()
      if success: # only update if read was successfull
        pos0 = val[0]; pos1 = val[1]
        vel0 = val[2]; vel1 = val[3]

      print(f"motor0_readings: [{pos0}, {vel0}]")
      print(f"motor1_readings: [{pos1}, {vel1}]")
      print("")
    except:
      pass
    
    readTime = time.time()

```

#

## Basic Library functions and usage (Four Motor Support Control)

- connect to EPMC module
  > controller = EPMCSerialClient(SupportedNumOfMotors.FOUR)
  >
  > controller.connect("port_name or port_path")

- clear speed, position, e.t.c data buffer on the EPMC module
  > controller.clearDataBuffer() # returns bool -> success

- send target angular velocity command
  > controller.writeSpeed(motor0_TargetVel, motor1_TargetVel)

- send PWM command
  > controller.writePWM(motor0_PWM, motor1_PWM)

- set motor command timeout
  > controller.setCmdTimeout(timeout_ms)

- get motor command timeout
  > controller.getCmdTimeout() # returns tuple -> (success, motor_command_timeout_ms): bool, float

- read motors angular position and angular velocity
  > controller.readMotorData() # returns bool, tuple(size=8floats) -> success, (pos0, pos1, pos2, pos3, vel0, vel1, vel2, vel3)

- read motors angular position
  > controller.readPos() # returns bool, tuple(size=4floats) -> success, (pos0, pos1, pos2, pos3)

- read motors angular velocity
  > controller.readVel() # returns bool, tuple(size=4floats) -> success, (vel0, vel1, vel2, vel3)

- read motor maximum commandable angular velocity
  > controller.getMaxVel(motor_no) # returns tuple -> (success, max_vel): bool, float
  > maxVel0 or maxVel1 based on the specified motor number

- while these function above help communicate with the already configure EPMC module, more examples of advanced funtions usage for parameter tuning can be found in the [epmc_setup_application](https://github.com/robocre8/epmc_setup_application) source code

#

## example code (Four Motor Support Control)
```python
from epmc_serial import EPMCSerialClient, SupportedNumOfMotors
import time

controller = EPMCSerialClient(SupportedNumOfMotors.FOUR)

# variable for communication
pos0=0.0; pos1=0.0; pos2=0.0; pos3=0.0
vel0=0.0; vel1=0.0; vel2=0.0; vel3=0.0

# [4 rev/sec, 2 rev/sec, 1 rev/sec, 0.5 rev/sec]
targetVel = [1.571, 3.142, 6.284, 12.568] 
vel = targetVel[1]
v = 0.0

readTime = None
readTimeInterval = 0.02 # 50Hz

cmdTime = None
cmdTimeInterval = 5.0

# 50Hz comm setup
serial_port = '/dev/ttyUSB0'
serial_baudrate = 115200
serial_timeout = 0.018 #value < 0.02 (for 50Hz comm)

controller.connect(serial_port, serial_baudrate, serial_timeout)

success = controller.clearDataBuffer()
controller.writeSpeed(0.0, 0.0, 0.0, 0.0)
print('configuration complete')

timeout_ms = 10000
controller.setCmdTimeout(timeout_ms)
success, val0 = controller.getCmdTimeout()
if success: # only update if read was successfull
  timeout_ms = val0
  print("command timeout in ms: ", timeout_ms)
else:
  print("ERROR: could not read motor command timeout")

sendHigh = True

readTime = time.time()
cmdTime = time.time()

while True:
  if time.time() - cmdTime > cmdTimeInterval:
    if sendHigh:
      # print("command high")
      v = vel
      controller.writeSpeed(v, v, v, v)
      vel = vel*-1
      sendHigh = False
    else:
      # print("command low")
      v = 0.0
      controller.writeSpeed(v, v, v, v)
      sendHigh = True
    
    
    cmdTime = time.time()



  if time.time() - readTime > readTimeInterval:
    try:
      # controller.writeSpeed(v, v, v, v)
      success, val = controller.readMotorData()
      if success: # only update if read was successfull
        pos0 = val[0]; pos1 = val[1]; pos2 = val[2]; pos3 = val[3]
        vel0 = val[4]; vel1 = val[5]; vel2 = val[6]; vel3 = val[7]

      print(f"motor0_readings: [{pos0}, {vel0}]")
      print(f"motor1_readings: [{pos1}, {vel1}]")
      print(f"motor2_readings: [{pos2}, {vel2}]")
      print(f"motor3_readings: [{pos3}, {vel3}]")
      print("")
    except:
      pass
    
    readTime = time.time()

```