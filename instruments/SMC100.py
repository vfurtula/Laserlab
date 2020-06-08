#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import sys, serial, time, random


class SMC100:
	
	def __init__(self,my_serial,testmode):
		self.testmode = testmode
		
		if self.testmode:
			print("Testmode: SMC100 port opened")
			self.isopen = True
		elif not self.testmode:
			# activate the serial. CHECK the serial port name!
			self.ser = serial.Serial(my_serial,baudrate=57600,parity=serial.PARITY_NONE,xonxoff=True,bytesize=serial.EIGHTBITS,stopbits=serial.STOPBITS_ONE, timeout=2)
			print("SMC100 serial port:", my_serial)
			self.isopen = True
			self.stopped = False
			
			time.sleep(0.5)
			
			
	def set_timeout(self,val):
		if self.testmode:
			print("Testmode: SMC100 set_timeout")
		elif not self.testmode:
			self.ser.timeout=val
		
	############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_int(self,s):
		try: 
			int(s)
			return True
		except ValueError:
			return False
		
		
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
	def readBytes(self,fun):
		eol=b'\r\n'
		read_buffer=bytearray()
		while True:
			try:
				c=self.ser.read(1)
			except Exception as e:
				print(''.join(["Fault while reading byte from ", fun, " command:\n",str(e)]))
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
			print(''.join(["Faulty byte conversion in ",fun]))
			self.ser.flush()
			return ""
		
		if fun in data:
			#print(data)
			idx=data.find(fun)
			return data[idx+len(fun):-2]
		else:
			print(''.join(["Expected return from ", fun, " but received return from ", data[:-2]]))
			self.ser.flush()
			return ""
		
	'''
	def readBytes(self,fun):
		
		try:
			read_buffer=self.ser.read_until(expected=LF)
		except Exception as e: # catch error and ignore it
			print(''.join(["Unaccepted EoL received from ",fun]))
			return ""
			
		try:
			data=read_buffer.decode()
		except Exception as e: # catch error and ignore it
			print(''.join(["Faulty byte conversion in ",fun]))
			return ""
		
		if fun in data:
			#print(data)
			idx=data.find(fun)
			return data[idx+len(fun):-2]
		else:
			print(''.join(["Expected return from ", fun, " but received return from ", data[:-2]]))
			return ""
	'''
	
	####################################################################
	# SMC100 functions
	####################################################################
	
	def set_reset(self,axs):
		if self.testmode:
			print("Testmode: SMC100 set_reset")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'RS',"\r\n"]).encode())
			time.sleep(5)
			
			
	def set_config(self,axs,state):
		if self.testmode:
			print("Testmode: SMC100 set_config")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'PW',str(state),"\r\n"]).encode())
			if state==0:
				time.sleep(10)
			elif state==1:
				time.sleep(1)
			else:
				raise ValueError("Only state 1 or state 0 accepted in the configuration mode!")
			
			
	def set_speed(self,axs,sp):
		if self.testmode:
			print("Testmode: SMC100 set_speed")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'VA',str(sp),"\r\n"]).encode())
			
			
	def set_acc(self,axs,acc):
		if self.testmode:
			print("Testmode: SMC100 set_acc")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'AC',str(acc),"\r\n"]).encode())
			
			
	def set_sr(self,axs,sr):
		if self.testmode:
			print("Testmode: SMC100 set_sr")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'SR',str(sr),"\r\n"]).encode())
			
			
	def set_sl(self,axs,sl):
		if self.testmode:
			print("Testmode: SMC100 set_sl")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'SL',str(sl),"\r\n"]).encode())
			
			
	def set_ht(self,axs,ht):
		if self.testmode:
			print("Testmode: SMC100 set_ht")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'HT',str(ht),"\r\n"]).encode())
			
			
	def return_ht(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_ht")
			return 1
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'HT'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
			else:
				if self.is_number(val):
					return int(val)
				else:
					val = ""
			
			
	def return_config(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_config")
			return 32
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'PW'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
			else:
				if self.is_number(val):
					return int(val)
				else:
					val = ""
				
				
	def return_speed(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_speed")
			return random.uniform(0,10)
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'VA'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
				if self.is_number(val):
					return float(val)
				else:
					val = ""
					
					
	def return_sl(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_sl")
			return random.uniform(0,10)
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'SL'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
				if self.is_number(val):
					return float(val)
				else:
					val = ""
					
					
	def return_sr(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_sr")
			return random.uniform(0,10)
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'SR'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
				if self.is_number(val):
					return float(val)
				else:
					val = ""
					
					
	def return_acc(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_acc")
			return random.uniform(0,10)
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'AC'])
			while not val:
				self.ser.write(''.join([mystr,'?',"\r\n"]).encode())
				val=self.readBytes(mystr)
				if self.is_number(val):
					return float(val)
				else:
					val = ""
			
			
	def return_ver(self,axs):
		if self.testmode:
			return "Testmode: SMC100 return_ver"
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'VE'])
			while not val:
				self.ser.write(''.join([mystr,"\r\n"]).encode())
				val=self.readBytes(mystr)
			else:
				return val
			
			
	def return_ts(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_ts")
			return "Testmode: SMC100 return_TS_32"
		elif not self.testmode:
			
			val=""
			mystr=''.join([str(axs),'TS'])
			while not val:
				self.ser.write(''.join([mystr,"\r\n"]).encode())
				val = self.readBytes(mystr)
				#print("return_ts",val)
			else:
				return val
			
			
	def go_home(self,axs):
		if self.testmode:
			print("Testmode: SMC100 go_home")
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'OR',"\r\n"]).encode())
			self.stopped = False
			
			tal=0
			while not self.stopped:
				val=self.return_ts(axs)
				print(val,tal)
				tal+=1
				if val[-2:] in ["32","33","34","35"]:
					return
			else:
				self.move_stop(axs)
				return
			
			
	def abort(self):
		self.stopped = True
		
		
	def move_stop(self,axs):
		if self.testmode:
			print("Testmode: SMC100 move_stop")
			return "Testmode: SMC100 move_stop"
		elif not self.testmode:
			self.ser.write(''.join([str(axs),'ST',"\r\n"]).encode())
		
		
	def return_pos(self,axs):
		if self.testmode:
			print("Testmode: SMC100 return_pos")
			if hasattr(self,"test_pos"):
				return float(self.test_pos)
			else:
				return random.uniform(0,25)
		elif not self.testmode:
			
			val=""
			mystr=''.join([str(axs),'TP'])
			while not val:
				self.ser.write(''.join([mystr,"\r\n"]).encode())
				val=self.readBytes(mystr)
				#print("return_pos",val)
			else:
				return float(val)
				
				
	def move_abspos(self,axs,pos):
		if self.testmode:
			print("Testmode: SMC100 move_abspos")
			self.test_pos = pos
			return float(self.test_pos)
		elif not self.testmode:
			start_pos = self.return_pos(axs)
			motion_time = self.return_motiontime(axs,pos-start_pos)
			self.ser.write(''.join([str(axs),'PA',str(pos),"\r\n"]).encode())
			self.stopped = False
			
			time_start = time.time()
			while not self.stopped:
				if time.time()-time_start > motion_time:
					val=self.return_ts(axs)
					if "33" in val:
						pos = self.return_pos(axs)
						return pos
			else:
				self.move_stop(axs)
				pos = self.return_pos(axs)
				return pos
			
			
	def move_relpos(self,axs,pos):
		if self.testmode:
			print("Testmode: SMC100 move_relpos")
			self.test_pos = pos
			return float(self.test_pos)
		elif not self.testmode:
			start_pos = self.return_pos(axs)
			motion_time = self.return_motiontime(axs,pos)
			self.ser.write(''.join([str(axs),'PR',str(pos),"\r\n"]).encode())
			self.stopped = False
			
			time_start = time.time()
			while not self.stopped:
				if time.time()-time_start > motion_time:
					val=self.return_ts(axs)
					if "33" in val:
						pos = self.return_pos(axs)
						return pos
			else:
				self.move_stop(axs)
				pos = self.return_pos(axs)
				return pos
			
			
	def my_reset(self,axs):
		if self.testmode:
			print("Testmode: SMC100 my_reset")
			return self.return_pos(axs)
		elif not self.testmode:
			self.go_home(axs)
			return self.return_pos(axs)
			
			
	def return_motiontime(self,axs,move):
		##########################
		move=abs(move)
		if move<1e-6:
			move=1e-5
		elif move>1e12:
			move=1e11
		##########################
		if self.testmode:
			print("Testmode: SMC100 return_motiontime")
			return random.uniform(0,10)
		elif not self.testmode:
			
			val = ""
			mystr=''.join([str(axs),'PT'])
			while not val:
				self.ser.write(''.join([mystr,str(move),"\r\n"]).encode())
				val=self.readBytes(mystr)
			else:
				return float(val)
			
			
	# clean up serial
	def close(self):
		if self.testmode:
			print("Testmode: SMC100 close")
			self.isopen=False
		elif not self.testmode:
			# flush and close serial
			self.ser.flush()
			self.ser.close()
			print("SMC100 port flushed and closed")
			self.isopen=False
			
	def is_open(self):
		return self.isopen
			
			
			
