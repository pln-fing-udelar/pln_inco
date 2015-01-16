# -*- coding: utf-8 -*- 

import nltk,nltk.tokenize,xml.etree
import os,codecs,fnmatch,re,types, copy,shutil
from sys import *
from pln_inco import graphviz,penn_treebank,stanford_parser
from string import *
import pln_inco
import time
import sqlite3
import os.path

class BioscopeCorpus:
	""" 
	This class includes every info we collect / generate about the Bioscope corpus. The related BioscopeCorpusProcessor loads the original corpus files into this structure
	@ivar documents: dictionary of L{bioscope.BioscopeDocument}, indexed by the document's id
	@type documents: C{Dictionary}
	"""
	
	def __init__(self,bcp,prefix):
		"""
		Loads the corpus documents from the corpus files. 
		@arg bcp: Environment information for the corpus original files.
		@type bcp: L{bioscope.BioscopeCorpusProcessor}
		@rtype: C{None}
		@arg prefix: Load only documents whose name matches the prefix 
		@type prefix: String
		"""
		
		# Get document ids from the corpus
		document_ids=bcp.get_doc_ids('a')

		# Create document list  
		self.documents=dict()
		contador=0
		total=len(document_ids)
		for docId in document_ids:
			if re.match(prefix,docId):
				contador+=1
				#print "Loading document ",docId, contador, " from ", total
				try:
					d=BioscopeDocument(docId,bcp)
					d.add_genia_and_bioscope_info(bcp)			
					self.documents[docId]=d
				except IndexError:
					print "I couldn't load document ",docId
		
class BioscopeDocument:
	""" 
	Bioscope document, including tagging and parsing information
	@ivar docId: document identified
	@type docId: C{string}
	@ivar sentences: instances of  L{bioscope.BioscopeSentence} included in the document 
	@type sentences: C{Dictionary}
	"""
	
	
	def __init__(self, docId,bcp):
		""" 
		Create the document and its sentences, loading from the corresponding files. This method does not loads Genia information (this is done with 
		L{bioscope.BioscopeDocument.add_genia_and_bioscope_info}
		
		@type bcp: L{bioscope.BioscopeCorpusProcessor}
		@rtype: C{None}
		"""

		self.docId=docId
		
		# Get sentence ids within the document 
		sentence_ids=bcp.get_sentence_ids(docId)

	
		self.sentences=dict()
		i=0
		for sentenceId in sentence_ids:
			s=BioscopeSentence(self.docId,sentenceId,i,bcp)
			self.sentences[sentenceId]=s
			i+=1

		# Load the parsing trees from the corresponding .parsed file...
		parsed_sentences=bcp.load_parsed_sentences(docId)
		for (key,sentence) in self.sentences.iteritems():
			#print>>stderr, key, sentence.sindex
			sentence.data=parsed_sentences[sentence.sindex]

	def add_genia_and_bioscope_info(self,bcp):	
		"""
		Adds to the parsing tree the tagging information produced by Genia Tagger
		@rtype: C{None}
		"""
	
		for (key,sentence) in self.sentences.iteritems():
			parse_tree=sentence.data

			
			# Load the sentence tokens according to Genia
			genia_words=bcp.get_genia_words(self.docId,sentence.sentenceId)
			
			# Load the sentence tokens according to Bioscope 
			bioscope_tokens=bcp.get_bioscope_tokens(self.docId,sentence.sentenceId)

			# If tokenization is different, use some heuristics to realign
			if len(genia_words)!=len(bioscope_tokens) and genia_words and bioscope_tokens:
				bioscope_tokens=pln_inco.bioscope.bioscope_retokenize(genia_words,bioscope_tokens)
				
			if len(genia_words)==len(bioscope_tokens)==len(parse_tree.leaves()):
				j=0
				for p in parse_tree.leaves():
					# Traverse the tree leaves and add information from Genia results
					tpos=parse_tree.leaf_treeposition(j)
					leaf_parent= tpos[0:len(tpos)-1]

					# Modify the tree label, changing it into a Dictionary with the Genia attributes
					# By default, this label is the POS
					pos=parse_tree[leaf_parent].label()

					# Get Genia Tagger attributes
					(word,lemma,pos2,chunk,ne)=genia_words[j] 

					# Get bioscope attributes
					specCue=bioscope_tokens[j][1]['SpecCue']
					negCue=bioscope_tokens[j][1]['NegCue']
					specXcope=bioscope_tokens[j][1]['specXcope']
					negXcope=bioscope_tokens[j][1]['negXcope']
					
					parse_tree[leaf_parent].set_label({'lemma':lemma, 'pos':pos, 'chunk':chunk, 'entity':ne, 'specCue':specCue, 'negCue':negCue,'specXcope':specXcope,'negXcope':negXcope})
					j+=1
				sentence.data_loaded=True
			else:
				print >> stderr, "Problem:"+sentence.sentenceId+":"+self.docId
				print >> stderr, sentence.sentenceId+':'+self.docId+':'+"Genia    words:",[x[0] for x in genia_words]
				print >> stderr, sentence.sentenceId+':'+self.docId+':'+"Bioscope words:",[x[0] for x in bioscope_tokens]
				print >> stderr, sentence.sentenceId+':'+self.docId+':'+"Leaves:        ",[x for x in parse_tree.leaves()]
				print >> stderr, "Lengths:",len(genia_words)," ",len(bioscope_tokens)," ", len(parse_tree.leaves())
				sentence.data_loaded=False
				
