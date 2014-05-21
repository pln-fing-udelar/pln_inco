# -*- coding: utf-8 -*- 
from subprocess import Popen, PIPE

"""
Operaciones para trabajar con graphviz
"""

def generate(entrada,format):
	""" Given a graphviz specification, returns the dot generated file, in the specifyied format
	Format can be one of: 'svg', 'png'
	"""
	
	if format=='svg':
		opt='-Tjpg'
	elif format=='png':
		opt='-Tpng'
		
	p=Popen(['dot',opt], stdin=PIPE, stdout=PIPE)
	return p.communicate(input=entrada)[0]