def test():
	
	# call the Motorstep drive port
	esp = SMC100("/dev/ttyUSB0",False)
	print("VER: ",esp.return_ver(1))
	
	#time.sleep(2)
	#print(esp.my_reset(1))
	#print(esp.move_abspos(1,2))
	
	
	for i in range(3):
		print("position axs 1: ",esp.return_pos(1))
		print(esp.move_abspos(1,2.11))
		print("position axs 1: ",esp.return_pos(1))
		print(esp.move_abspos(1,2.21))
		print("position axs 1: ",esp.return_pos(1))
		print(esp.move_abspos(1,2.31))
		#time.sleep(1)
		#print(esp.return_ts(1))
	#print("position axs 1: ",esp.return_pos(1))
	#print(esp.move_relpos(1,.2))
	#print("position axs 1: ",esp.return_pos(1))
	
	
	'''
	print("set PW: ",esp.set_config(1,1))
	print("set HT: ",esp.set_ht(1,1))
	time.sleep(2)
	print("get HT: ",esp.return_ht(1))
	print("set PW: ",esp.set_config(1,0))
	'''
	
	
	'''
	esp.set_speed(1,5)
	speed1 = esp.return_speed(1)
	print("axs1 speed:",speed1)
	
	pos1 = esp.move_abspos(1,150)
	print("axs 1 pos:",pos1)
	pos2 = esp.move_relpos(1,-20)
	print("axs 1 pos:",pos2)
	
	pos1 = esp.move_abspos(2,110)
	print("axs 2 pos:",pos1)
	pos2 = esp.move_relpos(2,-20)
	print("axs 2 pos:",pos2)
	
	pos1 = esp.move_abspos(3,90)
	print("axs 3 pos:",pos1)
	pos2 = esp.move_relpos(3,-20)
	print("axs 3 pos:",pos2)
	'''
	# clean up and close the Motorstep drive port
	esp.close()
 
if __name__ == "__main__":
	
	test()
  


