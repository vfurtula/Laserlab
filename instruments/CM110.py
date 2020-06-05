#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import sys, serial, argparse, time, random
import matplotlib.pyplot as plt


class CM110:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		self.my_serial=my_serial
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: CM110 port opened")
			self.isopen = True
		elif not self.testmode:
			self.ser = serial.Serial(port=self.my_serial, baudrate=9600, parity='N', stopbits=1)
			print("CM110 serial port:", self.my_serial)
			time.sleep(1)
			self.isopen = True
			self.dataok = False
		
	# read from the serial
	def readBytes(self,nob):
		data_ord=[]
		while True:
			data=self.ser.read(1)
			data_ord.extend([ord(data)])
			if data_ord[-1] in [24,27]:
				if len(data_ord)==nob:
					#print(data_ord)
					self.dataok = True
					break
				else:
					self.dataok = False
					print(data_ord)
					print(''.join(["Number of return bytes is ",str(len(data_ord))," but readBytes expected ",str(nob),". Trying again..."]))
					break
				
		return data_ord
	
	####################################################################
	# CM110 functions
	####################################################################
	
	def get_version(self):
		return "Spectral Products CM110"
	
	def set_um(self):
		#00 set units to microns
		if self.testmode:
			return "testmode set_um"
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [50,0]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(2)
			print("Status byte for set_um:", format(output[-2],'08b'))
			print("Ready signal for set_um:", output[-1])
			return output[-1]

	def set_nm(self):
		#01 set units to nm
		if self.testmode:
			return "testmode set_nm"
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [50,1]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(2)
			print("Status byte for set_nm:", format(output[-2],'08b'))
			print("Ready signal for set_nm:", output[-1])
			return output[-1]
	
	def set_as(self):
		#02 set units to angstroms
		if self.testmode:
			return "testmode set_as"
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [50,2]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(2)
			print("Status byte for set_as:", format(output[-2],'08b'))
			print("Ready signal for set_as:", output[-1])
			return output[-1]
	
	def set_goto(self,val):
		if self.testmode:
			return "testmode set_goto"
		elif not self.testmode:
			#GOTO to the very start of the scan                         		
			#calculate condition parameters suitable for byte operation
			multiplicator=val//256 #highbyte, 0 for numbers below 256
			runtohere=val-256*multiplicator #lowbyte
			#send the parameters to the CM110 monochromator
			self.dataok = False
			while not self.dataok:
				for tal in [16,multiplicator,runtohere]:
					self.ser.write(chr(tal).encode())
				print("...positioning scanner to the wavelength", val, "nm")
				time.sleep(2)
				output=self.readBytes(2)
			print("Status byte for set_goto:", format(output[-2],'08b'))
			print("Ready signal for set_goto:", output[-1])
			return output[-1]
		
	def set_stepsize(self,val):
		if self.testmode:
			return "testmode set_stepsize"
		elif not self.testmode:
			if val<128:
				#call STEP and set setepsize
				self.dataok = False
				while not self.dataok:
					for tal in [55,val]:
						self.ser.write(chr(tal).encode())
					output=self.readBytes(2)
				print("Status byte for set_stepsize:", format(output[-2],'08b'))
				print("Ready signal for set_stepsize:", output[-1])
				return output[-1]
		
	def make_step(self):
		#Moves the monochromator by a preset amount defined by the set_stepsize
		if self.testmode:
			#print("testmode make_step")
			return "testmode make_step"
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				self.ser.write(chr(54).encode())
				output=self.readBytes(2)
			#print("Status byte for make_step:", format(output[-2],'08b'))
			#print("Ready signal for make_step:", output[-1])
			return output[-1]
	
	def set_scan(self,start,end):
		if self.testmode:
			return "testmode set_scan"
		elif not self.testmode:
			#GOTO to the very start of the scan                         		
			#calculate condition parameters suitable for byte operation
			# START parameters
			mp_start=start//256 #highbyte, 0 for numbers below 256
			runtohere_start=start-256*mp_start #lowbyte
			# END parameters
			mp_end=end//256 #highbyte, 0 for numbers below 256
			runtohere_end=end-256*mp_end #lowbyte
			#send the parameters to the CM110 monochromator
			self.dataok = False
			while not self.dataok:
				for tal in [12,mp_start,runtohere_start,mp_end,runtohere_end]:
					self.ser.write(chr(tal).encode())
				print("...positioning scanner to the wavelength", val, "nm")
				output=self.readBytes(2)
			print("Status byte for set_scan:", format(output[-2],'08b'))
			print("Ready signal for set_scan:", output[-1])
			return output[-1]
	
	def set_speed(self,speed):
		if self.testmode:
			return "testmode set_speed"
		elif not self.testmode:
			#GOTO to the very start of the scan                         		
			#calculate condition parameters suitable for byte operation
			multiplicator=speed//256 #highbyte, 0 for numbers below 256
			runtohere=speed-256*multiplicator 
			#send the parameters to the CM110 monochromator
			self.dataok = False
			while not self.dataok:
				for tal in [13,multiplicator,runtohere]:
					self.ser.write(chr(tal).encode())
				print("...positioning scanner to the wavelength", val, "nm")
				output=self.readBytes(2)
			print("Status byte for set_speed:", format(output[-2],'08b'))
			print("Ready signal for set_speed:", output[-1])
			return output[-1]
	
	def get_position(self):
		# get current position of CM110
		if self.testmode:
			return random.randint(300,2000)
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [56,0]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(4)
			position = 256*output[-4]+output[-3]
			print("The current position of CM110 is", position)
			print("Status byte for get_position:", format(output[-2],'08b'))
			print("Ready signal for get_position:", output[-1])
			return position
	
	def get_grprmm(self):
		# get grooves per mm of CM110
		if self.testmode:
			return random.uniform(0,100)
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [56,2]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(4)
			grprmm = 256*output[-4]+output[-3]
			print("The grooves per mm of CM110 is", grprmm)
			print("Status byte for get_grprmm:", format(output[-2],'08b'))
			print("Ready signal for get_grprmm:", output[-1])
			return grprmm
	
	def get_speed(self):
		# get speed A/s of CM110
		if self.testmode:
			return random.uniform(0,100)
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [56,5]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(4)
			speed = 256*output[-4]+output[-3]
			print("The speed of CM110 is", speed, " A/s")
			print("Status byte for get_speed:", format(output[-2],'08b'))
			print("Ready signal for get_speed:", output[-1])
			return speed
	
	def get_units(self):
		# get current position of CM110
		if self.testmode:
			return "testmode get_units"
		elif not self.testmode:
			self.dataok = False
			while not self.dataok:
				for tal in [56,14]:
					self.ser.write(chr(tal).encode())
				output=self.readBytes(4)
				
			if output[-3]==0:
				mystr="um"
			elif output[-3]==1:
				mystr="nm"
			elif output[-3]==2:
				mystr="as"
			else:
				mystr="(unknown)"
				print("Unkown units!")
			print("Current units of CM110 are", mystr)
			print("Status byte for get_position:", format(output[-2],'08b'))
			print("Ready signal for get_position:", output[-1])
			return mystr
		
	def get_echo(self):
		if self.testmode:
			return "testmode get_echo"
		elif not self.testmode:
			#Moves the monochromator by a preset amount defined by the set_stepsize
			self.ser.timeout = 1
			self.dataok = False
			while not self.dataok:
				self.ser.write(chr(27).encode())
				output=self.readBytes(1)
			self.ser.timeout=None
			print("Echo signal coming from CM110!")
			
	# clean up serial
	def close(self):
		if self.testmode:
			print("testmode CM110 port flushed and closed")
			self.isopen = False
		elif not self.testmode:
			# flush and close serial
			self.ser.flush()
			self.ser.close()
			print("CM110 port flushed and closed")
			self.isopen = False
		
	def is_open(self):
		# flush and close serial
		return self.isopen
	
	
	
	
	
def main():
	
	# call the cm110 port
	cm110 = CM110("/dev/ttyUSB4",False)
	# do some testing here
	cm110.set_nm()
	cm110.get_position()
	cm110.set_goto(500)
	cm110.get_position()
	cm110.set_stepsize(100)
	for ii in list(range(10)):
		cm110.make_step()
		time.sleep(0.2)
		print(cm110.get_position())
	cm110.get_position()
	#cm110.get_grprmm()
	#cm110.get_speed()	
	#cm110.set_goto(2500)
	#cm110.set_speed(500)
	#cm110.set_scan(1000,1500)	

	# clean up and close the cm110 port
	cm110.close()
 
if __name__ == "__main__":
	
	main()
  