class BioscopeSentence:
	""" 
	This class contains the information for a single sentence in the corpus, including tagging and parsing information. Part of L{bioscope.BioscopeDocument}
		@ivar docId: document identifier 
		@type docId: C{string}
		@ivar sentenceId: sentence identifier 
		@type sentenceId: C{string}
		@ivar sindex: Intenger index for the sentence in the document
		@type sindex: C{int}
		@ivar data: Sentence parsing tree. 
		@type data: C{nltk.Tree}
		@ivar data_loaded: feature indicating if the information for the sentence has been correctly loaded 
		@type data_loaded: C{bool}
	"""
	
	def __init__(self,docId,sentenceId,sindex,bcp):
		"""
		Create the datastructures. Data is not loaded (this is done within the  L{bioscope.BioscopeDocument} class, where all sentences are loaded at the same time).
		@rtype:C{None}
		@type bcp: L{bioscope.BioscopeCorpusProcessor}
		
		"""
		self.docId=docId
		self.sentenceId=sentenceId
		self.sindex=sindex
		self.data=None
		self.data_loaded=False
		
	def has_hedging(self):
		"""
		Returns true if the sentence includes a hedge cude
		@rtype: C{bool}
		"""


		def has_hedge_cue(s): 
			""" 
			Given a node, returns True if it corresponds to a hedge cue
			@rtype: bool
			@arg s: tree node
			@type s: types.StringType o types.DictType
			"""
			if isinstance(s,types.StringType):
				return False
			elif isinstance(s,types.DictType):
				if s['specCue'] !='O':
					return True
				else:
					return False


		def has_hedging(t):
			"""
			Given a tree, returns True if it includes a hedge cue
			@rtype:bool
			@arg t:
			@type t: nltk.tree.Tree
			"""
			hh=False
			if has_hedge_cue(t.label()):
				return True
			else:
				for child in t: 
					if isinstance(child,nltk.tree.Tree):
						hh=has_hedging(child)

					if hh:
						return True

			return False
			
		return has_hedging(self.data)


	def has_negation(self):
		"""
		Returns True if the sentence includes a negation mark
		@rtype: C{bool}
		"""


		def has_negation_cue(s): 
			""" 
			Given a node, return True if it corresponds to a Negation Cue
			@rtype: bool
			@arg s: Tree node 
			@type s: types.StringType o types.DictType
			"""
			if isinstance(s,types.StringType):
				return False
			elif isinstance(s,types.DictType):
				if s['negCue'] !='O':
					return True
				else:
					return False


		def has_negation(t):
			"""
			Given a parsing tree, returns True if it includes a negation cue
			@rtype:bool
			@arg t:
			@type t: nltk.tree.Tree
			"""
			hh=False
			#if has_negation_cue(t.node):
			if has_negation_cue(t.label()):
				return True
			else:
				for child in t: 
					if isinstance(child,nltk.tree.Tree):
						hh=has_negation(child)

					if hh:
						return True

			return False
			
		return has_negation(self.data)


	def get_dot(self):
		"""
		Return a Graphviz specification of the sentence tree (including tagging and hedging marks)
		@rtype: C{string}
		"""
		
		def gv_rep(s):
			""" 
			Graphviz specification for a node. The function discriminates the cases when it includes just a POS tag, from those where it is a dictionary
			"""
			if isinstance(s,unicode):
				# If we have a unicode string, returns it  
				res=s
			elif isinstance(s,types.DictType):
				# build the string using dictionary values 
				res=s['pos']
				
				if s['chunk'] != 'O':
					res=res+'\\n'+'chunk:'+s['chunk']
				
				if s['entity']!='O':
					res=res+'\\n'+'entity:'+s['entity']
				
				if s['specCue'][0] !='O':
					res=res+'\\n'+'specCue:'+",".join(s['specCue'])
				
				if s['negCue'][0] !='O':
					res=res+'\\n'+'negCue:'+",".join(s['negCue'])
				
				if s['specXcope'][0] !='O':
					res=res+'\\n'+'specXcope:'+",".join(s['specXcope'])
					
				if s['negXcope'][0] !='O':
					res=res+'\\n'+'negXcope:'+",".join(s['negXcope'])

			else:
				res="Error"
		
			return res
				  
		def gv_print(t,initial=1):
			"""
			Given a tree, generate is graphviz representation. Node numeration starts with the iniitial parameter
			"""
			
			# Show the tree's root node 
			s='%s [label="%s"]' % (initial,gv_rep(t.label()))
	
			pos=initial+1
			for child in t: 
			
				
				if isinstance(child,nltk.tree.Tree):
					(s_child,newpos)=gv_print(child,pos)
					s=s+'\n'+ s_child
					s=s+'\n%s -> %s' % (initial,pos)
					pos=newpos
				elif isinstance(child, unicode):
					s=s+'\n%s [label="%s", shape=plaintext]' % (pos,child)
					s=s+'\n%s -> %s' % (initial,pos)			
				pos=pos+1
			return (s,pos-1)


		s="digraph G{\n"		
		s+=gv_print(self.data)[0]
		s+="\n}"
		
		return s
		
	def get_basic_attributes(self):
		"""
		Return a list of tokens, and its attributes. 
		The first element is a list with the attributes names
		@rtype: C{List}
		"""


		def get_tree_leaves(t):
			"""
			Given a tree, returns a list with its elements and tags, inorder.
			"""
			
			res=[]
			for child in t: 
				if isinstance(child, unicode):
					#s=t.node
					s=t.label()
					res=[(child,s['lemma'],s['pos'],s['chunk'],strip(s['entity']),s['specCue'],s['negCue'],s['specXcope'],s['negXcope'])]
				else:
					res += get_tree_leaves(child)
			return res
				
		
		s_table=[('TOKEN','LEMMA','POS','CHUNK','NE','SPEC-CUE','NEG-CUE','SPEC-XCOPE','NEG-XCOPE')]
		s_table += get_tree_leaves(self.data)
		return s_table
	
	def get_leaf_grandparent(self,leaf_pos,gp_number):
		"""
		Given a tree leave, returns its grandparent tree, and a treepos indicating the position in the original tree
		@arg leaf_pos: leave numer 
		@type leaf_pos: L{int}
		@arg gp_number: Grandparent number. Grandparent=2, Great-granparent=3, etc.
		@rtype: C{nltk.Tree}		
		
		
		"""
		parse_tree=self.data
		# Get the leave treepos 
		leaf_treepos=parse_tree.leaf_treeposition(leaf_pos)
		# Its grandparent treepos is just the same, without the last gp_number elements 
		leaf_grandparent=leaf_treepos[0:len(leaf_treepos)-gp_number]
		
		s=parse_tree[leaf_grandparent]
		return (s,leaf_grandparent)
	
	def get_node_scope(self,treepos):
		"""
		Given a tree node, returns the treepos for the first and last leaves within its scope
		@arg treepos: node position within the sentence tree
		@type treepos: C{List}
		@rtype: C{sequence}
		"""
		parse_tree=self.data
		subtree=parse_tree[treepos]
		# Move from 0, to find the first position of the scope 
		current_treepos=treepos
		while not isinstance(parse_tree[current_treepos],types.StringType):
			current_treepos=current_treepos+(0,)
		subtree_start_treepos=current_treepos
		subtree_end=subtree.leaf_treeposition(len(subtree.leaves())-1)
		subtree_end_treepos=treepos+subtree_end
		
		j=0
		for l in parse_tree.leaves():
			if parse_tree.leaf_treeposition(j) == subtree_start_treepos:
				start=j
			if parse_tree.leaf_treeposition(j)== subtree_end_treepos:
				if parse_tree[subtree_end_treepos]=='.':
					end=j-1
				else:
					end=j
				break
			j+=1
		return (start,end)
			

	def get_node_hedge_scope(self,treepos):
		"""
		Given a tree node, returns the treepos for the first and last leaves within its scope. This is a modified version 
		of  L{get_node_scope}, including some pruning heuristics that modify the scope to match Bioscope annotation criteria
		@arg treepos: Node position within the tree
		@type treepos: C{List}
		@rtype: C{sequence}
		"""
		parse_tree=self.data
		subtree=parse_tree[treepos]
		
		# Node children 
		children=parse_tree[treepos]
		# Node pos 
		pos=parse_tree[treepos].node
		
		current_treepos=treepos		
		
		# If the node corresponds to an S, when going down the tree I skip PP and ADVP to the left 
		if parse_tree[treepos].node in ['S','SBAR']:
			child_number=0
			for child in parse_tree[treepos]:
				if isinstance(child.node,types.DictType):
					if child.node['lemma']<>',':
						current_treepos=treepos+(child_number,)
						break
				else:
					if child.node not in ['ADVP','PP']:
						current_treepos=treepos+(child_number,)
						break
					else:
						pass
				child_number+=1

		# If the node corresponds to an NP, I skip left determiners, when they appear before an JJ
		elif parse_tree[treepos].node in ['NP']:
			children=parse_tree[treepos]
			j=0
			while j<len(children):
				child=children[j]
				if isinstance(child.node,types.DictType):
					if child.node['pos']=='DT' and children[j+1].node['pos']=='JJ':
						pass
					else:
						current_treepos=treepos+(j,)
						break
				j+=1
				
		while not isinstance(parse_tree[current_treepos],types.StringType):
			current_treepos=current_treepos+(0,)
		subtree_start_treepos=current_treepos
		subtree_end=subtree.leaf_treeposition(len(subtree.leaves())-1)
		subtree_end_treepos=treepos+subtree_end
		
		j=0
		for l in parse_tree.leaves():
			if parse_tree.leaf_treeposition(j) == subtree_start_treepos:
				start=j
			if parse_tree.leaf_treeposition(j)== subtree_end_treepos:
				if parse_tree[subtree_end_treepos]=='.':
					end=j-1
				else:
					end=j
				break
			j+=1
		return (start,end)
		
		
	def get_scope_start(self,treepos):
		"""
		Given a tree and a node, returns the left position of the scope
		"""
		
		parse_tree=self.data
		
		current_treepos=treepos
		while not isinstance(parse_tree[current_treepos],types.StringType):
			current_treepos=current_treepos+(0,)
		subtree_start_treepos=current_treepos
		
		j=0
		for l in parse_tree.leaves():
			if parse_tree.leaf_treeposition(j) == subtree_start_treepos:
				start=j
				break
			else:
				j+=1
		
		return start



	def get_scope_end(self,treepos):
			"""
			Given a tree and a node, returns the right position of the scope
			"""
			parse_tree=self.data
			subtree_end=parse_tree[treepos].leaf_treeposition(len(parse_tree[treepos].leaves())-1)
			subtree_end_treepos=treepos+subtree_end
			
			j=0
			for l in parse_tree.leaves():
				if parse_tree.leaf_treeposition(j)== subtree_end_treepos:
					if parse_tree[subtree_end_treepos] in ('.',':'):
						end=j-1
					else:
						end=j
					break
				j+=1
			
			return end


	
	def get_node_hedge_scope(self,treepos,hedge_cue_pos,use_heuristics=True):
		"""

		Given a tree node, returns the treepos for the first and last leaves within its scope. This is a modified version 
		of  L{get_node_scope}, including some pruning heuristics that modify the scope to match Bioscope annotation criteria
		@arg treepos: Node position within the tree
		@arg use_heuristics: if True it uses heuristics; if False, it just returns the result of L{get_scope_start} and L{get_scope_end}
		@type treepos: C{List}
		@rtype: C{sequence}
		"""
		parse_tree=self.data
		subtree=parse_tree[treepos]
		node_pos=subtree.node
		hedge_cue_treepos=parse_tree.leaf_treeposition(hedge_cue_pos)
		leaves=parse_tree.leaves()

		
		#parent_treepos=treepos[0:len(treepos)-1]
		#gparent_treepos=treepos[0:len(parent_treepos)-1]
		#left_parent_brother=treepos[0:parent_treepos[-1]-1]
		#right_parent_brother=treepos[0:parent_treepos[-1]+1]
		
		#print "Treepos del Ã¡rbol:",treepos
		#print subtree.leaves()
		#print "Cantidad de hojas:", len(subtree.leaves())
		#subtree_start=subtree.leaf_treeposition(0)
		
		# Get first and last scope positions 
		start=self.get_scope_start(treepos)
		end=self.get_scope_end(treepos)
		
		if use_heuristics:
			if node_pos in ['S','SBAR','VP']:
				# Omit PP and SBAR to the left of the scope
				j=0
				for child in subtree:
					if isinstance(child.node,types.DictType):
						if child.node['lemma']<>',':
							start=self.get_scope_start(treepos+(j,))
							break
					else:
						if child.node not in ['ADVP','PP','SBAR']:
							start=self.get_scope_start(treepos+(j,))
							break
						else:
							#print "Encontre ejemplo de regla 1"
							pass
					
					j+=1



				# If, at the end of the scope, there is a clause starting with because and other connectives, the scopes ends just when the clause stats
				j=hedge_cue_pos
				while j<=end:
					child=leaves[j]
					#print j,child
					if child in ['because','since','like','unlike','unless','minus','although','ie']:

						end=j-1
						break

					elif child in ['as'] and leaves[j-1]==',':
						end=j-1
						break

					j+=1

				# If the scope ends with a comma, delete it from the scope
				if leaves[end]==',':
					end=end-1
			elif node_pos in ['NP']:
				# If facing a NP, and there is a brother-PP to the right, add it to the scope
				parent_treepos=treepos[0:len(treepos)-1]
				if parent_treepos:
					try:
						right_parent_brother=parent_treepos+(treepos[-1]+1,)
						if parse_tree[right_parent_brother].node=='PP':
							end=self.get_scope_end(right_parent_brother)
					except IndexError:
						pass

				# If the hedge cue is a JJ, delete determiners
				hedge_cue_treepos2=hedge_cue_treepos[0:len(hedge_cue_treepos)-1]
				if parse_tree[hedge_cue_treepos2].node['pos']=='JJ':
					first_leaf=parse_tree.leaf_treeposition(start)
					first_leaf_parent=first_leaf[0:len(first_leaf)-1]

					if parse_tree[first_leaf_parent].node['pos']=='DT':	
						start+=1
		
		return (start,end)
		
	

