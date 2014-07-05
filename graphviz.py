# -*- coding: utf-8 -*- 
from subprocess import Popen, PIPE

"""
A module for generating graphviz images
"""

def generate(entrada,format):
	""" Given a graphviz specification, returns the dot generated file, in the specifyied format
	Format can be one of: 'jpg', 'png'
	"""
	
	if format=='jpg':
		opt='-Tjpg'
	elif format=='png':
		opt='-Tpng'
		
	p=Popen(['dot',opt], stdin=PIPE, stdout=PIPE)
	return p.communicate(input=entrada)[0]
