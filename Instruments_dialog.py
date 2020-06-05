#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import os, re, serial, time, configparser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)

from instruments import CM110, ArdMega2560, SR530, SMC100



class Instruments_dialog(QDialog):
	
	def __init__(self, parent, inst_list,cwd,lcdst):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		self.cwd = cwd
		self.lcdst = lcdst
		
		try:
			self.config.read(''.join([self.cwd,"/config.ini"]))
			
			self.testmode_check=self.bool_(self.config.get("Instruments","testmode"))
			
			self.cm110port_str=self.config.get("Instruments","cm110port").strip().split(",")[0]
			self.cm110port_check=self.bool_(self.config.get("Instruments","cm110port").strip().split(",")[1])
			
			self.ardport_str=self.config.get("Instruments","ardport").strip().split(",")[0]
			self.ardport_check=self.bool_(self.config.get("Instruments","ardport").strip().split(",")[1])
			
			self.sr530port_str=self.config.get("Instruments","sr530port").strip().split(",")[0]
			self.sr530port_check=self.bool_(self.config.get("Instruments","sr530port").strip().split(",")[1])
			
			self.smc100port_str=self.config.get("Instruments","smc100port").strip().split(",")[0]
			self.smc100port_check=self.bool_(self.config.get("Instruments","smc100port").strip().split(",")[1])
			
			self.CM110_tm=self.bool_(self.config.get("Instruments","cm110_tm"))
			self.Ard_tm=self.bool_(self.config.get("Instruments","ard_tm"))
			self.SR530_tm=self.bool_(self.config.get("Instruments","sr530_tm"))
			self.SMC100_tm=self.bool_(self.config.get("Instruments","smc100_tm"))
			
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
			
		# Enable antialiasing for prettier plots
		self.inst_list = inst_list
		
		self.initUI()
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def initUI(self):
		
		empty_string = QLabel("",self)
		
		cm110_lbl = QLabel("CM110 serial port",self)
		cm110_lbl.setStyleSheet("color: blue")
		self.cm110Edit = QLineEdit(self.cm110port_str,self)
		self.cm110Edit.textChanged.connect(self.on_text_changed)
		self.cm110Edit.setEnabled(self.cm110port_check)
		self.cm110Edit.setFixedWidth(325)
		self.cb_cm110 = QCheckBox("",self)
		self.cb_cm110.toggle()
		self.cb_cm110.setChecked(self.cm110port_check)
		self.cm110_status = QLabel("",self)
		
		smc100_lbl = QLabel("SMC100 serial port",self)
		smc100_lbl.setStyleSheet("color: blue")
		self.smc100Edit = QLineEdit(self.smc100port_str,self)
		self.smc100Edit.textChanged.connect(self.on_text_changed)
		self.smc100Edit.setEnabled(self.smc100port_check)
		self.smc100Edit.setFixedWidth(325)
		self.cb_smc100 = QCheckBox("",self)
		self.cb_smc100.toggle()
		self.cb_smc100.setChecked(self.smc100port_check)
		self.smc100_status = QLabel("",self)
		
		ard_lbl = QLabel("Arduino serial port",self)
		ard_lbl.setStyleSheet("color: blue")
		self.ardEdit = QLineEdit(self.ardport_str,self)
		self.ardEdit.textChanged.connect(self.on_text_changed)
		self.ardEdit.setEnabled(self.ardport_check)
		self.ardEdit.setFixedWidth(325)
		self.cb_ard = QCheckBox("",self)
		self.cb_ard.toggle()
		self.cb_ard.setChecked(self.ardport_check)
		self.ard_status = QLabel("",self)
		
		sr530_lbl = QLabel("SR530 serial port",self)
		sr530_lbl.setStyleSheet("color: blue")
		self.sr530Edit = QLineEdit(self.sr530port_str,self)
		self.sr530Edit.textChanged.connect(self.on_text_changed)
		self.sr530Edit.setEnabled(self.sr530port_check)
		self.sr530Edit.setFixedWidth(325)
		self.cb_sr530 = QCheckBox("",self)
		self.cb_sr530.toggle()
		self.cb_sr530.setChecked(self.sr530port_check)
		self.sr530_status = QLabel("",self)
		
		testmode_lbl = QLabel("Connect instruments using the TESTMODE",self)
		testmode_lbl.setStyleSheet("color: magenta")
		self.cb_testmode = QCheckBox("",self)
		self.cb_testmode.toggle()
		self.cb_testmode.setChecked(self.testmode_check)
		
		self.connButton = QPushButton("Connect to selected ports",self)
		#self.connButton.setFixedWidth(150)
		
		self.saveButton = QPushButton("Save settings",self)
		self.saveButton.setEnabled(False)
		#self.saveButton.setFixedWidth(150)
		
		self.closeButton = QPushButton("CLOSE",self)
		self.closeButton.setEnabled(True)
		
		##############################################
		
		# Add all widgets
		g0_0 = QGridLayout()
		
		g0_0.addWidget(cm110_lbl,0,0)
		g0_0.addWidget(self.cb_cm110,0,1)
		g0_0.addWidget(self.cm110Edit,1,0)
		g0_0.addWidget(self.cm110_status,2,0)
		g0_0.addWidget(empty_string,3,0)
		
		g0_0.addWidget(ard_lbl,4,0)
		g0_0.addWidget(self.cb_ard,4,1)
		g0_0.addWidget(self.ardEdit,5,0)
		g0_0.addWidget(self.ard_status,6,0)
		g0_0.addWidget(empty_string,7,0)
		
		g0_0.addWidget(sr530_lbl,8,0)
		g0_0.addWidget(self.cb_sr530,8,1)
		g0_0.addWidget(self.sr530Edit,9,0)
		g0_0.addWidget(self.sr530_status,10,0)
		g0_0.addWidget(empty_string,11,0)
		
		g0_0.addWidget(smc100_lbl,12,0)
		g0_0.addWidget(self.cb_smc100,12,1)
		g0_0.addWidget(self.smc100Edit,13,0)
		g0_0.addWidget(self.smc100_status,14,0)
		g0_0.addWidget(empty_string,15,0)
		
		g0_0.addWidget(testmode_lbl,24,0)
		g0_0.addWidget(self.cb_testmode,24,1)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(self.connButton,0,0)
		g1_0.addWidget(self.saveButton,0,1)
		
		g2_0 = QGridLayout()
		g2_0.addWidget(self.closeButton,0,0)
		
		v0 = QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g1_0)
		v0.addLayout(g2_0)
		
		self.setLayout(v0) 
    
    ##############################################
	
		# run the main script
		self.connButton.clicked.connect(self.set_connect)
		self.saveButton.clicked.connect(self.save_)
		self.closeButton.clicked.connect(self.close_)
		
		self.cb_cm110.stateChanged.connect(self.cm110_stch)
		self.cb_ard.stateChanged.connect(self.ard_stch)
		self.cb_sr530.stateChanged.connect(self.sr530_stch)
		self.cb_smc100.stateChanged.connect(self.smc100_stch)
		
		##############################################
		
		# Connection warnings
		if self.inst_list.get("CM110"):
			if self.CM110_tm:
				self.cm110_status.setText("Status: TESTMODE")
				self.cm110_status.setStyleSheet("color: magenta")
			else:
				self.cm110_status.setText("Status: CONNECTED")
				self.cm110_status.setStyleSheet("color: green")
		else:
			self.cm110_status.setText("Status: unknown")
			self.cm110_status.setStyleSheet("color: black")
		
		if self.inst_list.get("SMC100"):
			if self.SMC100_tm:
				self.smc100_status.setText("Status: TESTMODE")
				self.smc100_status.setStyleSheet("color: magenta")
			else:
				self.smc100_status.setText("Status: CONNECTED")
				self.smc100_status.setStyleSheet("color: green")
		else:
			self.smc100_status.setText("Status: unknown")
			self.smc100_status.setStyleSheet("color: black")
		
		if self.inst_list.get("Ard"):
			if self.Ard_tm:
				self.ard_status.setText("Status: TESTMODE")
				self.ard_status.setStyleSheet("color: magenta")
			else:
				self.ard_status.setText("Status: CONNECTED")
				self.ard_status.setStyleSheet("color: green")
		else:
			self.ard_status.setText("Status: unknown")
			self.ard_status.setStyleSheet("color: black")
		
		if self.inst_list.get("SR530"):
			if self.SR530_tm:
				self.sr530_status.setText("Status: TESTMODE")
				self.sr530_status.setStyleSheet("color: magenta")
			else:
				self.sr530_status.setText("Status: CONNECTED")
				self.sr530_status.setStyleSheet("color: green")
		else:
			self.sr530_status.setText("Status: unknown")
			self.sr530_status.setStyleSheet("color: black")
			
		##############################################
		
		# Check boxes
		"""
		if not self.checked_list.get("CM110"):
			self.cb_cm110.setChecked(False)
		
		if not self.checked_list.get("Ard"):
			self.cb_ard.setChecked(False)
		
		if not self.checked_list.get("Oriel"):
			self.cb_oriel.setChecked(False)
		
		if not self.checked_list.get("K2001A"):
			self.cb_k2001a.setChecked(False)
		
		if not self.checked_list.get("Agilent34972A"):
			self.cb_a34972a.setChecked(False)
		
		if not self.checked_list.get("GUV"):
			self.cb_guv.setChecked(False)
		"""
		
		self.setWindowTitle("Pick-up instruments and connect")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
		
	def cm110_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.cm110Edit.setEnabled(True)
		else:
			self.cm110Edit.setEnabled(False)
			
			
	def smc100_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.smc100Edit.setEnabled(True)
		else:
			self.smc100Edit.setEnabled(False)
			
			
	def ard_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.ardEdit.setEnabled(True)
		else:
			self.ardEdit.setEnabled(False)
			
			
	def sr530_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.sr530Edit.setEnabled(True)
		else:
			self.sr530Edit.setEnabled(False)
			
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Save settings*")
		self.saveButton.setEnabled(True)
		
		
	def set_connect(self):
		
		# Connect or disconnect CM110 laser gun
		self.cm110()
		
		# Connect or disconnect Arduino power meter
		self.ard()
		
		# Connect or disconnect Arduino power meter
		self.sr530()
		
		# Connect or disconnect SMC100 laser gun
		self.smc100()
		
		# Save all the performed changes
		self.save_()
		
		# Set the testmode check box correctly for the next run
		if self.inst_list.get("Ard") or self.inst_list.get("CM110") or self.inst_list.get("SR530") or self.inst_list.get("SMC100"):
			if self.cb_testmode.isChecked():
				self.cb_testmode.setChecked(True)
			else:
				self.cb_testmode.setChecked(False)
		else:
			self.cb_testmode.setChecked(False)
			
		if not self.inst_list.get("Ard") and not self.inst_list.get("CM110") and not self.inst_list.get("SR530") and not self.inst_list.get("SMC100"):
			QMessageBox.critical(self, "Message","No instruments connected. At least 1 instrument is required.")
			return
				
				
	def sr530(self):
		
		# CLOSE the SR530 port before doing anything with the port
		if self.inst_list.get("SR530"):
			if self.inst_list.get("SR530").is_open():
				self.inst_list.get("SR530").close()
				self.inst_list.pop("SR530", None)
				self.sr530_status.setText("Status: device disconnected!")
				self.sr530_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_sr530.isChecked():
			self.SR530_tm = True
			self.SR530 = SR530.SR530(str(self.sr530Edit.text()), self.SR530_tm)
			self.sr530_status.setText("Testmode: CONNECTED")
			self.sr530_status.setStyleSheet("color: magenta")
			self.inst_list.update({"SR530":self.SR530})
			
		elif not self.cb_testmode.isChecked() and self.cb_sr530.isChecked():
			try:
				self.SR530_tm = False
				self.SR530 = SR530.SR530(str(self.sr530Edit.text()), self.SR530_tm)
				self.SR530.get_version()
			except Exception as e:
				reply = QMessageBox.critical(self, 'SR530 testmode', ''.join(["SR530 could not return valid echo signal. Check the port name and check the connection.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.SR530_tm = True
					self.SR530 = SR530.SR530(str(self.sr530Edit.text()), self.SR530_tm)
					self.sr530_status.setText("Testmode: CONNECTED")
					self.sr530_status.setStyleSheet("color: magenta")
					self.inst_list.update({"SR530":self.SR530})
				else:
					self.cb_sr530.setChecked(False)
			else:
				self.inst_list.update({"SR530":self.SR530})
				self.sr530_status.setText("Status: CONNECTED")
				self.sr530_status.setStyleSheet("color: green")
				
				val = self.inst_list.get("SR530").get_version()
				print(''.join(["SR530 ID:\n\t",val]))
				
				
	def ard(self):
		
		# CLOSE the Arduino port before doing anything with the port
		if self.inst_list.get("Ard"):
			if self.inst_list.get("Ard").is_open():
				self.inst_list.get("Ard").close()
				self.inst_list.pop("Ard", None)
				self.ard_status.setText("Status: device disconnected!")
				self.ard_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_ard.isChecked():
			self.Ard_tm = True
			self.Ard = ArdMega2560.ArdMega2560(str(self.ardEdit.text()), self.Ard_tm)
			self.ard_status.setText("Testmode: CONNECTED")
			self.ard_status.setStyleSheet("color: magenta")
			self.inst_list.update({"Ard":self.Ard})
			
		elif not self.cb_testmode.isChecked() and self.cb_ard.isChecked():
			try:
				self.Ard_tm = False
				self.Ard = ArdMega2560.ArdMega2560(str(self.ardEdit.text()), self.Ard_tm)
				self.Ard.get_version()
			except Exception as e:
				reply = QMessageBox.critical(self, 'Arduino testmode', ''.join(["Arduino could not return valid echo signal. Check the port name and check the connection.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.Ard_tm = True
					self.Ard = ArdMega2560.ArdMega2560(str(self.ardEdit.text()), self.Ard_tm)
					self.ard_status.setText("Testmode: CONNECTED")
					self.ard_status.setStyleSheet("color: magenta")
					self.inst_list.update({"Ard":self.Ard})
				else:
					self.cb_ard.setChecked(False)
			else:
				self.inst_list.update({"Ard":self.Ard})
				self.ard_status.setText("Status: CONNECTED")
				self.ard_status.setStyleSheet("color: green")
				
				val = self.inst_list.get("Ard").get_version()
				print(''.join(["Arduino ID:\n\t",val]))
			
			
	def cm110(self):
		
		# CLOSE the CM110 port before doing anything with the port
		if self.inst_list.get("CM110"):
			if self.inst_list.get("CM110").is_open():
				self.inst_list.get("CM110").close()
				self.inst_list.pop("CM110", None)
				self.cm110_status.setText("Status: device disconnected!")
				self.cm110_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_cm110.isChecked():
			self.CM110_tm = True
			self.CM110 = CM110.CM110(str(self.cm110Edit.text()), self.CM110_tm)
			self.cm110_status.setText("Testmode: CONNECTED")
			self.cm110_status.setStyleSheet("color: magenta")
			self.inst_list.update({"CM110":self.CM110})
			
		if not self.cb_testmode.isChecked() and self.cb_cm110.isChecked():
			try:
				self.CM110_tm = False
				self.CM110 = CM110.CM110(str(self.cm110Edit.text()), self.CM110_tm)
				self.CM110.get_version()
			except Exception as e:
				reply = QMessageBox.critical(self, 'CM110 testmode', ''.join(["CM110 could not return valid echo signal. Check the port name and check the connection to the laser.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.CM110_tm = True
					self.CM110 = CM110.CM110(str(self.cm110Edit.text()), self.CM110_tm)
					self.cm110_status.setText("Testmode: CONNECTED")
					self.cm110_status.setStyleSheet("color: magenta")
					self.inst_list.update({"CM110":self.CM110})
				else:
					self.cb_cm110.setChecked(False)
			else:
				self.inst_list.update({"CM110":self.CM110})
				self.cm110_status.setText("Status: CONNECTED")
				self.cm110_status.setStyleSheet("color: green")
				
				val = self.inst_list.get("CM110").get_version()
				print(''.join(["CM110 ID:\n\t",val]))
				
				
	def smc100(self):
		
		# CLOSE the SMC100 port before doing anything with the port
		if self.inst_list.get("SMC100"):
			if self.inst_list.get("SMC100").is_open():
				self.inst_list.get("SMC100").close()
				self.inst_list.pop("SMC100", None)
				self.smc100_status.setText("Status: device disconnected!")
				self.smc100_status.setStyleSheet("color: red")
				
		if self.cb_testmode.isChecked() and self.cb_smc100.isChecked():
			self.SMC100_tm = True
			self.SMC100 = SMC100.SMC100(str(self.smc100Edit.text()), self.SMC100_tm)
			self.smc100_status.setText("Testmode: CONNECTED")
			self.smc100_status.setStyleSheet("color: magenta")
			self.inst_list.update({"SMC100":self.SMC100})
			
		if not self.cb_testmode.isChecked() and self.cb_smc100.isChecked():
			try:
				self.SMC100_tm = False
				self.SMC100 = SMC100.SMC100(str(self.smc100Edit.text()), self.SMC100_tm)
				self.SMC100.return_ver(1)
				self.lcdst.display( str(self.SMC100.return_pos(1))[:5] )
			except Exception as e:
				reply = QMessageBox.critical(self, 'SMC100 testmode', ''.join(["SMC100 could not return valid echo signal. Check the port name and check the connection to the laser.\n\n",str(e),"\n\nProceed into the testmode?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.SMC100_tm = True
					self.SMC100 = SMC100.SMC100(str(self.smc100Edit.text()), self.SMC100_tm)
					self.smc100_status.setText("Testmode: CONNECTED")
					self.smc100_status.setStyleSheet("color: magenta")
					self.inst_list.update({"SMC100":self.SMC100})
				else:
					self.cb_smc100.setChecked(False)
			else:
				self.inst_list.update({"SMC100":self.SMC100})
				self.smc100_status.setText("Status: CONNECTED")
				self.smc100_status.setStyleSheet("color: green")
				
				val = self.inst_list.get("SMC100").return_ver(1)
				print(''.join(["SMC100 ID:\n\t",val]))
				self.lcdst.display( str(self.inst_list.get("SMC100").return_pos(1))[:5] )
				
				
	def save_(self):
		
		self.config.set("Instruments", 'testmode', str(self.cb_testmode.isChecked()) )
		self.config.set("Instruments", "cm110port", ",".join([str(self.cm110Edit.text()), str(self.cb_cm110.isChecked()) ]) )
		self.config.set("Instruments", "ardport", ",".join([str(self.ardEdit.text()), str(self.cb_ard.isChecked())]) )
		self.config.set("Instruments", "sr530port", ",".join([str(self.sr530Edit.text()), str(self.cb_sr530.isChecked())]) )
		self.config.set("Instruments", "smc100port", ",".join([str(self.smc100Edit.text()), str(self.cb_smc100.isChecked()) ]) )
		self.config.set("Instruments", 'cm110_tm', str(self.CM110_tm) )
		self.config.set("Instruments", 'ard_tm', str(self.Ard_tm) )
		self.config.set("Instruments", 'sr530_tm', str(self.SR530_tm) )
		self.config.set("Instruments", 'smc100_tm', str(self.SMC100_tm) )
		
		with open(''.join([self.cwd,os.sep,"config.ini"]), "w") as configfile:
			self.config.write(configfile)
			
		self.saveButton.setText("Settings saved")
		self.saveButton.setEnabled(False)
	
	
	def close_(self):
		
		self.close()
			
			
	def closeEvent(self,event):
			
		event.accept()
	

