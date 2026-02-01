import serial
import struct
from typing import Tuple
from enum import Enum
from time import sleep

# Serial Protocol Command IDs
START_BYTE = 0xAA
WRITE_VEL = 0x01
WRITE_PWM = 0x02
READ_POS = 0x03
READ_VEL = 0x04
READ_UVEL = 0x05
READ_TVEL = 0x06
SET_PPR = 0x07
GET_PPR = 0x08
SET_KP = 0x09
GET_KP = 0x0A
SET_KI = 0x0B
GET_KI = 0x0C
SET_KD = 0x0D
GET_KD = 0x0E
SET_RDIR = 0x0F
GET_RDIR = 0x10
SET_CUT_FREQ = 0x11
GET_CUT_FREQ = 0x12
SET_MAX_VEL = 0x13
GET_MAX_VEL = 0x14
SET_PID_MODE = 0x15
GET_PID_MODE = 0x16
SET_CMD_TIMEOUT = 0x17
GET_CMD_TIMEOUT = 0x18
SET_I2C_ADDR = 0x19
GET_I2C_ADDR = 0x1A
RESET_PARAMS = 0x1B
READ_MOTOR_DATA = 0x2A
CLEAR_DATA_BUFFER = 0x2C
GET_NUM_OF_MOTORS = 0x2D

class SupportedNumOfMotors(Enum):
    TWO = 2
    FOUR = 4


