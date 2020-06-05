#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import sys, serial, argparse, time, re, random
import numpy as np
import matplotlib.pyplot as plt




class SR530:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: SR530 port opened")
			self.isopen = True
		elif not self.testmode:
			self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_TWO)
			print("SR530 serial port:", my_serial)
			self.isopen = True
			time.sleep(1)

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
		data=""
		while True:
			data_=self.ser.read(1)
			data+=data_.decode()
			if data[-1] in ["\r"]:
				return data[:-1]
	
	####################################################################
	# SR530 functions
	####################################################################
	
	def get_version(self):
		return "Standford Research SR530"
	
	def set_timeout(self,val):
		if self.testmode:
			print("Testmode: set_timeout method called")
		elif not self.testmode:
			self.ser.timeout=val
		
	def set_local(self):
		if self.testmode:
			print("Testmode: set_local method called")
		elif not self.testmode:
			my_string=''.join(['I0\r'])
			self.ser.write(my_string.encode())
		
	def set_remote(self):
		if self.testmode:
			print("Testmode: set_remote method called")
		elif not self.testmode:
			my_string=''.join(['I1\r'])
			self.ser.write(my_string.encode())
			print("Set_remote method called")
		
	def set_wait(self,val):
		if self.testmode:
			print("Testmode: set_wait method called")
		elif not self.testmode:
			my_string=''.join(['W',str(val),'\r'])
			self.ser.write(my_string.encode())
			print("Set_wait method called")
		
	def display_voltage(self):
		if self.testmode:
			print("Testmode: display_voltage method called")
		elif not self.testmode:
			my_string=''.join(['S0\r'])
			self.ser.write(my_string.encode())
		
	def return_statusbyte(self):
		if self.testmode:
			return '{0:08b}'.format(5)
		elif not self.testmode:
			try:
				self.ser.write(''.join(['Y\r']).encode())
				val=self.readBytes()
			except Exception as e:
				raise Exception(''.join(["No return from the Y command!"]))
			
			if self.is_number(val):
				val_='{0:08b}'.format(int(val))
				print("return_satus_bytes: ", val_)
				return val_
			else:
				raise Exception(''.join(["Bad value returned from lock-in (Y command):", val]))
		
	def return_wait(self):
		if self.testmode:
			return 0.0
		elif not self.testmode:
			try:
				self.ser.write(''.join(['W\r']).encode())
				val=self.readBytes()
			except Exception as e:
				raise Exception(''.join(["No return from the W command!"]))
			
			if self.is_number(val):
				#print("return_wait:",val)
				return float(val)
			else:
				raise Exception(''.join(["Bad value returned from lock-in (W command):", val]))
		
	def return_reffreq(self):
		if self.testmode:
			time.sleep(0.1)
			return random.randint(1,1000)
		elif not self.testmode:
			try:
				self.ser.write(''.join(['F\r']).encode())
				val=self.readBytes()
			except Exception as e:
				raise Exception(''.join(["No return from the F command!"]))
			
			if self.is_number(val):
				#print("return_reffreq: ", val)
				return float(val)
			else:
				raise Exception(''.join(["Bad value returned from lock-in (F command):", val]))
		
	def return_voltage(self,val):
		if self.testmode:
			time.sleep(0.1)
			return random.uniform(0,10)
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			try:
				self.ser.write(''.join(['Q',val,'\r']).encode())
				val=self.readBytes()
			except Exception as e:
				raise Exception("No return from the Q command!")
			
			if self.is_number(val):
				#print("return_reffreq: ", val
				return float(val)
			else:
				raise Exception(''.join(["Bad value returned from lock-in (Q command):", val]))
		
	# clean up serial
	def close(self):
		# flush and close serial
		if self.testmode:
			print("Testmode: SR530 port flushed and closed")
			self.isopen=False
		elif not self.testmode:
			self.ser.flush()
			self.ser.close()
			print("SR530 port flushed and closed")
			self.isopen=False
		
	def is_open(self):
		return self.isopen
	
	
	
		
		
def main():
	
	# call the sr530 port
	model_530 = SR530("/dev/ttyUSB3",False)
	model_530.set_remote()
	model_530.set_wait(1)
	print(model_530.return_wait())
	model_530.set_wait(2)
	print(model_530.return_wait())
	
	for i in range(10):
		print(model_530.return_voltage(1))
		print(model_530.return_statusbyte())
		
	'''
	model_530.set_remote()
	model_530.display_voltage()
	model_530.return_wait()
	model_530.set_wait(1)
	model_530.return_statusbyte()
	for i in range(10):
		model_530.return_voltage()
	'''
	
	# clean up and close the sr530 port
	model_530.close()
	
if __name__ == "__main__":
	
  main()
  


