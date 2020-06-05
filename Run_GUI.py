#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 10:35:01 2019

@author: Vedran Furtula
"""

import os, sys, serial, time, numpy, configparser, itertools, h5py

from PyQt5 import QtGui

import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt5.QtCore import Qt, QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView, QFileDialog, QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem, QSlider, QInputDialog, QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton, QDialog, QCheckBox)

from help_dialogs import Reset_dialog
import Instruments_dialog



class WorkerSignals(QObject):
	# Create signals to be used
	
	make_update1 = pyqtSignal(object,object,object,object,object)
	make_update2 = pyqtSignal(object,object,object,object)
	make_update3 = pyqtSignal()
	make_update4 = pyqtSignal(object)
	make_update5 = pyqtSignal(object)
	
	warning = pyqtSignal(object)
	critical = pyqtSignal(object)
	error = pyqtSignal(tuple)
	
	finished = pyqtSignal()
	
	
	
	
	
class Run_CM110_Thread(QRunnable):
	"""
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	"""
	def __init__(self,*argv):
		super(Run_CM110_Thread, self).__init__()
		
		# constants	
		self.end_flag=False
		
		self.arr_cm110 = argv[0]
		self.dwell_time = argv[1]
		self.dwell_time_ard = argv[2]
		self.avg_pts = argv[3]
		self.file_txt = argv[4]
		self.file_hdf5 = argv[5]
		self.timestr = argv[6]
		self.analogRef = argv[7]
		self.inst_list = argv[8]
		self.arr_smc100 = argv[9]
		self.cb_cm110 = argv[10]
		self.cb_smc100 = argv[11]
		self.channel = argv[12]
		
		self.signals = WorkerSignals()
		
		
	def abort(self):
		
		self.end_flag=True
		
		if self.inst_list.get("SMC100"):
			self.inst_list.get("SMC100").abort()
			time.sleep(0.2)
			step_pos = self.inst_list.get("SMC100").return_pos(1)
			self.signals.make_update4.emit(step_pos)
			
			
	@pyqtSlot()
	def run(self):
		
		try:
			self.scan()
		except Exception as e:
			self.signals.warning.emit(str(e))
		else:
			pass
		finally:
			self.signals.finished.emit()  # Done
		
		
	def scan(self):
		
		if not self.cb_cm110.isChecked() and not self.cb_smc100.isChecked():
			'''
			dt = h5py.string_dtype(encoding="utf-8")
			dt_ = h5py.vlen_dtype(numpy.dtype("float"))
			'''
			# Create header for new inputs
			with h5py.File(self.file_hdf5, 'w') as f:
				f.create_dataset("set_wl", (0,), maxshape=(None,) )
				f.create_dataset("real_wl", (0,), maxshape=(None,) )
				f.create_dataset("volt", (0,), maxshape=(None,) )
				f.create_dataset("ard_bit", (0,), maxshape=(None,) )
				f.create_dataset("stepper_pos", (0,), maxshape=(None,) )
				f.create_dataset("timetrace", (0,), maxshape=(None,) )
				
				f.create_dataset("set_wl_endpts", (0,), maxshape=(None,) )
				f.create_dataset("real_wl_endpts", (0,), maxshape=(None,) )
				f.create_dataset("volt_endpts", (0,), maxshape=(None,) )
				f.create_dataset("ard_bit_endpts", (0,), maxshape=(None,) )
				f.create_dataset("stepper_pos_endpts", (0,), maxshape=(None,) )
				f.create_dataset("timetrace_endpts", (0,), maxshape=(None,) )
			
			#make a heading for the datafile with only last Arduino output for each wavelength
			
			with open(self.file_txt, 'w') as thefile:
				thefile.write(''.join([ "SET wavel[nm], REAL wavel[nm], Voltage[V], Ard raw data[0..1023 steps], STEPPER pos, Timetrace [sec]\n"]))
			
		###########################################
		
		if self.inst_list.get("SMC100") and not self.cb_cm110.isChecked():
			step_pos = self.inst_list.get("SMC100").return_pos(1)
			self.signals.make_update4.emit(step_pos)
			
		if self.inst_list.get("SR530"):
			self.inst_list.get("SR530").set_remote()
			
		if self.inst_list.get("CM110") and not self.cb_smc100.isChecked():
			if not self.inst_list.get("CM110").get_units()=="nm":
				self.inst_list.get("CM110").set_nm()
				
			print("The current monochromator position is:")
			
		###########################################
		
		time_start=time.time()
		
		for step_pos in self.arr_smc100:
			
			if self.end_flag:
				return
			
			if self.inst_list.get("SMC100") and not self.cb_cm110.isChecked():
				step_pos = round(step_pos,3)
				step_pos = self.inst_list.get("SMC100").move_abspos(1,step_pos)
				self.signals.make_update4.emit(step_pos)
				self.signals.make_update3.emit()
			else:
				step_pos = -1
			
			if self.cb_smc100.isChecked():
				return
			
			# go to the START position
			if self.inst_list.get("CM110") and not self.cb_smc100.isChecked():
				self.inst_list.get("CM110").set_goto(self.arr_cm110[0])
				
			if self.cb_cm110.isChecked():
				self.signals.make_update5.emit(self.arr_cm110[0])
				return
			
			# define STEPSIZE
			if self.inst_list.get("CM110"):
				if len(self.arr_cm110)>1:
					step = int(abs(self.arr_cm110[0]-self.arr_cm110[1]))
					self.inst_list.get("CM110").set_stepsize(step)
			
			for set_position in self.arr_cm110:
				# DO NOT step the monochromator first time you enter then while loop
				if self.inst_list.get("CM110"):
					real_position = self.inst_list.get("CM110").get_position()
					set_position = set_position
				else:
					real_position = -1
					set_position = -1
				
				if self.inst_list.get("CM110"):
					print(''.join(["SET, REAL: ",str(set_position), ", ", str(real_position), " nm at STEPPER pos: ", str(step_pos)]))
					self.signals.make_update5.emit(set_position)
				
				time_s = time.time()
				while (time.time()-time_s)<self.dwell_time:
					if self.end_flag:
						return
					time_ard_start=time.time()
					# wait until self.dwell_time_ard, then go back and get a new value
					while (time.time()-time_ard_start)<self.dwell_time_ard/1000:
						if self.end_flag:
							return
					# Send averaging points to the Arduino serial by
					if self.inst_list.get("SR530"):
						bit_step = -1
						Vout = self.inst_list.get("SR530").return_voltage(self.channel)
					elif self.inst_list.get("Ard"):
						bit_step = self.inst_list.get("Ard").get_val(int(self.avg_pts))
						Vout = self.analogRef*bit_step/1023
					else:
						bit_step = -1
						Vout = -1
					
					time_elap=time_ard_start-time_start
					
					# Write data to HDF5
					with h5py.File(self.file_hdf5, 'a') as f:
						#print("hdf5, set_position:", type(set_position))
						dset = f["set_wl"]
						dset.resize((dset.size+1,))
						dset[-1] = set_position
						
						#print("hdf5, real_position:", type(real_position))
						dset = f["real_wl"]
						dset.resize((dset.size+1,))
						dset[-1] = real_position
						
						#print("hdf5, Vout:", type(Vout))
						dset = f["volt"]
						dset.resize((dset.size+1,))
						dset[-1] = Vout
						
						#print("hdf5, bit_step:", type(bit_step))
						dset = f["ard_bit"]
						dset.resize((dset.size+1,))
						dset[-1] = bit_step
						
						#print("hdf5, step_pos:", type(step_pos))
						dset = f["stepper_pos"]
						dset.resize((dset.size+1,))
						dset[-1] = step_pos
						
						#print("hdf5, time_elap:", type(time_elap))
						dset = f["timetrace"]
						dset.resize((dset.size+1,))
						dset[-1] = time_elap
					
					self.signals.make_update2.emit(set_position,real_position,Vout,time_elap)
					
					if self.cb_cm110.isChecked() or self.cb_smc100.isChecked():
						return
					
				# Save stepped wavelengths and voltage data in a textfile
				with open(self.file_txt, 'a') as thefile:
					thefile.write("%s " % set_position)
					thefile.write("\t%s " % real_position)
					thefile.write("\t%s" % format(Vout, "010.8f"))
					thefile.write("\t%s" % bit_step)
					thefile.write("\t%s" % step_pos)
					thefile.write("\t%s\n" % format(time_elap, "010.4f"))
				
				# Write data to HDF5
				with h5py.File(self.file_hdf5, 'a') as f:
					#print("hdf5, set_position:", type(set_position))
					dset = f["set_wl_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = set_position
					
					#print("hdf5, real_position:", type(real_position))
					dset = f["real_wl_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = real_position
					
					#print("hdf5, Vout:", type(Vout))
					dset = f["volt_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = Vout
					
					#print("hdf5, bit_step:", type(bit_step))
					dset = f["ard_bit_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = bit_step
					
					#print("hdf5, step_pos:", type(step_pos))
					dset = f["stepper_pos_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = step_pos
					
					#print("hdf5, time_elap:", type(time_elap))
					dset = f["timetrace_endpts"]
					dset.resize((dset.size+1,))
					dset[-1] = time_elap
				
				self.signals.make_update1.emit(set_position,real_position,Vout,time_elap,bit_step)
				
				# Do STEP
				if self.inst_list.get("CM110"):
					if set_position == self.arr_cm110[-1]:
						pass
					else:
						self.inst_list.get("CM110").make_step()
							
							
							
							
							

		
		
		
		
		
		
		
		
		
		
class Run_CM110(QMainWindow):
	
	def __init__(self):
		super().__init__()
		
		self.cwd = os.getcwd()
		self.load_()
		
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
		
		
	def initUI(self):
		
		################### MENU BARS START ##################
		
		MyBar = QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.save_) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		instMenu = MyBar.addMenu("Instruments")
		self.conMode = instMenu.addAction("Load instruments")
		self.conMode.triggered.connect(self.instrumentsDialog)
		
		################### MENU BARS END ##################
		
		#####################################################
		lbl1 = QLabel("MONOCHROMATOR CM110 settings:", self)
		lbl1.setStyleSheet("color: blue")
		
		start_lbl = QLabel("Start[nm]",self)
		stop_lbl = QLabel("Stop[nm]",self)
		step_lbl = QLabel("Step[nm]",self)
		lcd_cm100_lbl = QLabel("",self)
		
		self.startEdit = QLineEdit(self.start_cm110,self)
		self.stopEdit = QLineEdit(self.stop_cm110,self)
		self.stepEdit = QLineEdit(self.step_cm110,self)
		
		self.lcd_cm100 = QLCDNumber(self)
		self.lcd_cm100.setStyleSheet("color: blue")
		#self.lcdst.setFixedHeight(40)
		self.lcd_cm100.setSegmentStyle(QLCDNumber.Flat)
		self.lcd_cm100.setNumDigits(5)
		self.lcd_cm100.display("-----")
		
		self.cb_cm110 = QCheckBox("Move monochromator CM110 to a point",self)
		self.cb_cm110.toggle()
		self.cb_cm110.setChecked(False)
		
		#####################################################
		
		lbl3 = QLabel("NEWPORT stepper SMC100:", self)
		lbl3.setStyleSheet("color: blue")
		startst_lbl = QLabel("Start",self)
		stopst_lbl = QLabel("Stop",self)
		stepst_lbl = QLabel("Step",self)
		lcdst_lbl = QLabel("",self)
		
		self.startst_Edit = QLineEdit(self.startst,self) 
		self.stopst_Edit = QLineEdit(self.stopst,self) 
		self.stepst_Edit = QLineEdit(self.stepst,self)
		
		self.lcdst = QLCDNumber(self)
		self.lcdst.setStyleSheet("color: blue")
		#self.lcdst.setFixedHeight(40)
		self.lcdst.setSegmentStyle(QLCDNumber.Flat)
		self.lcdst.setNumDigits(5)
		self.lcdst.display("-----")
		
		self.cb_smc100 = QCheckBox("Move the SMC100 stepper to a point",self)
		self.cb_smc100.toggle()
		self.cb_smc100.setChecked(False)
		
		#####################################################
		
		dwelltime = QLabel("DWELL time for scans [s]:",self)
		dwelltime.setStyleSheet("color: blue")
		
		self.dwelltimeEdit = QLineEdit(str(self.dwell_time),self) 
		
		#####################################################
		
		lbl7 = QLabel("LOCK-IN SR530 settings:", self)
		lbl7.setStyleSheet("color: blue")
		
		channel_lbl = QLabel("Channel", self)
		self.combo4 = QComboBox(self)
		mylist=["1","2","X","Y"]
		self.combo4.addItems(mylist)
		self.combo4.setCurrentIndex(mylist.index(self.channel))
		
		#####################################################
		
		lbl2 = QLabel("ARDUINO Mega2560 settings:", self)
		lbl2.setStyleSheet("color: blue")
		dwelltime_lbl = QLabel("Dwell time [ms]",self)
		self.dwelltimeEdit_ard = QLineEdit(str(self.dwell_time_ard),self)
		
		avgpts_lbl = QLabel("Averaging points", self)
		self.combo1 = QComboBox(self)
		mylist=["1","5","10","50","100","200"]
		self.combo1.addItems(mylist)
		self.combo1.setCurrentIndex(mylist.index(str(self.avg_pts)))
		
		#####################################################
		
		lbl4 = QLabel("STORAGE filename and location settings:", self)
		lbl4.setStyleSheet("color: blue")
		filename = QLabel("folder/file",self)
		self.filenameEdit = QLineEdit(self.filename_str,self)
		
		#####################################################
		
		lbl6 = QLabel("PLOT options:", self)
		lbl6.setStyleSheet("color: blue")
		mylist2=["200","400","800","1600","3200","6400"]
		
		schroll_lbl = QLabel("Schroll time after",self)
		self.combo2 = QComboBox(self)
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.schroll_time)))
		
		schroll2_lbl = QLabel("Schroll wavelength after",self)
		self.combo3 = QComboBox(self)
		self.combo3.addItems(mylist2)
		self.combo3.setCurrentIndex(mylist2.index(str(self.schroll_wl)))
		
		##############################################
		
		lbl5 = QLabel("Scan or move:", self)
		lbl5.setStyleSheet("color: blue")
		
		#save_str = QLabel("Store settings", self)
		#self.saveButton = QPushButton("Save",self)
		#self.saveButton.setEnabled(True)
		
		run_str = QLabel("Record lock-in data", self)
		self.runButton = QPushButton("Load instruments",self)
		
		#saveplots_str = QLabel("Save plots as png", self)
		#self.saveplotsButton = QPushButton("Save plots",self)
		#self.saveplotsButton.setEnabled(True)
		'''
		elapsedtime_str = QLabel('Show voltage vs. time', self)
		self.elapsedtimeButton = QPushButton("Plot 2",self)
		self.elapsedtimeButton.setEnabled(False)
		'''
		cancel_str = QLabel("Stop current run", self)
		self.stopButton = QPushButton("STOP",self)
		self.stopButton.setEnabled(False)
		
		##############################################
		
		# status info which button has been pressed
		#self.status_str = QLabel("Edit settings and press SAVE!", self)
		#self.status_str.setStyleSheet("color: green")
		
		##############################################
		
		# status info which button has been pressed
		self.elapsedtime_str = QLabel("TIME trace for storing plots and data:", self)
		self.elapsedtime_str.setStyleSheet("color: blue")
		
		##############################################
		
		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.timestr)
			
		##############################################
		# Add all widgets		
		g1_0 = QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)
		g1_1 = QGridLayout()
		#g1_1.addWidget(cm110port,0,0)
		#g1_1.addWidget(self.cm110portEdit,0,1)
		
		g1_2 = QGridLayout()
		g1_2.addWidget(start_lbl,0,0)
		g1_2.addWidget(stop_lbl,0,1)
		g1_2.addWidget(step_lbl,0,2)
		g1_2.addWidget(lcd_cm100_lbl,0,3)
		g1_2.addWidget(self.startEdit,1,0)
		g1_2.addWidget(self.stopEdit,1,1)
		g1_2.addWidget(self.stepEdit,1,2)
		g1_2.addWidget(self.lcd_cm100,1,3)
		v1 = QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_1)
		v1.addLayout(g1_2)
		v1.addWidget(self.cb_cm110)
		
		g0_0 = QGridLayout()
		g0_0.addWidget(dwelltime,0,0)
		g0_0.addWidget(self.dwelltimeEdit,0,1)
		
		g9_0 = QGridLayout()
		g9_0.addWidget(lbl3,0,0)
		g9_1 = QGridLayout()
		g9_1.addWidget(startst_lbl,0,0)
		g9_1.addWidget(stopst_lbl,0,1)
		g9_1.addWidget(stepst_lbl,0,2)
		g9_1.addWidget(lcdst_lbl,0,3)
		g9_1.addWidget(self.startst_Edit,1,0)
		g9_1.addWidget(self.stopst_Edit,1,1)
		g9_1.addWidget(self.stepst_Edit,1,2)
		g9_1.addWidget(self.lcdst,1,3)
		v9 = QVBoxLayout()
		v9.addLayout(g9_0)
		v9.addLayout(g9_1)
		v9.addWidget(self.cb_smc100)
		
		g3_0 = QGridLayout()
		g3_0.addWidget(lbl7,0,0)
		g3_1 = QGridLayout()
		g3_1.addWidget(channel_lbl,0,0)
		g3_1.addWidget(self.combo4,0,1)
		v3 = QVBoxLayout()
		v3.addLayout(g3_0)
		v3.addLayout(g3_1)
		
		g2_0 = QGridLayout()
		g2_0.addWidget(lbl2,0,0)
		g2_1 = QGridLayout()
		g2_1.addWidget(dwelltime_lbl,0,0)
		g2_1.addWidget(avgpts_lbl,1,0)
		g2_1.addWidget(self.dwelltimeEdit_ard,0,1)
		g2_1.addWidget(self.combo1,1,1)
		v2 = QVBoxLayout()
		v2.addLayout(g2_0)
		v2.addLayout(g2_1)
		
		g4_0 = QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QGridLayout()
		g4_1.addWidget(filename,0,0)
		g4_1.addWidget(self.filenameEdit,0,1)
		v4 = QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
				
		g7_0 = QGridLayout()
		g7_0.addWidget(lbl6,0,0)
		g7_1 = QGridLayout()
		g7_1.addWidget(schroll2_lbl,0,0)
		g7_1.addWidget(self.combo3,0,1)
		g7_1.addWidget(schroll_lbl,1,0)
		g7_1.addWidget(self.combo2,1,1)
		v7 = QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
		g5_0 = QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		g5_1 = QGridLayout()
		#g5_1.addWidget(save_str,0,0)
		g5_1.addWidget(run_str,0,0)
		#g5_1.addWidget(saveplots_str,2,0)
		g5_1.addWidget(cancel_str,1,0)
		#g5_1.addWidget(self.saveButton,0,1)
		g5_1.addWidget(self.runButton,0,1)
		#g5_1.addWidget(self.saveplotsButton,2,1)
		g5_1.addWidget(self.stopButton,1,1)
		v5 = QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		g6_0 = QGridLayout()
		g6_0.addWidget(self.elapsedtime_str,0,0)
		g6_0.addWidget(self.lcd,1,0)
		v6 = QVBoxLayout()
		v6.addLayout(g6_0)
		
		# add all groups from v1 to v6 in one vertical group v7
		v8 = QVBoxLayout()
		v8.addLayout(v1)
		v8.addLayout(v9)
		v8.addLayout(g0_0)
		v8.addLayout(v2)
		v8.addLayout(v3)
		v8.addLayout(v4)
		v8.addLayout(v7)
		v8.addLayout(v5)
		v8.addLayout(v6)
	
		# set graph  and toolbar to a new vertical group vcan
		vcan = QVBoxLayout()
		self.pw1 = pg.PlotWidget(name="Plot1")  ## giving the plots names allows us to link their axes together
		vcan.addWidget(self.pw1)
		self.pw2 = pg.PlotWidget(name="Plot2")
		vcan.addWidget(self.pw2)

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addLayout(vcan,3.75)
		
    ##############################################
    # PLOT 1 settings
		# create plot and add it to the figure canvas		
		self.p0 = self.pw1.plotItem
		self.curve1=[self.p0.plot()]
		# create plot and add it to the figure
		self.p0vb = pg.ViewBox()
		self.curve5=pg.PlotCurveItem(pen=None)
		self.p0vb.addItem(self.curve5)
		# connect respective axes to the plot 
		self.p0.showAxis('right')
		self.p0.getAxis('right').setLabel("10-bit Arduino output")
		self.p0.scene().addItem(self.p0vb)
		self.p0.getAxis('right').linkToView(self.p0vb)
		self.p0vb.setXLink(self.p0)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw2.plotItem
		self.curve2=self.p1.plot(pen='r')
		self.curve3=self.p1.plot()
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve4=pg.PlotCurveItem(pen='y')
		self.curve6=pg.PlotCurveItem(pen='m')
		self.p2.addItem(self.curve4)
		self.p2.addItem(self.curve6)
		# connect respective axes to the plot 
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Wavelength", units='m', color='yellow')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw2.setDownsampling(mode='peak')
		self.pw2.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		###############################################################################
		
		self.inst_list = {}
		self.colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
		
		self.threadpool = QThreadPool()
		print("Multithreading in Run_COMPexPRO with maximum %d threads" % self.threadpool.maxThreadCount())
		
		# reacts to choises picked in the menu
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		self.combo4.activated[str].connect(self.onActivated4)
		self.cb_cm110.stateChanged.connect(self.cm110_stch)
		self.cb_smc100.stateChanged.connect(self.smc100_stch)
		
		# save all paramter data in the config file
		#self.saveButton.clicked.connect(self.save_)
		#self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# cancel the script run
		self.stopButton.clicked.connect(self.set_stop)
		
		self.allFields(False)
		
		##############################################
		
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.set_disconnect)
		self.timer.setSingleShot(True)
		
		##############################################
		
		self.setGeometry(100, 100, 1100, 650)
		self.setWindowTitle("Monochromator CM110 Control And Data Acqusition")
		
		w = QWidget()
		w.setLayout(hbox)
		self.setCentralWidget(w)
		self.show()
		
		
	def instrumentsDialog(self):
		
		self.Inst = Instruments_dialog.Instruments_dialog(self,self.inst_list,self.cwd,self.lcdst)
		self.Inst.exec()
		
		if self.inst_list.get("CM110") or self.inst_list.get("Ard") or self.inst_list.get("SR530") or self.inst_list.get("SMC100"):
			self.allFields(True)
			self.runButton.setText("Scan")
			self.timer.start(1000*60*self.minutes)
		else:
			self.allFields(False)
			self.runButton.setText("Load instruments!")
			
			
	def allFields(self,trueorfalse):
		
		self.startEdit.setEnabled(trueorfalse)
		self.stopEdit.setEnabled(trueorfalse)
		self.stepEdit.setEnabled(trueorfalse)
		
		self.startst_Edit.setEnabled(trueorfalse)
		self.stopst_Edit.setEnabled(trueorfalse)
		self.stepst_Edit.setEnabled(trueorfalse)
		
		self.dwelltimeEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit_ard.setEnabled(trueorfalse)
		
		self.combo1.setEnabled(trueorfalse)
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		self.cb_cm110.setEnabled(trueorfalse)
		self.cb_smc100.setEnabled(trueorfalse)
		
		##############################################################
		
		if not self.inst_list.get("Ard"):
			self.dwelltimeEdit_ard.setEnabled(False)
			self.combo1.setEnabled(False)
		
		if not self.inst_list.get("SMC100"):
			self.cb_smc100.setEnabled(False)
			self.startst_Edit.setEnabled(False)
			self.stopst_Edit.setEnabled(False)
			self.stepst_Edit.setEnabled(False)
			self.lcdst.display("-----")
			
		if not self.inst_list.get("CM110"):
			self.combo3.setEnabled(False)
			self.cb_cm110.setEnabled(False)
			self.startEdit.setEnabled(False)
			self.stopEdit.setEnabled(False)
			self.stepEdit.setEnabled(False)
		
		if not self.inst_list.get("CM110") and not self.inst_list.get("SMC100"):
			self.dwelltimeEdit.setEnabled(False)
			
		if not self.inst_list.get("SR530"):
			self.combo4.setEnabled(False)
			
		##############################################################
		
		self.filenameEdit.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
		
		
	def cm110_stch(self, state):
		
		if state in [Qt.Checked,True]:
			self.allFields(False)
			self.cb_cm110.setEnabled(True)
			self.startEdit.setEnabled(True)
			self.runButton.setText("Move")
			self.runButton.setEnabled(True)
		else:
			self.allFields(True)
			self.runButton.setText("Scan")
			
			
	def smc100_stch(self, state):
		
		if state in [Qt.Checked,True]:
			self.allFields(False)
			self.cb_smc100.setEnabled(True)
			self.startst_Edit.setEnabled(True)
			self.runButton.setText("Move")
			self.runButton.setEnabled(True)
		else:
			self.allFields(True)
			self.runButton.setText("Scan")
			
			
	def onActivated1(self, text):
		
		self.avg_pts = str(text)
		
		
	def onActivated2(self, text):
		
		self.schroll_time = int(text)
		
		
	def onActivated3(self, text):
		
		self.schroll_wl = int(text)
		
		
	def onActivated4(self, text):
		
		self.channel = str(text)
		
		
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
	
	
	def create_file(self, mystr):
		
		head, ext = os.path.splitext(mystr)
		#print("head: ",head)
		#print("ext: ",ext)
		#print("filename: ",self.filenameEdit.text())
		
		totalpath = ''.join([self.cwd,os.sep,head,'_',self.timestr,ext])
		my_dir = os.path.dirname(totalpath)
		
		if not os.path.isdir(my_dir):
			QMessageBox.warning(self, "Message","".join(["Folder(s) named ",my_dir," will be created!"]))
			
		try:
			os.makedirs(my_dir, exist_ok=True)
		except Exception as e:
			QMessageBox.critical(self, "Message","".join(["Folder named ",head," not valid!\n\n",str(e)]))
			return ""
		
		return totalpath
	
	
	def set_run(self):
		
		# MINIMUM REQUIREMENTS for proper run
		if not self.inst_list.get("CM110") and not self.inst_list.get("SR530") and not self.inst_list.get("Ard") and not self.inst_list.get("SMC100"):
			QMessageBox.critical(self, 'Message',"No instruments connected. At least 1 instrument is required.")
			return
			
		########################################################
		
		if self.inst_list.get("SMC100"):
			val = self.inst_list.get("SMC100").return_ts(1)
			if val[-2:] not in ["32","33","34","35"]:
				# RESET the stepper if active
				self.Reset_dialog = Reset_dialog.Reset_dialog(self, self.inst_list)
				self.Reset_dialog.exec()
				# Checkif the stepper is ready
				val = self.inst_list.get("SMC100").return_ts(1)
				if val[-2:] not in ["32","33","34","35"]:
					return
				
		########################################################
		
		if self.inst_list.get("CM110"):
			if self.startEdit.text() and not self.stopEdit.text() and not self.stepEdit.text():
				try:
					self.arr_cm110 = numpy.arange(int(self.startEdit.text()),int(self.startEdit.text())+1,1)
				except Exception as e:
					QMessageBox.warning(self, 'Message',''.join(["The wavelength parameter should be an integer and non-zero!\n\n",str(e)]))
					return
				
			elif self.startEdit.text() and self.stopEdit.text() and self.stepEdit.text():
				try:
					self.arr_cm110 = numpy.arange(int(self.startEdit.text()),int(self.stopEdit.text())+int(self.stepEdit.text()),int(self.stepEdit.text()))
				except Exception as e:
					QMessageBox.warning(self, 'Message',''.join(["All wavelength scan parameters should be integers and non-zero!\n\n",str(e)]))
					return
				
			else:
				QMessageBox.warning(self, 'Message',''.join(["Fill in the fields as [start, stop, step] or [start].\nAll three fields empty are not allowed or otherwise disconnect the instrument."]))
				return
		
		else:
			self.arr_cm110 = numpy.array([-1])
				
		########################################################
		
		staEd = int(1000*float(self.startst_Edit.text()))
		stoEd = int(1000*float(self.stopst_Edit.text()))
		steEd = int(1000*float(self.stepst_Edit.text()))
		
		if self.inst_list.get("SMC100"):
			if self.startst_Edit.text() and not self.stopst_Edit.text() and not self.stepst_Edit.text():
				try:
					self.arr_smc100 = numpy.arange(staEd,staEd+1,1)
				except Exception as e:
					QMessageBox.warning(self, 'Message',''.join(["The Newport parameter should be a real number and non-zero!\n\n",str(e)]))
					return
				
			elif self.startst_Edit.text() and self.stopst_Edit.text() and self.stepst_Edit.text():
				try:
					self.arr_smc100 = numpy.arange(staEd,stoEd+steEd,steEd)
				except Exception as e:
					QMessageBox.warning(self, 'Message',''.join(["All Newport scan parameters should be real numbers and non-zero!\n\n",str(e)]))
					return
				
			else:
				QMessageBox.warning(self, 'Message',''.join(["Fill in the fields as [start, stop, step] or [start].\nAll three fields empty are not allowed or otherwise disconnect the instrument."]))
				return
		
		else:
			self.arr_smc100 = numpy.array([-1])
			
		########################################################
		
		if not self.is_number(self.dwelltimeEdit.text()):
			QMessageBox.warning(self, 'Message',"Dwell time scan parameter is not a real number!")
			return
		
		########################################################
		
		# For SAVING data
		if "\\" in self.filenameEdit.text():
			self.filenameEdit.setText(self.filenameEdit.text().replace("\\",os.sep))
			
		if "/" in self.filenameEdit.text():
			self.filenameEdit.setText(self.filenameEdit.text().replace("/",os.sep))
			
		if not self.filenameEdit.text():
			self.filenameEdit.setText(''.join(["data",os.sep,"data"]))
		
		if not os.sep in self.filenameEdit.text():
			self.filenameEdit.setText(''.join(["data", os.sep, self.filenameEdit.text()]))
		
		'''
		# Initial read of the config file		
		start_sc = int(self.startEdit.text())
		stop_sc = int(self.stopEdit.text())
		step_sc = int(self.stepEdit.text())
		start_st = float(self.startst_Edit.text())
		stop_st = float(self.stopst_Edit.text())
		step_st = float(self.stepst_Edit.text())
		dwelltime = [float(self.dwelltimeEdit[ii].text()) for ii in range(self.numofintervals)]
		dwell_ard = float(self.dwelltimeEdit_ard.text())
		file_txt = self.create_file(''.join([self.filenameEdit.text(),".txt"]))
		file_hdf5 = self.create_file(''.join([self.filenameEdit.text(),".hdf5"]))
		
		for start,stop,step,dwell in zip(start_sc,stop_sc,step_sc,dwelltime):
			
			if start<0 or start>9000:
				QMessageBox.warning(self, 'Message',"Minimum start wavelength is 0 nm and maximum 9000 nm!")
				return
			
			if stop<0 or stop>9000:
				QMessageBox.warning(self, 'Message',"Minimum stop wavelength is 0 nm and maximum 9000 nm!")
				return
			
			if step<0 or step>127:
				QMessageBox.warning(self, 'Message',"Minimum step is 0 units and maximum 127 units!")
				return
			
			if dwell<3*dwell_ard/1000 or dwell>100:
				QMessageBox.warning(self, 'Message',"Monochromator dwell time is minimum 3 times Arduino dwell time and maximum 100 s!")
				return
			
			if dwell_ard<10 or dwell_ard>dwell*1000:
				QMessageBox.warning(self, 'Message',"Arduino dwell time is minimum 10 ms and maximum CM110 dwell time!")
				return
		'''
		
		dwelltime = float(self.dwelltimeEdit.text())
		dwell_ard = float(self.dwelltimeEdit_ard.text())
		file_txt = self.create_file(''.join([self.filenameEdit.text(),".txt"]))
		file_hdf5 = self.create_file(''.join([self.filenameEdit.text(),".hdf5"]))
		
		if len(self.arr_cm110)==0:
			QMessageBox.critical(self, 'Message',"The length of the CM110 wavelength array is zero. Check your start, stop and step values!")
			return
		
		if len(self.arr_smc100)==0:
			QMessageBox.critical(self, 'Message',"The length of the SMC100 stepper positions array is zero. Check your start, stop and step values!")
			return
		
		if self.inst_list.get("CM110"):
			if self.arr_cm110[0]<0 or self.arr_cm110[0]>9000:
				QMessageBox.warning(self, 'Message',"Minimum start wavelength is 0 nm and maximum 9000 nm!")
				return
			
			if self.arr_cm110[-1]<0 or self.arr_cm110[-1]>9000:
				QMessageBox.warning(self, 'Message',"Minimum stop wavelength is 0 nm and maximum 9000 nm!")
				return
			
			if len(self.arr_cm110)>1: 
				if int(abs(self.arr_cm110[0]-self.arr_cm110[1]))<1 or int(abs(self.arr_cm110[0]-self.arr_cm110[1]))>127:
					QMessageBox.warning(self, 'Message',"Minimum step wavelength is 0.1 nm and maximum 127 nm!")
					return
				
			if dwelltime<3*dwell_ard/1000 or dwelltime>100:
				QMessageBox.warning(self, 'Message',"Monochromator dwell time is minimum 3 times Arduino dwell time and maximum 100 s!")
				return
			
			if dwell_ard<10 or dwell_ard>dwelltime*1000:
				QMessageBox.warning(self, 'Message',"Arduino dwell time is minimum 10 ms and maximum CM110 dwell time!")
				return
		
		self.clear_vars_graphs()
		
		self.allFields(False)
		self.conMode.setEnabled(False)
		self.runButton.setEnabled(False)
		self.stopButton.setEnabled(True)
		self.stopButton.setText("STOP")
		if self.cb_cm110.isChecked() or self.cb_smc100.isChecked():
			self.runButton.setText("Moving...")
		else:
			self.runButton.setText("Scanning...")
		
		self.timer.stop()
		
		self.get_thread=Run_CM110_Thread(self.arr_cm110,dwelltime,dwell_ard,self.avg_pts,file_txt,file_hdf5,self.timestr,self.analogref,self.inst_list,self.arr_smc100/1000,self.cb_cm110,self.cb_smc100,self.channel)
		
		self.get_thread.signals.make_update1.connect(self.make_update1)
		self.get_thread.signals.make_update2.connect(self.make_update2)
		self.get_thread.signals.make_update3.connect(self.make_update3)
		self.get_thread.signals.make_update4.connect(self.make_update4)
		self.get_thread.signals.make_update5.connect(self.make_update5)
		self.get_thread.signals.finished.connect(self.finished)
		# Execute
		self.threadpool.start(self.get_thread)
		
		
	def make_update1(self,set_position,real_positions,endpoint_data,endpoints_times,raw_data):
		
		self.set_wl.extend([ 1e-9*set_position ])
		self.real_wl.extend([ 1e-9*real_positions ])
		self.all_volts.extend([ endpoint_data  ])	
		self.all_times.extend([ endpoints_times ])
		self.all_raw.extend([ raw_data ])
		
		if len(self.set_wl)>self.schroll_wl:
			self.plot_volts[:-1] = self.plot_volts[1:]  # shift data in the array one sample left
			self.plot_volts[-1] = endpoint_data
			self.plot_wl[:-1] = self.plot_wl[1:]  # shift data in the array one sample left
			self.plot_wl[-1] = 1e-9*set_position
			self.plot_set_wl[:-1] = self.plot_set_wl[1:]  # shift data in the array one sample left
			self.plot_set_wl[-1] = 1e-9*set_position
			self.plot_real_wl[:-1] = self.plot_real_wl[1:]  # shift data in the array one sample left
			self.plot_real_wl[-1] = 1e-9*real_positions
			self.plot_raw[:-1] = self.plot_raw[1:]  # shift data in the array one sample left
			self.plot_raw[-1] = raw_data
		else:
			self.plot_volts.extend([ float(endpoint_data)  ])
			self.plot_wl.extend([ 1e-9*set_position ])
			self.plot_set_wl.extend([ 1e-9*set_position ])
			self.plot_real_wl.extend([ 1e-9*real_positions ])
			self.plot_raw.extend([ int(raw_data)  ])
		
		self.curve1[-1].setData(self.plot_wl, self.plot_volts)
		self.curve5.setData(self.plot_set_wl, self.plot_raw)
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0vb.setGeometry(self.p0.vb.sceneBoundingRect())
			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0vb.linkedViewChanged(self.p0.vb, self.p0vb.XAxis)
		updateViews()
		self.p0.vb.sigResized.connect(updateViews)
		
		###########################################################
		# Update curve3 in different plot
		if len(self.set_wl_tr)>=self.schroll_time:
			local_times=self.all_times[-self.counter:]
			local_volts=self.all_volts[-self.counter:]
			self.curve3.setData(local_times, local_volts)
		else:
			self.curve3.setData(self.all_times, self.all_volts)
		
		
	def make_update2(self,set_position,real_positions,all_data,timelist):
		
		self.set_wl_tr.extend([ 1e-9*set_position ])
		self.real_wl_tr.extend([ 1e-9*real_positions ])
		#self.all_volts_tr.extend([ float(all_data) ])
		#self.all_time_tr.extend([ float(timelist) ])
				
		if len(self.set_wl_tr)==self.schroll_time:
			self.counter=len(self.set_wl)

		if len(self.set_wl_tr)>self.schroll_time:
			self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			self.plot_time_tr[-1] = timelist
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = all_data
			self.plot_set_wl_tr[:-1] = self.plot_set_wl_tr[1:]  # shift data in the array one sample left
			self.plot_set_wl_tr[-1] = 1e-9*set_position
			self.plot_real_wl_tr[:-1] = self.plot_real_wl_tr[1:]  # shift data in the array one sample left
			self.plot_real_wl_tr[-1] = 1e-9*real_positions
		else:
			self.plot_set_wl_tr.extend([ 1e-9*set_position ])
			self.plot_real_wl_tr.extend([ 1e-9*real_positions ])
			self.plot_volts_tr.extend([ all_data ])
			self.plot_time_tr.extend([ timelist ])

		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve4.setData(self.plot_time_tr, self.plot_set_wl_tr)
		self.curve6.setData(self.plot_time_tr, self.plot_real_wl_tr)
		
		
	def make_update3(self):
		
		self.plot_wl = []
		self.plot_volts = []
		
		mycol=next(self.colors)
		self.curve1.extend( [self.p0.plot(pen=pg.mkPen(mycol,width=1), symbolPen=mycol, symbolBrush=mycol, symbolSize=3)] )
		
		
	def make_update4(self,val):
		
		self.lcdst.display(str(val)[:5])
		
		
	def make_update5(self,val):
		
		self.lcd_cm100.display(str(val))
		
		
	def set_disconnect(self):
		
		##########################################
		
		if self.inst_list.get("CM110"):
			if self.inst_list.get("CM110").is_open():
				self.inst_list.get("CM110").close()
			self.inst_list.pop("CM110", None)
				
		##########################################
		
		if self.inst_list.get("Ard"):
			if self.inst_list.get("Ard").is_open():
				self.inst_list.get("Ard").close()
			self.inst_list.pop("Ard", None)
			
		##########################################
		
		if self.inst_list.get("SR530"):
			if self.inst_list.get("SR530").is_open():
				self.inst_list.get("SR530").close()
			self.inst_list.pop("SR530", None)
			
		##########################################
		
		if self.inst_list.get("SMC100"):
			if self.inst_list.get("SMC100").is_open():
				self.inst_list.get("SMC100").close()
			self.inst_list.pop("SMC100", None)
			
		##########################################
		
		print("All com ports DISCONNECTED")
		
		self.allFields(False)
		self.conMode.setEnabled(True)
		self.runButton.setText("Load instrument!")
		self.runButton.setEnabled(False)
		
		
	def set_stop(self):
		
		self.stopButton.setEnabled(False)
		self.stopButton.setText("Stopped")
		
		if hasattr(self, "get_thread"):
			self.get_thread.abort()
			
		self.stop_pressed = True
		
		
	def clear_vars_graphs(self):
		
		# PLOT 1 initial canvas settings
		self.set_wl=[]
		self.real_wl=[]
		self.all_volts=[]
		self.all_times=[]
		self.all_raw=[]
		self.plot_set_wl=[]
		self.plot_real_wl=[]
		self.plot_raw=[]
		self.plot_volts=[]
		self.plot_wl=[]
		for c in self.curve1:
			c.setData([],[])
		self.curve5.setData(self.plot_set_wl, self.plot_raw)
		self.curve3.setData([], [])
		self.pw1.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.pw1.setTitle(''.join(["CM110 scan as function of wavelength"]))
		self.pw1.setLabel('left', "Voltage", units='V')
		self.pw1.setLabel('bottom', "Wavelength", units='m')
		
		# PLOT 2 initial canvas settings
		self.set_wl_tr=[]
		self.real_wl_tr=[]
		self.plot_set_wl_tr=[]
		self.plot_real_wl_tr=[]
		self.plot_volts_tr=[]
		self.plot_time_tr=[]
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve4.setData(self.plot_time_tr, self.plot_set_wl_tr)
		self.curve6.setData(self.plot_time_tr, self.plot_real_wl_tr)
		self.pw2.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.p1.setTitle(''.join(["CM110 scan as function of time"]))
		self.p1.setLabel('left', "Voltage", units='V', color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s')
		
		self.stop_pressed = False
		
		
	def load_(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		try:
			self.config.read(''.join([self.cwd,os.sep,"config.ini"]))
			self.last_used_scan = self.config.get("LastScan","last_used_scan")
			
			self.start_cm110 = self.config.get(self.last_used_scan,"start")
			self.stop_cm110 = self.config.get(self.last_used_scan,"stop")
			self.step_cm110 = self.config.get(self.last_used_scan,"step")
			
			self.startst = self.config.get(self.last_used_scan,"startst")
			self.stopst = self.config.get(self.last_used_scan,"stopst")
			self.stepst = self.config.get(self.last_used_scan,"stepst")
			
			self.dwell_time = int(self.config.get(self.last_used_scan,"wait_time"))
			self.dwell_time_ard = int(self.config.get(self.last_used_scan,"wait_time_ard"))
			self.avg_pts = int(self.config.get(self.last_used_scan,"avg_pts"))
			self.schroll_time = int(self.config.get(self.last_used_scan,"schroll_time"))
			self.schroll_wl = int(self.config.get(self.last_used_scan,"schroll_wl"))
			self.channel = self.config.get(self.last_used_scan,"channel")
			
			self.filename_str = self.config.get(self.last_used_scan,"filename")
			self.timestr = self.config.get(self.last_used_scan,"timestr")
			self.analogref = float(self.config.get(self.last_used_scan,"analogref"))
			self.minutes = float(self.config.get(self.last_used_scan,"timer"))
			
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		
	def save_(self):
		
		self.timestr=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.timestr)
		
		self.config.set("LastScan","last_used_scan", self.last_used_scan )
		
		self.config.set(self.last_used_scan,"start", self.startEdit.text() )
		self.config.set(self.last_used_scan,"stop", self.stopEdit.text() )
		self.config.set(self.last_used_scan,"step", self.stepEdit.text()  )
		self.config.set(self.last_used_scan,"wait_time", self.dwelltimeEdit.text() )
		
		self.config.set(self.last_used_scan,"startst", self.startst_Edit.text() )
		self.config.set(self.last_used_scan,"stopst", self.stopst_Edit.text() )
		self.config.set(self.last_used_scan,"stepst", self.stepst_Edit.text() )
		
		self.config.set(self.last_used_scan,"wait_time_ard", self.dwelltimeEdit_ard.text() )
		self.config.set(self.last_used_scan,"avg_pts", str(self.avg_pts) )
		self.config.set(self.last_used_scan,"schroll_time", str(self.schroll_time) )
		self.config.set(self.last_used_scan,"schroll_wl", str(self.schroll_wl) )
		self.config.set(self.last_used_scan,"channel", self.channel )
		
		self.config.set(self.last_used_scan,"filename", self.filenameEdit.text() )
		self.config.set(self.last_used_scan,"timestr", str(self.timestr) )
		self.config.set(self.last_used_scan,"analogref", str(self.analogref) )
		
		with open(''.join([self.cwd,os.sep,"config.ini"]), "w") as configfile:
			self.config.write(configfile)
		
		
	def finished(self):
		
		if not self.stop_pressed:
			self.stopButton.setEnabled(False)
			if hasattr(self, "get_thread"):
				self.get_thread.abort()
			
			self.stop_pressed = True
		
		self.allFields(True)
		self.conMode.setEnabled(True)
		
		if self.inst_list.get("CM110") or self.inst_list.get("SR530") or self.inst_list.get("Ard") or self.inst_list.get("SMC100"):
			if self.cb_cm110.isChecked():
				self.allFields(False)
				self.cb_cm110.setEnabled(True)
				self.startEdit.setEnabled(True)
				self.runButton.setText("Move")
				self.runButton.setEnabled(True)
			elif self.cb_smc100.isChecked():
				self.allFields(False)
				self.cb_smc100.setEnabled(True)
				self.startst_Edit.setEnabled(True)
				self.runButton.setText("Move")
				self.runButton.setEnabled(True)
			else:
				self.allFields(True)
				self.runButton.setText("Scan")
		else:
			self.runButton.setText("Load instrument!")
		
		self.timer.start(1000*60*self.minutes)
		
		
	def closeEvent(self, event):
		
		reply = QMessageBox.question(self, 'Message', "Quit now? Any changes that are not saved will stay unsaved!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		
		if reply == QMessageBox.Yes:
			
			if self.inst_list.get("CM110"):
				if not hasattr(self, "get_thread"):
					if self.inst_list.get("CM110").is_open():
						self.inst_list.get("CM110").close()
				else:
					if not self.stop_pressed:
						QMessageBox.warning(self, "Message", "Scan in progress. Stop the scan then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("CM110").is_open():
							self.inst_list.get("CM110").close()
							
			if self.inst_list.get("SR530"):
				if not hasattr(self, "get_thread"):
					if self.inst_list.get("SR530").is_open():
						self.inst_list.get("SR530").close()
				else:
					if not self.stop_pressed:
						QMessageBox.warning(self, "Message", "Scan in progress. Stop the scan then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("SR530").is_open():
							self.inst_list.get("SR530").close()
			
			if self.inst_list.get("SMC100"):
				if not hasattr(self, "get_thread"):
					if self.inst_list.get("SMC100").is_open():
						self.inst_list.get("SMC100").close()
				else:
					if not self.stop_pressed:
						QMessageBox.warning(self, "Message", "Scan in progress. Stop the scan then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("SMC100").is_open():
							self.inst_list.get("SMC100").close()
							
			if self.inst_list.get("Ard"):
				if not hasattr(self, "get_thread"):
					if self.inst_list.get("Ard").is_open():
						self.inst_list.get("Ard").close()
				else:
					if not self.stop_pressed:
						QMessageBox.warning(self, "Message", "Scan in progress. Stop the scan then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("Ard").is_open():
							self.inst_list.get("Ard").close()
							
			if hasattr(self, "timer"):
				if self.timer.isActive():
					self.timer.stop()
					
			event.accept()
		else:
		  event.ignore()
		
	##########################################
	
	def save_plots(self):
		
		# For SAVING data
		if "\\" in self.filenameEdit.text():
			self.filenameEdit.setText(self.filenameEdit.text().replace("\\",os.sep))
			
		if "/" in self.filenameEdit.text():
			self.filenameEdit.setText(self.filenameEdit.text().replace("/",os.sep))
			
		if not self.filenameEdit.text():
			self.filenameEdit.setText(''.join(["data",os.sep,"data"]))
		
		if not os.sep in self.filenameEdit.text():
			self.filenameEdit.setText(''.join(["data", os.sep, self.filenameEdit.text()]))
			
		save_plot1 = self.create_file(''.join([self.filenameEdit.text(),".png"]))
		save_plot2 = self.create_file(''.join([self.filenameEdit.text(),"_elapsedtime",".png"]))
		
		# create an exporter instance, as an argument give it
		# the item you wish to export
		exporter = pg.exporters.ImageExporter(self.pw1.plotItem)
		exporter.params.param('width').setValue(1920, blockSignal=exporter.widthChanged)
		exporter.params.param('height').setValue(1080, blockSignal=exporter.heightChanged)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot1)
		
		exporter = pg.exporters.ImageExporter(self.pw2.plotItem)
		exporter.params.param('width').setValue(1920, blockSignal=exporter.widthChanged)
		exporter.params.param('height').setValue(1080, blockSignal=exporter.heightChanged)
		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_plot2)
		
		
#########################################
#########################################
#########################################


def main():
	
	app = QApplication(sys.argv)
	ex = Run_CM110()
	#sys.exit(app.exec())
	
	# avoid message "Segmentation fault (core dumped)" with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()


if __name__ == '__main__':
	
	main()
