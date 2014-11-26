# -*- coding: utf-8 -*- 
from subprocess import Popen, PIPE

"""
A module for generating graphviz images
"""

def generate(dot,format):
	""" Given a graphviz specification, returns the dot generated file, in the specifyied format
	This function assumes that dot is installed and included in the PATH variable
	Format can be one of: 'jpg', 'png', 'svg'
	@arg input: a unicode string with the dot specification 
	@arg format: one of 'jpg', 'png', 'svg'
	@return a binary file with the appropiate format
	"""
	
	if format=='jpg':
		opt='-Tjpg'
	elif format=='png':
		opt='-Tpng'
	elif format=='svg':
		opt='-Tsvg'
		
	encoded_string=dot.encode('utf-8')
	p=Popen(['dot',opt], stdin=PIPE, stdout=PIPE)
	return p.communicate(input=encoded_string)[0]