class BioscopeCorpusProcessor:
	""" Methods for loading the original corpus from its xml format, and generate intermediate  analysis files
	
	@ivar working_dir: BIOSCOPE corpus directoy, containing the .xml files
 	@type working_dir: C{string}

	
	@ivar txt_dir: directory for the text version of the corpus, one file = one document. One sentence per line.
	@type txt_dir: C{string}
	
	@ivar parsed_files_dir: directory for theh parsing results. One file = one document.  
	@type parsed_files_dir: C{string}
	
	@ivar bioscope_files_dir: directory for the Bioscope annotated version of the documents. One file = one document, xml files. 
	@type bioscope_files_dir: C{string}
	
	@ivar event_dir: Genia event directory 
	@type event_dir: C{string}
	
	@ivar genia_files_dir: directory for the Genia annotated texts. One file = one sentence
	@type genia_files_dir: C{string}
	
	@ivar att_dir: directory for the attribute files. One file = one sentence
	@type att_dir: C{string}
	
	@ivar crf_corpus_dir: directory for the CRF analysis of the corpus
	@type crf_corpus_dir: C{string}
		
	@ivar genia_articles_dir: directory for the Genia annotated texts. One file = one document
	@type genia_articles_dir: C{string} 
	@ivar genia_temp_file: temporary file for Genia analsyis. It is called genia_temp.txt and it is placede in the working_dir
	@type genia_temp_file: C{string}
	@ivar genia_temp_results_files: temporary file for Genia analysis results. It is called genia_temp.genia and it is placed in the working directory
	@type genia_temp_results_files: C{string}
	
	@ivar genia_event_corpus_dir: corpus Genia Event original
	@type genia_event_corpus_dir: C{string}
	
	@ivar parser_grammar_file: stanford parser Grammar file
	@type parser_grammar_file: C{string}
	
	@ivar original_bioscope_corpus: XML file for the Bioscope corpus 
	@type original_bioscope_corpus: C{xml.etree.ElementTree}
	
	@ivar bioscope_files_corpus: XML Corpus reader for the bioscope corpus. This Reader allows to read each document separately
	@type bioscope_files_corpus: C{nltk.corpus.XMLCorpusReader}
	
	@ivar parsed_files_corpus: NLTK Corpus Reader for reading the parsed files
	@type parsed_files_corpus: C{nltk.corpus.BracketParseCorpusReader}
	
	@ivar genia_files_corpus: NLTK corpus reader for reading Genia analysis
	@type genia_files_corpus: C{nltk.corpus.WordListCorpusReader}
	
	@ivar training_filename: CRF/Yamcha  training file 
	@type training_filename:C{string}

	@ivar att_database: SQLite file for the corpus. It is called attributes.db, and placed in the C{working_dir}
	@type att_database:C{string}
	
	"""
	
	
	def __init__(self, working_dir, bioscope_xml_file):
	
		"""
		Loads the required variables (directories, file names, etc...) that allows processing the original Bioscope corpus and 
		generate intermediate results
		
		@arg working_dir: Bioscope corpus directory 
		@type working_dir: C{string}
		@arg bioscope_xml_file: Bioscope corpus file 
		@type bioscope_xml_file: C{string}
		@rtype: C{None}
		"""
		
		self.working_dir=working_dir
		self.txt_dir=os.path.join(working_dir,'txt')
		self.parsed_files_dir=os.path.join(working_dir,'parsed')
		self.bioscope_files_dir=os.path.join(working_dir,'bioscope')
		self.event_dir=os.path.join(working_dir,'event')
		self.genia_files_dir=os.path.join(working_dir,'genia')
		self.attribute_table_files_dir=os.path.join(working_dir,'attributes')
		self.genia_articles_dir=os.path.join(working_dir,'genia_articles')
		self.image_files_dir=os.path.join(working_dir,'img')

	
		# Genia analysis 
		self.genia_temp_file=os.path.join(working_dir,'genia_temp.txt')
		self.genia_temp_results_file=os.path.join(working_dir,'genia_temp.genia')
		
		
		# GENIA home  
		self.genia_home=os.path.expandvars('$GENIA_TAGGER_HOME')		
		self.genia_event_corpus_dir=os.path.expandvars('$GENIA_EVENT')
		
		# Stanford parser grammar
		self.parser_grammar_file=os.path.join(os.path.expandvars('$STANFORD_PARSER_HOME'),'englishPCFG.ser.gz')
		
	
		# Original corpus (composed by one or more xml files), and analyzed files
		self.original_bioscope_corpus=nltk.corpus.XMLCorpusReader(working_dir,'.\*\.xml').xml(bioscope_xml_file)
		self.bioscope_files_corpus=nltk.corpus.XMLCorpusReader(self.bioscope_files_dir,'.\*\.bioscope')
		self.parsed_files_corpus=nltk.corpus.BracketParseCorpusReader(self.parsed_files_dir,'.\*\.parsed')
		self.genia_files_corpus=nltk.corpus.WordListCorpusReader(self.genia_files_dir,'\.\*\.genia')
		
		# SQLite DB for storign attributes
		self.att_database=os.path.join(working_dir,'attributes.db');

		
	def get_doc_ids(self,prefix):
		""" 
		Read the corpus and return a list of document identifiers.
		@arg prefix: optional prefix for loading only certain documents
		@type prefix: C{String}
		@rtype: C{List}
		
		"""
		
		ids=[]
		for docset in self.original_bioscope_corpus.getchildren(): 
			for doc in docset.getchildren(): # Get			
				docId=doc.getchildren()[0].text 
				ids.append(prefix+docId)
		return ids
	
	def get_sentence_ids(self,docId):
		""" 
		Given a document, read the corresponding .bioscope file and return a list of sentence identifiers
		@arg docId: document identifier
		@type docId: C{Integer}
		@rtype:C{List}
		
		"""
		
		bioscope_doc=self.bioscope_files_corpus.xml(docId+'.bioscope')
		ids=[]
		for sentence in bioscope_doc.getchildren():
			ids.append(sentence.get('id'))
		
		return ids							
			
	def load_parsed_sentences(self,docId):
		""" 
		Given a document identifier, read the corresponding .parsed files and return a list of parsed sentences (loaded using the C{nltk.corpus.BracketParseCorpusReader}C{nltk.corpus.BracketParseCorpusReader} NLTK reader. Sentences are ordered as they appear in the .parsed file.
		@rtype: C{List}
		"""
		
		# Lo primero que hace es parsear el documento, solamente si el documento tiene alguna marca de incertidumbre
		return self.parsed_files_corpus.parsed_sents(docId+'.parsed')
		
		
	def get_genia_words(self,docId,sentenceId):
		""" 
		Given a document and sentence dentifier, return a list of (word,lemma,pos,chunk,ne) tuples generated by the Genia tagger
		@rtype: C{List}
		"""
		genia_raw_words=self.genia_files_corpus.words(docId+'.'+sentenceId+'.genia')
		genia_words=[]
		for word in genia_raw_words:
			(word,lemma,pos,chunk,ne)=split(rstrip(word,os.linesep),'\t')		
			genia_words.append((word,lemma,pos,chunk,ne))
		return genia_words
		
	def get_max_nesting_level(self,docId,sentenceId,scope_type):
		"""
		Given a sentence returns the maximum nesting level for hedging/negation
		@arg scope_type: One of 'negation' or 'hedging'
		@type scope_type: C{String}
		@rtype: Int
		"""
		

		def includes_hedging_or_negation(element,xcope_id,scope_type):
			if element.tag=='cue' and element.get('type')==scope_type and element.get('ref')==xcope_id:
				return True
			else:
				for ch in element.getchildren():
					if includes_hedging_or_negation(ch,xcope_id,scope_type):
						return True
				return False


		def get_bioscope_element_hedge_or_negation_levels(element,scope_type):
			if element.tag=='xcope' and includes_hedging_or_negation(element,element.get('id'),scope_type):
				nested_levels=1
			else:
				nested_levels=0

			# Sum children hedge nesting level
			child_max_nested_levels=0
			for ch in element.getchildren():
					if get_bioscope_element_hedge_or_negation_levels(ch,scope_type) > child_max_nested_levels:
						child_max_nested_levels=get_bioscope_element_hedge_or_negation_levels(ch,scope_type)
			return child_max_nested_levels+nested_levels
					
		bioscope_doc=self.bioscope_files_corpus.xml(docId+'.bioscope')
		for sentence in bioscope_doc.getchildren():
			if sentence.get('id')==sentenceId:
				hedge_levels= get_bioscope_element_hedge_or_negation_levels(sentence,scope_type)

		return hedge_levels
		
	def get_bioscope_tokens(self,docId,sentenceId):
		"""
		Given a sentence, get the original file and tokenize it, using C{nltk.tokenize.TreebankWordTokenizer}). Returns a list of pairs property:value for each token
		@rtype: C{List}
		"""

		# Get the max nesting levels for the sentence 
		max_hedge_levels=self.get_max_nesting_level(docId,sentenceId,scope_type='speculation')
		hedge_scopes = ['O' for i in range(max_hedge_levels)]
		max_negation_levels=self.get_max_nesting_level(docId,sentenceId,scope_type='negation')
		negation_scopes = ['O' for i in range(max_negation_levels)]
		
		
		def includes_hedging_or_negation(element,xcope_id,scope_type):
			if element.tag=='cue' and element.get('type')==scope_type and element.get('ref')==xcope_id:
				return True
			else:
				for ch in element.getchildren():
					if includes_hedging_or_negation(ch,xcope_id,scope_type):
						return True
	
				return False
		
		
		def get_bioscope_element_spec_tags(element,hedge_cue_num,negation_cue_num,hedge_scopes,negation_scopes):
			
			""" 
			Given an element of the xml tree (C{xml.etree.ElementTree}), returns the Bioscope marks. If the node corresponds to a text, it tokenizes it.
			Adicionalmente, si es un texto, lo tokeniza.
			@type element: C{xml.etree.ElementTree}

			"""
		
			# Tokenize using the Penn Treebank tokenizer... 
			wt=nltk.tokenize.TreebankWordTokenizer()

			# Find each token's attributes
			hedge_cues=['O' for i in range(max_hedge_levels)]
			negation_cues=['O' for i in range(max_negation_levels)]
			if element.tag=='sentence':
				# At the begining of the sentence, the speculation mark is False, the negation mark is empty, and the scope list is also empty
				# La lista de scopes está vacía
				hedge_scopes=['O' for i in hedge_scopes]
				negation_scopes=['O' for i in negation_scopes]
				hedge_cues=['O' for i in hedge_cues]
				negation_cues=['O' for i in negation_cues]
			elif element.tag=='cue' and element.get('type')=='negation':
				# Found a negation cue
				pass
			elif element.tag=='cue' and element.get('type')=='speculation':
				# Starts a speculation block
				# Elements within this scope are marked as speculative
				pass
			elif element.tag=='xcope':
				# If i am in a speculation/negation scope, I still do not have a hedge cue
				
				# If it is a hedge scope, increase de nesting levelSi es un hedge de scope, entonces aumento un nivel de anidamiento
				if includes_hedging_or_negation(element,element.get('id'),scope_type='speculation'):
					hedge_cue_num=hedge_cue_num+1
					# New hedging level
					j=0
					for i in hedge_scopes:
						if i!='O':
							j=j+1
						else:
							# Substitute the first 'O' with a 'B'
							hedge_scopes[j]='B'
							break
					
				if includes_hedging_or_negation(element,element.get('id'),scope_type='negation'):
					negation_cue_num=negation_cue_num+1				
					# New negation level 
					j=0
					for i in negation_scopes:
						if i!='O':
							j=j+1
						else:
							negation_scopes[j]='B'
							break

			
			# If the text contains text, tokenize it and add the corresponding tags
			if element.text:
				element_text=wt.tokenize(element.text)
			else:
				element_text=[]
				
			element_tagged_text=[]
			
			first_token=True
			for elem in element_text:
				
				# Load the speculation mark values
				
				if hedge_cue_num>0 and element.get('type')=='speculation':
					if first_token:
						hedge_cues[hedge_cue_num-1]='B-SPECCUE'
						first_token=False
					else:
						hedge_cues[hedge_cue_num-1]='I-SPECCUE'
				else:
					hedge_cues=['O' for i in hedge_cues]
					
				# Load negation mark values
				if negation_cue_num>0  and element.get('type')=='negation':
					if first_token:
						negation_cues[negation_cue_num-1]='B-NEGCUE'
						first_token=False
					else:
						negation_cues[negation_cue_num-1]='I-NEGCUE'
				else:
					negation_cues=['O' for i in negation_cues]
					
				# Load scope marks 
				j=0
				hedge_scope_marks=[]
				for i in hedge_scopes:
					if i=='B':
						hedge_scope_marks.append('B-SPECXCOPE')
						hedge_scopes[j]='I'
					elif i=='I':
						hedge_scope_marks.append('I-SPECXCOPE')						
					else:
						hedge_scope_marks.append('O')	
					j=j+1


				# Load negation scope marks 
				j=0
				negation_scope_marks=[]
				for i in negation_scopes:
					if i=='B':
						negation_scope_marks.append('B-NEGXCOPE')
						negation_scopes[j]='I'
					elif i=='I':
						negation_scope_marks.append('I-NEGXCOPE')						
					else:
						negation_scope_marks.append('O')	
					j=j+1
					
			
				if not hedge_scope_marks:
					hedge_scope_marks=['O']

				if not negation_scope_marks:
					negation_scope_marks=['O']

				if not hedge_cues:
					hedge_cues=['O']
				
				if not negation_cues:
					negation_cues=['O']
					
					
				#print >> stderr, 'Anoto el texto ',elem, ' con el tag ',hedge_cues
				# Add the element to the tagged text
				element_tagged_text.append((elem,{'SpecCue':[h for h in hedge_cues],'NegCue':[h for h in negation_cues],'specXcope':hedge_scope_marks,'negXcope':negation_scope_marks}))
					
							
			
			# Process childen 
			j=0
			for ch in element.getchildren():
				element_tagged_text += get_bioscope_element_spec_tags(ch,hedge_cue_num,negation_cue_num,hedge_scopes,negation_scopes)
			
			# Process the text to the right of the tag
			if element.tail:
				element_tail=wt.tokenize(element.tail)
			else:
				element_tail=[]

			element_tagged_tail=[]
			
			
			# What appears to the right is never a speculation/negation mark
			hedge_cues=['O' for i in hedge_cues]
			negation_cues=['O' for i in negation_cues]
			
			# If the speculation scope ends, drop the las nesting level
			if includes_hedging_or_negation(element,element.get('id'),scope_type='speculation') and element.tag=='xcope':
				j=0
				for i in hedge_scopes:
					if i !='O':
						j=j+1
					else:
						hedge_scopes[j-1]='O'
						break
				# If at the end, assign True to the first one, because there is only one
				hedge_scopes[j-1]='O'
						
			# Same for speculation 
			if includes_hedging_or_negation(element,element.get('id'),scope_type='negation') and element.tag=='xcope':
				j=0
				for i in negation_scopes:
					if i !='O':
						j=j+1
					else:
						negation_scopes[j-1]='O'
						break
				negation_scopes[j-1]='O'
						
						

			# Load scope mark values
			j=0
			hedge_scope_marks=[]
			for i in hedge_scopes:
				if i=='B':
					hedge_scope_marks.append('B-SPECXCOPE')
					hedge_scopes[j]='I'
				elif i=='I':
					hedge_scope_marks.append('I-SPECXCOPE')						
				else:
					hedge_scope_marks.append('O')	
				j=j+1

			# Same for negation scope marks
			j=0
			negation_scope_marks=[]
			for i in negation_scopes:
				if i=='B':
					negation_scope_marks.append('B-NEGXCOPE')
					negation_scopes[j]='I'
				elif i=='I':
					negation_scope_marks.append('I-NEGXCOPE')						
				else:
					negation_scope_marks.append('O')	
				j=j+1


					
			if not hedge_scope_marks:
				hedge_scope_marks=['O']

			if not negation_scope_marks:
				negation_scope_marks=['O']
				
			if not hedge_cues:
				hedge_cues=['O']
				
							
			if not negation_cues:
				negation_cues=['O']
			
			
			for elem in element_tail:
				element_tagged_tail.append((elem,{'SpecCue':[h for h in hedge_cues],'NegCue':[h for h in negation_cues], 'specXcope':hedge_scope_marks,'negXcope':negation_scope_marks}))



			return element_tagged_text + element_tagged_tail
			
		
		# Read the bioscope file
		bioscope_doc=self.bioscope_files_corpus.xml(docId+'.bioscope')
		for sentence in bioscope_doc.getchildren():
			if sentence.get('id')==sentenceId:
				tokens=get_bioscope_element_spec_tags(sentence,hedge_cue_num=0,negation_cue_num=0, hedge_scopes=hedge_scopes, negation_scopes=negation_scopes)
		return tokens

