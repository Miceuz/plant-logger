#!/usr/bin/python
from time import sleep, time
from influxdb import InfluxDBClient
import RPi.GPIO as gpio
from chirp_modbus import SoilMoistureSensor

import serial

DEFAULT_BAUDRATE = 19200
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = 2


READING_INTERVAL_S = 3
SENSOR_PORT = '/dev/ttyUSB0'


def scanBus(serialport, startAddress = 1, endAddress = 247, verbose=False, findOne=False, serialbaudrate=DEFAULT_BAUDRATE, serialparity=DEFAULT_PARITY, serialstopbits=DEFAULT_STOPBITS):
	addresses=[]
	if verbose:
		print("Scanning bus from " +str(startAddress) + " to " + str(endAddress))
	for i in range(startAddress, endAddress+1):
		try:
			if verbose:
				print('Trying address: ' + str(i))

			# minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
			# minimalmodbus.PARITY=serial.PARITY_NONE
			# minimalmodbus.STOPBITS = serialstopbits
			# minimalmodbus.BAUDRATE = serialbaudrate
			
			sensor = minimalmodbus.Instrument(serialport, slaveaddress=i)
			sensor.serial.baudrate = serialbaudrate
			sensor.serial.stopbits = serialstopbits
			sensor.close_port_after_each_call = True

			addressRead = sensor.read_register(0, functioncode=3)
			if(i == addressRead):
				addresses.append(i)
				if verbose:
					print('FOUND!')
				if findOne:
					return addresses
		except (IOError):
			if verbose:
				print("nope...")
			pass
	return addresses

def formatForDb(address, sensor_status):
	points=[{
			"measurement":"plant_data", 
            "tags":{"address": address}, 
			"fields":{"sensor_status":sensor_status}
			}]
	return points

def formatForDb(address, moisture, temperature):
	points=[{
			"measurement":"plant_data", 
            "tags":{"address":address}, 
			"fields":{"temperature":temperature, "moisture":moisture}
			}]
	return points

def formatForDb(address, moisture, temperature, sensor_status):
	points=[{
			"measurement":"plant_data", 
            "tags":{"address":address}, 
			"fields":{"temperature":temperature, 
					  "moisture":moisture, 
					  "sensor_status":sensor_status}
			}]
	return points

def postToDb(points):
	try:
		dbclient.write_points(points)
		gpio.output(27, gpio.HIGH)
	except:
		print("#could not post")
		gpio.output(27, gpio.LOW)

def logOne(address):
	global SENSOR_PORT
	sensor = SoilMoistureSensor(address = address, serialport = SENSOR_PORT)
	try:
		moisture = sensor.getMoisture()
		temperature = sensor.getTemperature()
		postToDb(formatForDb(address, moisture, temperature, "OK"))
	except(IOError, ValueError):
		postToDb(formatForDb(address, "ERROR"))
		gpio.output(27, gpio.LOW)
		print("#could not read sensor " + str(address))



while True:
	found = scanBus(serialport=SENSOR_PORT, endAddress = 80, findOne=False, verbose=False, serialbaudrate=19200, serialstopbits=2)
	if found:
		print("Found " + str(len(found)) + " sensors: " + str(found))
		for address in found:
			logOne(address)

	sleep(READING_INTERVAL_S)