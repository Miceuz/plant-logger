#!/usr/bin/python
from time import sleep, time
from influxdb import InfluxDBClient
import RPi.GPIO as gpio
from chirp_modbus import SoilMoistureSensor

import serial
import minimalmodbus

import paho.mqtt.client as paho

DEFAULT_BAUDRATE = 19200
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = 2


READING_INTERVAL_S = 3
SENSOR_PORT = '/dev/ttyUSB0'

gpio.setmode(gpio.BCM)

GREEN = 25
RED = 24
gpio.setup(GREEN, gpio.OUT)
gpio.setup(RED, gpio.OUT)

led = gpio.LOW

broker = "sensors.technarium.lt"
port=1883
def on_publish(client, userdata, result):
    print("published")
    pass
mqtt_client = paho.Client("plant-logger")
mqtt_client.on_publish = on_publish
mqtt_client.connect(broker, port)

def blink():
    global led
    gpio.output(GREEN, led);
    if gpio.LOW == led:
        led = gpio.HIGH
    else:
        led = gpio.LOW

error = False;

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
                                blink()
				addresses.append(i)
				if verbose:
					print('FOUND!')
				if findOne:
					return addresses
		except (IOError):
			if verbose:
				print("nope...")
                        error = True
			pass
                gpio.output(GREEN, gpio.LOW)
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
		# gpio.output(27, gpio.HIGH)
	except:
		print("#could not post")
		# gpio.output(27, gpio.LOW)
import json

def logOne(address):
        global mqtt_broker
	global SENSOR_PORT
	sensor = SoilMoistureSensor(address = address, serialport = SENSOR_PORT)
	try:
		moisture = sensor.getMoisture()
		temperature = sensor.getTemperature()
		postToDb(formatForDb(address, moisture, temperature, "OK"))
                ret = mqtt_client.publish('/akademija/sensors', json.dumps({'address':address, 'moisture':moisture, 'temperature':temperature}))
	except(IOError, ValueError):
                error = True
		postToDb(formatForDb(address, "ERROR"))
		# gpio.output(27, gpio.LOW)
		print("#could not read sensor " + str(address))


dbclient = InfluxDBClient(host='localhost', port=8086)
dbclient.switch_database('soil')



while True:
	found = scanBus(serialport=SENSOR_PORT, endAddress = 80, findOne=False, verbose=False, serialbaudrate=19200, serialstopbits=2)
        
        if found:
		print("Found " + str(len(found)) + " sensors: " + str(found))
		for address in found:
			logOne(address)
        else:
            error = True
        
        if error:
            gpio.output(RED, gpio.HIGH)
	
        sleep(READING_INTERVAL_S)
        gpio.output(RED, gpio.LOW)
        error = False