class EPMCSerialClient:
    """Python client for EPMC serial communication."""

    def __init__(self, supported_num_of_motors: SupportedNumOfMotors):
        self.ser: serial.Serial | None = None
        self.num_of_motors: int = supported_num_of_motors.value

    def connect(self, port: str, baud: int = 115200, timeout: float = 0.1):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        sleep(3.0)

        for _ in range(10):
            if self.confirmNumOfMotors():
                return
            sleep(0.1)

        self.disconnect()
        raise RuntimeError("EPMC motor count mismatch")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    # ------------------ Packet Helpers ------------------

    def _flush_rx(self):
        """Flush any unread bytes in RX buffer"""
        if self.ser is None:
            return
        try:
            self.ser.reset_input_buffer()
        except serial.SerialException:
            pass


    def _flush_tx(self):
        """Flush TX buffer"""
        if self.ser is None:
            return
        try:
            self.ser.reset_output_buffer()
        except serial.SerialException:
            pass


    def _send_packet(self, cmd: int, payload: bytes = b""):
        if self.ser is None:
            raise RuntimeError("Serial port is not connected")
        self._flush_rx()
        length = len(payload)
        packet = bytearray([START_BYTE, cmd, length]) + payload
        checksum = sum(packet) & 0xFF
        packet.append(checksum)
        self.ser.write(packet)
        self.ser.flush()

    
    def _read_floats(self, count: int) -> Tuple[bool, tuple]:
        if self.ser is None:
            raise RuntimeError("Serial port is not connected")

        try:
            payload = self.ser.read(4 * count)

            if len(payload) != 4 * count:
                # partial frame → stream is now misaligned
                self._flush_rx()
                return False, tuple([0.0] * count)

        except (serial.SerialTimeoutException,
                serial.SerialException,
                Exception):
            # Any read-related failure → resync stream
            self._flush_rx()
            return False, tuple([0.0] * count)
        
        return True, struct.unpack("<" + "f" * count, payload)

    # ------------------ Generic Data ------------------
    
    def write_data1(self, cmd: int, val: float, pos: int = 0):
        payload = struct.pack("<Bf", pos, val)
        self._send_packet(cmd, payload)

    def read_data1(self, cmd: int, pos: int = 0) -> Tuple[bool, float]:
        payload = struct.pack("<Bf", pos, 0.0)
        self._send_packet(cmd, payload)
        success, (val,) = self._read_floats(1)
        return success, val

    def write_data2(self, cmd: int, a: float, b: float):
        payload = struct.pack("<ff", a, b)
        self._send_packet(cmd, payload)

    def read_data2(self, cmd: int) -> Tuple[bool, float, float]:
        self._send_packet(cmd)
        success, vals = self._read_floats(2)
        return success, vals
        # return success, *vals

    def read_data4(self, cmd: int) -> Tuple[bool, float, float, float, float]:
        self._send_packet(cmd)
        success, vals = self._read_floats(4)
        return success, vals
        # return success, *vals
    
    def write_data4(self, cmd: int, a: float, b: float, c: float, d: float):
        payload = struct.pack("<ffff", a, b, c, d)
        self._send_packet(cmd, payload)

    def read_data8(self, cmd: int) -> Tuple[bool, float, float, float, float, float, float, float, float]:
        self._send_packet(cmd)
        success, vals = self._read_floats(8)
        return success, vals
        # return success, *vals

    # ----------------------------------------------------

    def confirmNumOfMotors(self):
        success, num_of_motors = self.read_data1(GET_NUM_OF_MOTORS)
        return (success and int(num_of_motors) == self.num_of_motors)
        
    # ------------------ Motor Commands ------------------

    def writeSpeed(self, v0: float, v1: float, v2: float = 0.0, v3: float = 0.0):
        if self.num_of_motors == SupportedNumOfMotors.TWO.value:
            self.write_data2(WRITE_VEL, v0, v1)
        elif self.num_of_motors == SupportedNumOfMotors.FOUR.value:
            self.write_data4(WRITE_VEL, v0, v1, v2, v3)

    def writePWM(self, pwm0: float, pwm1: float, pwm2: float = 0.0, pwm3: float = 0.0):
        if self.num_of_motors == SupportedNumOfMotors.TWO.value:
            self.write_data2(WRITE_PWM, pwm0, pwm1)
        elif self.num_of_motors == SupportedNumOfMotors.FOUR.value:
            self.write_data4(WRITE_PWM, pwm0, pwm1, pwm2, pwm3)
    
    # ----- MOTOR READ HELPERS ----------

    def _read_motor_array(self, cmd: int):
        if self.num_of_motors == SupportedNumOfMotors.TWO.value:
            success, vals = self.read_data2(cmd)
        elif self.num_of_motors == SupportedNumOfMotors.FOUR.value:
            success, vals = self.read_data4(cmd)
        else:
            return False, tuple()

        return success, tuple(round(v, 4) for v in vals)

    # ---------- READ COMMANDS ----------

    def readPos(self):
        return self._read_motor_array(READ_POS)

    def readVel(self):
        return self._read_motor_array(READ_VEL)

    def readUVel(self):
        return self._read_motor_array(READ_UVEL)

    def readTVel(self):
        return self._read_motor_array(READ_TVEL)

    def readMotorData(self):
        if self.num_of_motors == SupportedNumOfMotors.TWO.value:
            success, vals = self.read_data4(READ_MOTOR_DATA)
        elif self.num_of_motors == SupportedNumOfMotors.FOUR.value:
            success, vals = self.read_data8(READ_MOTOR_DATA)
        else:
            return False, tuple()

        return success, tuple(round(v, 4) for v in vals)

    # ------------------ PID / Timeout ------------------
    def setCmdTimeout(self, timeout: float):
        self.write_data1(SET_CMD_TIMEOUT, timeout)

    def getCmdTimeout(self):
        success, timeout = self.read_data1(GET_CMD_TIMEOUT)
        return success, int(timeout)

    def setPidMode(self, mode: int):
        self.write_data1(SET_PID_MODE, mode)

    def getPidMode(self):
        success, mode = self.read_data1(GET_PID_MODE)  # FIXED
        return success, int(mode)

    def clearDataBuffer(self):
        success, _ = self.read_data1(CLEAR_DATA_BUFFER)
        return success

    # ------------------ Motor Parameters ------------------
    def getMaxVel(self, motor_no: int):
        success, maxVel = self.read_data1(GET_MAX_VEL, motor_no)
        return success, round(maxVel, 3)

    def setMaxVel(self, motor_no: int, maxVel: float):
        self.write_data1(SET_MAX_VEL, maxVel, motor_no)

    def setPPR(self, motor_no: int, ppr: float):
        self.write_data1(SET_PPR, ppr, motor_no)

    def getPPR(self, motor_no: int):
        success, ppr = self.read_data1(GET_PPR, motor_no)
        return success, round(ppr, 3)

    def setKp(self, motor_no: int, kp: float):
        self.write_data1(SET_KP, kp, motor_no)

    def getKp(self, motor_no: int):
        success, kp = self.read_data1(GET_KP, motor_no)
        return success, round(kp, 3)

    def setKi(self, motor_no: int, ki: float):
        self.write_data1(SET_KI, ki, motor_no)

    def getKi(self, motor_no: int):
        success, ki = self.read_data1(GET_KI, motor_no)
        return success, round(ki, 3)

    def setKd(self, motor_no: int, kd: float):
        self.write_data1(SET_KD, kd, motor_no)

    def getKd(self, motor_no: int):
        success, kd = self.read_data1(GET_KD, motor_no)
        return success, round(kd, 3)

    def setRdir(self, motor_no: int, rdir: int):
        self.write_data1(SET_RDIR, rdir, motor_no)

    def getRdir(self, motor_no: int):
        success, rdir = self.read_data1(GET_RDIR, motor_no)
        return success, int(rdir)

    def setCutOffFreq(self, motor_no: int, freq: float):
        self.write_data1(SET_CUT_FREQ, freq, motor_no)

    def getCutOffFreq(self, motor_no: int):
        success, freq = self.read_data1(GET_CUT_FREQ, motor_no)
        return success, round(freq, 3)

    def setI2cAddress(self, i2cAddr: int):
        self.write_data1(SET_I2C_ADDR, i2cAddr)

    def getI2cAddress(self):
        success, addr = self.read_data1(GET_I2C_ADDR)
        return success, int(addr)

    def resetAllParams(self):
        success, _ = self.read_data1(RESET_PARAMS)
        return success