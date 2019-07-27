#!/usr/bin/python
import minimalmodbus
import serial
from time import sleep, time
from influxdb import InfluxDBClient
import RPi.GPIO as gpio
gpio.setmode(gpio.BCM)
gpio.setup(27, gpio.OUT)


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
	if time() - lastPostTimestamp > 3:
		try:
			moisture = sensor.read_register(0, functioncode=4)
			temperature = sensor.read_register(1, functioncode=4, numberOfDecimals=1, signed=True)
			point=[
			{"measurement":"data", 
                            "tags":{"plant":"begonija"}, 
			"fields":{"temperature":temperature*1.0, "moisture":moisture*1.0}}]
			#print(point)				
			try:
				dbclient.write_points(point)
				gpio.output(27, gpio.HIGH)
			except:
				print("#could not post")
				gpio.output(27, gpio.LOW)

		except(IOError, ValueError):
                        point=[
                             {"measurement":"data",
                            "tags":{"plant":"begonija"},
                            "fields":{"sensor_status":"pyzdiec"}
                            }] 
                        			
                             
			try:
				dbclient.write_points(point)
				gpio.output(27, gpio.HIGH)
			except:
				print("#could not post")
				gpio.output(27, gpio.LOW)
                        print("#could not read sensor")
		
		lastPostTimestamp = time()
