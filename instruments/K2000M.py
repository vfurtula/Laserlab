# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re, random, visa
import numpy as np
import matplotlib.pyplot as plt

class K2000M:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		
		self.testmode = testmode
		if self.testmode:
			print("Testmode: K2000M port opened")
			self.isopen = True
		elif not self.testmode:
			self.ser = serial.Serial(my_serial, baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3)
			#rm = visa.ResourceManager()
			#self.ser = rm.open_resource(my_serial)
			self.isopen = True
			#self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
			print("K2000M serial port:", my_serial)
			time.sleep(2)
			
	############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_number(self,s):
		try:
			float(s)
			return True
		except ValueError:
			pass
		
		try:
			import unicodedata
			unicodedata.numeric(s)
			return True
		except (TypeError, ValueError):
			pass
		
		return False
	
	# read from the serial
	def readBytes(self):
		eol=b"\r\n"
		read_buffer=bytearray()
		while True:
			try:
				c=self.ser.read(1)
			except Exception as e:
				print(''.join(["Fault while reading a byte:\n",str(e)]))
				self.ser.flush()
				return ""
			
			if c:
				read_buffer+=c
				if read_buffer[-2:]==eol:
					break
			else:
				break
			
		try:
			data=read_buffer.decode()
		except Exception as e: # catch error and ignore it
			print(''.join(["Faulty byte conversion:\n",str(e)]))
			self.ser.flush()
			return ""
		
		return data
	
	####################################################################
	# K2000M functions
	####################################################################
	
	def return_id(self):
		if self.testmode:
			return "Testmode: return_id K2000M"
		elif not self.testmode:
			self.ser.write(''.join(["*idn?\r\n"]).encode())
			val=self.readBytes()
			return val
		
	def set_dc_voltage(self):
		if self.testmode:
			return "Testmode: set_dc_voltage K2000M"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:volt:dc")
			self.ser.write(":sense:volt:dc:nplc 3")
			#self.ser.write(":sense:volt:dc:rang:upp 15") #possibly bad resolution
			self.ser.write(":sense:volt:dc:rang:auto 1")
			
	def return_voltage(self,*argv):
		if self.testmode:
			time.sleep(0.1)
			if argv:
				return argv[0]+random.uniform(-1,1)
			else:
				return random.uniform(-1,1)
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			while True:
				self.ser.write(''.join([":read?\r\n"]).encode())
				val=self.readBytes()
				
				val = val.split(',')[0][:-4]
				if self.is_number(val):
					#print("return_reffreq: ", val)
					return float(val)
				else:
					print("Bad value returned from K2000M (read command):", val)
					
	def is_open(self):
		return self.isopen

	def close(self):
		if self.testmode:
			print("Testmode: K2000M stepper port flushed and closed")
			self.isopen=False
		elif not self.testmode:
			self.ser.close()
			print("Status: K2000M stepper port flushed and closed")
			self.isopen=False
			
			
def main():
  
	# call the sr510 port
	model_510 = K2000M("/dev/ttyUSB0", False)
	
	print(model_510.return_id())
	
if __name__ == "__main__":
	
  main()
  


