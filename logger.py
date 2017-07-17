#!/usr/bin/python
import minimalmodbus
import serial
from time import sleep, time
import thingspeak
import ctypes

channel = thingspeak.Channel(302723, api_key='81017W69ZTW9GREW', write_key='FX5IXEFIS6YTEGN9')
libc = ctypes.CDLL("libc.so.6")

SENSOR_PORT = '/dev/ttyUSB1'
SCALE_PORT = '/dev/ttyUSB0'

ADDRESS = 1
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
minimalmodbus.PARITY=serial.PARITY_NONE
minimalmodbus.STOPBITS = 2
minimalmodbus.BAUDRATE=19200
sensor = minimalmodbus.Instrument(SENSOR_PORT, slaveaddress=ADDRESS)
scale = serial.Serial(SCALE_PORT)

lastPostTimestamp = time()

weight = 0
moisture = 0
temperature = 0

scale.write('0\r\n')
while True:
	weight = int(float(scale.readline()))
	#sleep(0.1)
	if time() - lastPostTimestamp > 30:
		try:
			moisture = sensor.read_register(0, functioncode=4)
			temperature = sensor.read_register(1, functioncode=4, numberOfDecimals=1, signed=True)
			try:
				channel.update({'field1':moisture, 'field2':temperature, 'field3':weight})
			except:
				print("#could not post")
			print(weight, moisture, temperature)
			libc.sync()
		except(IOError, ValueError):
			print("#could not read sensor")
		
		lastPostTimestamp = time()
