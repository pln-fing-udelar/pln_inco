"""
Module for working with  NLTK syntax trees
"""
import nltk.tree

def tree_to_dot(t):
	"""
	Given a NLTK full syntax Tree, returns a dot representation, suitable for using with Graphviz.
	This function assumes that the node property is a String

	@type t: L{nltk.tree.Tree}
	@rtype: C{string}

	"""


	def gv_print(t,start_node=1):
		"""
		Print the tree for a defined node. Nodes are specified in-order in the original tree	
		"""

		# Print the start node of the tree
		s='%s [label="%s"]' % (start_node,t.node)
		pos=start_node+1

		# Print the node's children
		for child in t:
			if isinstance(child,nltk.tree.Tree):
				(s_child,newpos)=gv_print(child,pos)
				s=s+'\n'+ s_child
				s=s+'\n%s -> %s' % (start_node,pos)
				pos=newpos
			elif isinstance(child, str):
				s=s+'\n%s [label="%s", shape=plaintext]' % (pos,child)
				s=s+'\n%s -> %s' % (start_node,pos)	
			pos+=1
		return (s,pos-1)

	# Print the digraph dot specification
	s="digraph G{\n"	
	s+=gv_print(t)[0]
	s+="\n}"

	return s