def bioscope_get_text(xml_element):
	""" 
	Given a bioscope xml tree, extract the text, without the annotation marks
	@arg xml_element: XML for the Bioscope corpus
	@type xml_element: C{xml.etree.ElementTree}
	@rtype: C{String}
	"""

	if xml_element.text: 
		texto=xml_element.text
	else:
		texto=''

	if xml_element.tail and xml_element.tag != 'sentence':
		tail=xml_element.tail
	else:
		tail=''

	texto_hijos=[bioscope_get_text(ch) for ch in xml_element.getchildren()]
	res=''.join([texto]+texto_hijos+[tail])
	return res
				

def bioscope_retokenize(genia_words,bioscope_tokens):
	"""
	Given a list of words, resulting form the GENIA tagger tokenizer, and another, resulting from text tokenizing using C{nltk.tokenize.TreebankWordTokenizer()}, retokenizes the second one, to mache Genia tagging
	@arg genia_words: list of words from Genia Tagger tokenization
	@type genia_words: C{List}
	@arg bioscope_tokens: list of word from the C{nltk.tokenize.TreebankWordTokenizer()}
	@type bioscope_tokens: C{List}
	@return: bioscope_tokens, retokenizado
	@rtype: C{List}
	"""
	
	import warnings
	# Ignoro los warnings al convertir unicode, no quiero problemas
	warnings.simplefilter('ignore')

	for i in range(0,len(genia_words)):
		if i<len(bioscope_tokens):
			genia_word=genia_words[i][0]
			treebank_token=bioscope_tokens[i][0]
			
			if genia_word != treebank_token:
				# 0: brackets seem different, by the are just encoded following the PennTreebank annotation guidelines. Skip. 
				if treebank_token in ('(',')','[',']','{','}'):
					pass
				else:
					# 2: if the genia word mathces the bioscope word plus the following word, join them
					if i<len(bioscope_tokens)-1 and genia_word==treebank_token+bioscope_tokens[i+1][0]:
						bioscope_tokens[i]=(bioscope_tokens[i][0]+bioscope_tokens[i+1][0], bioscope_tokens[i][1]) 
						del(bioscope_tokens[i+1])
					# Caso 3: ... even three separated words
					elif i<len(bioscope_tokens)-2 and  genia_word==treebank_token+bioscope_tokens[i+1][0]+bioscope_tokens[i+2][0]:
						del(bioscope_tokens[i+1])
						del(bioscope_tokens[i+1])
					# Caso 4:... even four f**  
					elif i<len(bioscope_tokens)-3 and genia_word==treebank_token+bioscope_tokens[i+1][0]+bioscope_tokens[i+2][0]+bioscope_tokens[i+3][0]:
						bioscope_tokens[i]=(bioscope_tokens[i][0]+bioscope_tokens[i+1][0]+bioscope_tokens[i+2][0]+bioscope_tokens[i+3][0], bioscope_tokens[i][1]) 					
						del(bioscope_tokens[i+1])
						del(bioscope_tokens[i+1])
						del(bioscope_tokens[i+1])
	warnings.simplefilter('always')
	return bioscope_tokens
	

