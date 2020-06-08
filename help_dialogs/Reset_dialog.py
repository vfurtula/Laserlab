#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import re, serial, time

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QFrame
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QWidget)



class WorkerSignals(QObject):
	
	# Create signals to be used
	about = pyqtSignal(object)
	critical = pyqtSignal(object)
	warning = pyqtSignal(object)
	info = pyqtSignal(object)
	
	statusbyte = pyqtSignal(object)
	finished = pyqtSignal()
	
	
	
	
class Reset_Thread(QRunnable):
	"""
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	"""
	def __init__(self,*argv):
		super(Reset_Thread, self).__init__()
		
		# constants	
		self.inst_list = argv[0]
		
		self.signals = WorkerSignals()
			
			
	@pyqtSlot()
	def run(self):
		
		try:
			self.reset()
		except Exception as e:
			self.signals.warning.emit(str(e))
		else:
			pass
		finally:
			if self.inst_list.get("SMC100"):
				val = self.inst_list.get("SMC100").return_ts(1)
				self.signals.statusbyte.emit(val[-2:])
				
			self.signals.finished.emit()  # Done
			
			
	def abort(self):
		
		if self.inst_list.get("SMC100"):
			self.inst_list.get("SMC100").abort()
			
			
	def reset(self):
		
		if self.inst_list.get("SMC100"):
			val = self.inst_list.get("SMC100").return_ts(1)
			self.signals.statusbyte.emit(val[-2:])
			
			if val[-2:] not in ["32","33","34","35"]:
				time.sleep(1)
				self.signals.info.emit("go_home")
				self.inst_list.get("SMC100").go_home(1)
		
		
		
		
		
		
		
class Reset_dialog(QDialog):
	
	def __init__(self, parent, inst_list):
		super().__init__(parent)
		
		# constants
		self.inst_list = inst_list
		
		self.setupUi()
		
		
	def setupUi(self):
		
		self.stopButton = QPushButton("STOP RESET",self)
		self.stopButton.setFixedHeight(35)
		self.stopButton.setFixedWidth(150)
		self.stopButton.setEnabled(False)
		
		self.startButton = QPushButton("Start reset",self)
		self.startButton.setFixedHeight(35)
		self.startButton.setFixedWidth(150)
		self.startButton.setEnabled(True)
		
		lbl0 = QLabel("Statusbyte returned from the SMC100PP:\t", self)
		self.lbl_st = QLabel("", self)
		self.lbl_st.setStyleSheet("color: blue")
			
		grid_0 = QHBoxLayout()
		grid_0.addWidget(self.startButton)
		grid_0.addWidget(self.stopButton)
		grid_1 = QHBoxLayout()
		grid_1.addWidget(lbl0)
		grid_1.addWidget(self.lbl_st)
		grid_2 = QVBoxLayout()
		grid_2.addLayout(grid_0)
		grid_2.addLayout(grid_1)
		
		# cancel the script run
		self.startButton.clicked.connect(self.start)
		self.stopButton.clicked.connect(self.abort)
		
		self.threadpool = QThreadPool()
		
		self.setLayout(grid_2)
		self.setWindowTitle("Reset dialog for SMC100PP stepper")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		grid_2.setSizeConstraint(grid_2.SetFixedSize)
		
		
	def abort(self):
		
		self.worker.abort()
			
			
	def start(self):
		
		reply = QMessageBox.question(self, 'Message', "The stepper will RESET and MOVE to the home position. Remove all components from the stepper head!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		
		if reply == QMessageBox.Yes:
			
			self.worker = Reset_Thread(self.inst_list)
			self.worker.signals.finished.connect(self.finished)
			self.worker.signals.info.connect(self.info)
			self.worker.signals.statusbyte.connect(self.statusbyte)
			# Execute
			self.threadpool.start(self.worker)
			
			#################################################
			
			self.startButton.setEnabled(False)
			self.startButton.setText("..reseting..")
		
		
	def finished(self):
		
		self.startButton.setEnabled(True)
		self.startButton.setText("Start reset")
		self.stopButton.setEnabled(False)
		self.setWindowTitle("Reset dialog for SMC100PP stepper")
		
		
	def statusbyte(self,sb):
		
		self.lbl_st.setText(sb)
		
		
	def info(self,mystr):
		
		if mystr=="go_home":
			self.setWindowTitle("homing the stepper, please wait!")
			self.stopButton.setEnabled(True)
		elif mystr=="reset":
			self.setWindowTitle("reseting the stepper, please wait!")
			self.stopButton.setEnabled(False)
		else:
			self.stopButton.setEnabled(False)
		
		
	def about(self,mystr):
		
		QMessageBox.about(self, 'Message',mystr)
		
		
	def warning(self,mystr):
		
		QMessageBox.warning(self, 'Message',mystr)
		
		
	def critical(self,mystr):
		
		QMessageBox.critical(self, 'Message',mystr)
		
		
	def closeEvent(self,event):
		
		event.accept()
		
		
		
		
		
		
		
		
		
		
		
		
		
