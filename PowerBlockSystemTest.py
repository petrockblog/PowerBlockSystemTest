# Initialization
import time
import RPi.GPIO as GPIO
from subprocess import call, check_output, CalledProcessError


class Button:

    """Represents a virtual toggle button for a given pin."""

    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        self.level = GPIO.HIGH
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, self.level)

    def setPressed(self):
        self.level = GPIO.LOW
        GPIO.output(self.pin, self.level)
        time.sleep(0.1)

    def setReleased(self):
        self.level = GPIO.HIGH
        GPIO.output(self.pin, self.level)
        time.sleep(0.1)

    def setLOW(self):
        self.level = GPIO.LOW
        GPIO.output(self.pin, self.level)
        time.sleep(0.1)

    def setHIGH(self):
        self.level = GPIO.HIGH
        GPIO.output(self.pin, self.level)
        time.sleep(0.1)

    def __str__(self):
        return "Button '%s' on pin %d, current level: %d" % (self.name, self.pin, self.level)


class Mysignal:

    """Represents a signal that is observed on a given pin."""

    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def getSignal(self):
        return GPIO.input(self.pin)

    def __str__(self):
        return "Signal '%s' on pin %d, current level: %d" % (self.name, self.pin, GPIO.input(self.pin))


class Programmer:

    def __init__(self, firmwarename):
        self.firmwarename = firmwarename

    def flashFirmware(self):
        returncode = call(["avrdude", "-pt85", "-cstk500v2", "-P/dev/ttyUSB0", "-u", "-Uflash:w:%s:a" %
                           (self.firmwarename), "-Ulfuse:w:0xe2:m", "-Uhfuse:w:0xdf:m", "-Uefuse:w:0xff:m"])

        if returncode != 0:
            print "Error while flashing firmware!"
        else:
            print "Successfully downloaded firmware to uC!"

        return returncode


class LED(object):

    """docstring for LED"""

    def __init__(self, name, pin):
        super(LED, self).__init__()
        self.name = name
        self.pin = pin
        self.dc = 1  # 0 .. 100
        self.freq = 1

        GPIO.setup(pin, GPIO.OUT)
        self.pwmpin = GPIO.PWM(pin, self.freq)
        self.pwmpin.start(self.dc)

    def setDutyCycle(self, dc):
        self.pwmpin.ChangeDutyCycle(dc)

    def setFrequency(self, freq):
        self.pwmpin.stop()
        self.pwmpin = GPIO.PWM(self.pin, freq)
        self.pwmpin.start(self.dc)


class Systemtest:

    def __init__(self):
        self.testPassed = True
        self.verbose = False

    def setVerbose(self, mode):
        self.verbose = mode

    def testEquals(self, observed, expected):
        if observed != expected:
            self.testPassed = False
            if self.verbose is True:
                print "Expected: %s, Observed: %s. Test FAILED" % (expected, observed)
            return False
        else:
            if self.verbose is True:
                print "Expected: %s, Observed: %s. Test PASSED" % (expected, observed)
            return True

    def hasPassed(self):
        return self.testPassed


def main():
    # RPi.GPIO Layout verwenden (wie Pin-Nummern)
    GPIO.setmode(GPIO.BOARD)

    # Initialize programmer
    # programmer = Programmer("/home/pi/attiny.hex")

    # Initialize GPIOs
    rpishutdown = Mysignal("RPi_Shutdown", 7)
    rpistatus = Button("RPi_Status", 11)
    rpistatus.setLOW()
    btn = Button("Btn", 12)
    rpi5v = Mysignal("RPi_5V", 13)

    boardAttachedBtn = Mysignal("BoardAttached", 18)
    statusled = LED("Status-LED", 22)
    statusled.setDutyCycle(0)

    while True:
        # isBoardAttached = False
        # while isBoardAttached is False:
        #     attached = boardAttachedBtn.getSignal()
        #     if attached is GPIO.HIGH:
        #         time.sleep(1)
        #         attached = boardAttachedBtn.getSignal()
        #         if attached is GPIO.HIGH:
        raw_input("Press ENTER to start system test.")
        isBoardAttached = True
        statusled.setDutyCycle(50)

        # Initialize system test
        systest = Systemtest()
        systest.setVerbose(True)

        # Download Firmware
        # retcode = programmer.flashFirmware()
        # print "Testing, if firmware was successfully loaded."
        # systest.testEquals(retcode, 0)

        # Press button to turn on RPi
        btn.setPressed()
        time.sleep(1.2)
        print "Testing, if button turns on the supply voltage."
        systest.testEquals(rpi5v.getSignal(), GPIO.HIGH)

        # # check, if MCP23017 components can be found
        # try:
        #     result = check_output(
        #         "sudo i2cdetect -y 1 | grep \"20: 20\"", shell=True)
        #     print "Testing, if GPIO expanders can be found."
        #     systest.testEquals(result[:27], "20: 20 -- -- -- -- -- -- 27")
        # except CalledProcessError, e:
        #     systest.testEquals(0, 1)

        # Set RPi_Status bit
        rpistatus.setHIGH()
        # Release button to turn off RPi
        btn.setReleased()
        time.sleep(0.1)
        print "Testing, if supply voltage is high and if shutdown signal is high."
        systest.testEquals(rpi5v.getSignal(), GPIO.HIGH)
        systest.testEquals(rpishutdown.getSignal(), GPIO.HIGH)

        # Set RPi_Status bit
        rpistatus.setLOW()
        time.sleep(0.1)
        print "Testing, if supply voltage is low."
        systest.testEquals(rpi5v.getSignal(), GPIO.LOW)

        if systest.hasPassed():
            print "System test passed."
            statusled.setDutyCycle(100)
        else:
            print "System test FAILED."
            statusled.setFrequency(5)

        # isBoardAttached = True
        # while isBoardAttached is True:
        #     attached = boardAttachedBtn.getSignal()
        #     if attached is GPIO.LOW:
        #         time.sleep(1)
        #         attached = boardAttachedBtn.getSignal()
        #         if attached is GPIO.LOW:
        #             isBoardAttached = False
        raw_input("Press ENTER to finish system test.")
        statusled.setFrequency(1)
        statusled.setDutyCycle(0)


if __name__ == '__main__':
    main()
