#!/usr/bin/python
import minimalmodbus
import serial
from time import sleep, time
from influxdb import InfluxDBClient
import RPi.GPIO as gpio

READING_INTERVAL_S = 3
SENSOR_PORT = '/dev/ttyUSB0'

ADDRESS = 1
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
minimalmodbus.PARITY=serial.PARITY_NONE
minimalmodbus.STOPBITS = 2
minimalmodbus.BAUDRATE=19200
sensor = minimalmodbus.Instrument(SENSOR_PORT, slaveaddress=ADDRESS)

gpio.setmode(gpio.BCM)
gpio.setup(27, gpio.OUT)

lastPostTimestamp = time()

moisture = 0
temperature = 0

dbclient = InfluxDBClient(host='localhost', port=8086)
dbclient.switch_database('soil_sensors')

def formatForDb(moisture, temperature):
	points=[{
			"measurement":"data", 
            "tags":{"plant":"begonija"}, 
			"fields":{"temperature":temperature*1.0, "moisture":moisture*1.0}
			}]
	return points

def formatForDb(moisture, temperature, sensor_status):
	points=[{
			"measurement":"data", 
            "tags":{"plant":"begonija"}, 
			"fields":{"temperature":temperature*1.0, 
					  "moisture":moisture*1.0, 
					  "sensor_status":sensor_status}
			}]
	return points

def formatForDb(sensor_status):
	points=[{
			"measurement":"data", 
            "tags":{"plant":"begonija"}, 
			"fields":{"sensor_status":sensor_status}
			}]
	return points

def postToDb(points):
	try:
		dbclient.write_points(points)
		gpio.output(27, gpio.HIGH)
	except:
		print("#could not post")
		gpio.output(27, gpio.LOW)

try:
	while True:
		if time() - lastPostTimestamp > READING_INTERVAL_S:
			try:
				moisture = sensor.read_register(0, functioncode=4)
				temperature = sensor.read_register(1, functioncode=4, numberOfDecimals=1, signed=True)
				postToDb(formatForDb(moisture, temperature, "OK"))
			except(IOError, ValueError):
				postToDb(formatForDb("ERROR"))
				gpio.output(27, gpio.LOW)
				print("#could not read sensor")

			lastPostTimestamp = time()
except KeyboardInterrupt:
	print("Exiting...")
finally:
	GPIO.cleanup()
