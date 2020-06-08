#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, serial, time, random


class ArdMega2560:
	
	
	def __init__(self,my_serial,testmode):
		
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		self.my_serial=my_serial
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: Ard port opened")
			self.isopen = True
		elif not self.testmode:
			self.ser = serial.Serial(self.my_serial, 115200)
			print("Arduino Mega2560 serial port:", self.my_serial)
			self.isopen = True
		
		'''
		time.sleep(0.2)
		#Initialize Arduino serial port and toggle DTR to reset Arduino
		print("Initialize Arduino and set serial port:", self.my_serial)
		#self.ser = serial.Serial(self.ardport_str, 9600)
		#time.sleep(0.2)
		self.ser.setDTR(False)
		time.sleep(1)
		self.ser.flushInput()
		self.ser.setDTR(True)
		time.sleep(1.5)
		'''
		
		
	def get_version(self):
		
		return "Arduino Mega2560"
		
		
	# Pyserial readline() function reads until '\n' is sent (other EOLs are ignored).
	# Therefore changes to readline() are required to match it with EOL character '\r'.
	# See: http://stackoverflow.com/questions/16470903/pyserial-2-6-specify-end-of-line-in-readline
	def _readline(self):
		#eol=b'\r\n'
		eol=b'\n'
		leneol=len(eol)
		line=bytearray()
		while True:
		  c=self.ser.read(1)
		  if c:
		    line+=c
		    if line[-leneol:]==eol:
		      break
		  else:
		    break
		return bytes(line[:-leneol]).decode()
	
	
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
		
		
	def get_val(self,avg_pts):
		# and pass the number of averaging points to the Arduino serial
		if self.testmode:
			return random.randint(0,1023)
		elif not self.testmode:
			if avg_pts<1:
				raise ValueError("The number of averaging points is minimum 1")
			else:
				# pass number of averaging points, 43 is + in ascii
				for tal in [43,avg_pts]:
					self.ser.write(chr(tal).encode())
					
			# Read voltage data from the serial
			line = self._readline()
			
			# first read voltage (bit no.) from the serial 
			if(len(line.split()) == 1): # expected no. of columns from Arduino
				for val in line.split():
					if self.is_number(val) and int(val)<2**10:
						return int(val)
						#Vout=self.analogRef*float(val)/(2**10-1)
					else:
						raise ValueError("Arduino output larger than 1023!")
			else:
				raise ValueError("Multiple outputs at the Arduino serial!")
		
		
	# close serial and clean up
	def close(self):
		# flush and close serial
		if self.testmode:
			print("testmode Ard port flushed and closed")
			self.isopen = False
		elif not self.testmode:
			self.ser.flush()
			self.ser.close()
			print("Arduino port flushed and closed")
			self.isopen = False
		
	def is_open(self):
		# flush and close serial
		return self.isopen
		
		
		
		
def main():
	Ard = ArdMega2560("/dev/ttyACM0",True)
	tal=0
	while tal<10:
		time.sleep(0.25)
		print(Ard.get_val(1))
		tal+=1
	Ard.close()
	
if __name__ == "__main__":
	
  main()
  
  
  
  
  
  
  
  
  
  
  
  
