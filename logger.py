#!/usr/bin/python
import minimalmodbus
import serial
from time import sleep, time
from influxdb import InfluxDBClient


SENSOR_PORT = '/dev/ttyUSB0'

ADDRESS = 1
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
minimalmodbus.PARITY=serial.PARITY_NONE
minimalmodbus.STOPBITS = 2
minimalmodbus.BAUDRATE=19200
sensor = minimalmodbus.Instrument(SENSOR_PORT, slaveaddress=ADDRESS)

lastPostTimestamp = time()

moisture = 0
temperature = 0

dbclient = InfluxDBClient(host='localhost', port=8086)
dbclient.switch_database('soil_sensors')

while True:
	if time() - lastPostTimestamp > 30:
		try:
			moisture = sensor.read_register(0, functioncode=4)
			temperature = sensor.read_register(1, functioncode=4, numberOfDecimals=1, signed=True)
			point=[
			{"measurement":"data", 
			"tags":{"plant":"begonija"}, 
			"fields":{"temperature":temperature*1.0, "moisture":moisture*1.0}}]
			try:
				dbclient.write_points(point)
			except:
				print("#could not post")
		except(IOError, ValueError):
			print("#could not read sensor")
		
		lastPostTimestamp = time()
