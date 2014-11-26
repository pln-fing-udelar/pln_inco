# -*- coding: utf-8 -*- 
import subprocess
import shlex
import codecs
import os
"""
Module for using the GENIA tagger
Part of the pln-inco package
"""
	
def tag(fileName, geniaHome):
	""" 
	Given a file, process it with the GENIA tagger and return its result
	@arg fileName: file with the text to process
	@arg geniaHome: GENIA Home. We need it because GENIA only works when the file is in its own directory (!)
	"""

	# change to the GENIA home
	present_dir=os.getcwd()
	os.chdir(geniaHome)
	p=subprocess.Popen(['./geniatagger',fileName], stdout=subprocess.PIPE)
	result= p.communicate()[0]
	# back to the directory we started
	os.chdir(present_dir)
	return result