def gen_conll_file_hc(dbname,tablename,sentence_type,filename,xs,y,predicted_y):
	""" 
	Given a BIOSCOPE db table, generate the file for training/evaluation using CRF++
	The file is in CoNLL format (one line for each token, with attributes space separated, and the last one is the target class). Blank lines separate sentences
	@arg dbname: file for the database file 
	@type dbname:C{string}
	@arg tablename: table name
	@type tablename:C{string}
	@arg sentence_type: a string for SENTENCE_TYPE. If ALL, use every tuple
	@type sentence_type: C{string}
	@arg xs: list of attributes to generate. They must match the table's column name, and do not include the target class
	@type xs: List
	@arg y: Attribute indicating the target class
	@type y:List
	@arg predicted_y: Learned class (for evaluation)
	@type predicted_y: C{string}
	"""

	content=''	
	t0=time.clock()
	f=open(filename,'w+')
	conn= sqlite3.connect(dbname)	
	conn.text_factory = str
	conn.row_factory=sqlite3.Row
	c=conn.cursor()
	
	# Create the attribute list 
	cabezal_select=','.join(xs)
	cabezal_select=cabezal_select+','+y+' '
	if predicted_y:
		cabezal_select=cabezal_select+','+predicted_y+' '

	if sentence_type=='ALL':
		c.execute('select document_id,sentence_id,token_num, '+cabezal_select+' from '+tablename+' order by document_id,sentence_id,token_num')
	else:
		c.execute('select document_id,sentence_id,token_num, '+cabezal_select+' from '+tablename+' where sentence_type=?  order by document_id,sentence_id,token_num', (sentence_type,))	
	
	prev_sentence_id='-1'	
	in_scope=False
	for row in c:
		if (prev_sentence_id != row['sentence_id']):
			# Sentence end, leave a blank space, except for the first sentence
			if prev_sentence_id != '-1':					
				content=content+'\n'
			prev_sentence_id = row['sentence_id']
		for k in row.keys():
			value=row[k]		
			content=content+str(value)+'\t'

		# Delete las tab
		content=rstrip(content)
		content=content+'\n'	
		f.write(content)
		content=''
	f.close()
	c.close()
	
