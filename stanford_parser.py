# -*- coding: utf-8 -*- 
import subprocess
import shlex
import codecs
import tempfile
"""
Module for working with the Stanford Parser. Every function here assumes you have installed the Stanford Parser and set the CLASSPATH to:
Something like...
export STANFORD_PARSER=$HOME/bin/stanford-parser-full-2014-01-04
export CLASSPATH=$STANFORD_PARSER/stanford-parser.jar:$STANFORD_PARSER/stanford-parser-3.3.1-models.jar
"""
	
def lexicalized_parser_parse(sentences,model='englishPCFG',output='penn'):
	""" 
	Given a list of sentences, it parses them with the Lexicalized Stanford Parser, and return the results.  
	Uses the englishPCFG.ser.gz
	
	@arg sentences: List of C{String} containing the sentences  
	@arg model: model to use. For the moment, the only valid value is 'englishPCFG' 
	@arg output: type of output for the Stanford Parser. Valid values: penn (default), basicDependencies (coNLL dependencies). When called with the 'basicDependencies' value
	it also add an outputFormatOptions valued with 'typedDependencies'
	"""


	# Build a text for parsing. Just one sentence for each line
	text='\n'.join(sentences)
	
	command_line='java -mx1000m edu.stanford.nlp.parser.lexparser.LexicalizedParser -sentences newline -tagSeparator / -tokenizerFactory edu.stanford.nlp.process.WhitespaceTokenizer -tokenizerMethod newCoreLabelTokenizerFactory -outputFormat - -outputFormatOptions - modelFile -'
	args=shlex.split(command_line)

	# Incorporate the model file
	if model=='englishPCFG':
		model_file='edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'
	args[-2]=model_file

	# Incorporate  the output format
	if output=='penn':
		# No outputFormatOptions
		del args[-3]
		del args[-3]
		# Specify outputFormat	
		args[-3]='penn'
	elif output=='basicDependencies':
		# Specify outputFormat and outputFormatOptions
		args[-3]='basicDependencies'
		args[-5]='typedDependencies'


	# Create a process and read its output
	p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	(result,stderrdata)=p.communicate(input=text)

	# Return a list of analyzed sentences, with the specified format
	return result.split('\n\n')[:-1]
	
def lexicalized_parser_tag(sentences,model='englishPCFG'):
	""" 
	Given a list of sentences, parse them with the Lexicalized Stanford Parser, and return their pos_tags.
	I guess I should better use the Stanford Tagger for performance decisions, but this is pretty direct
	Uses the englishPCFG.ser.gz
	
	@arg sentences: List of C{String} containing the sentences  
	@model: model to use. For the moment, the only valid value is 'englishPCFG' 
	"""

	# Build a text for parsing. Just one sentence for each line
	text='\n'.join(sentences)
	

	command_line='java -mx1000m edu.stanford.nlp.parser.lexparser.LexicalizedParser -sentences newline -escaper edu.stanford.nlp.process.PTBEscapingProcessor -tagSeparator / -outputFormat wordsAndTags modelFile -'
	args=shlex.split(command_line)

	# Create a temporary file for storing the text. Pass it to the command line as an argument
	# Last argument
	#source=tempfile.NamedTemporaryFile(delete=False)
	#source.write(text)
	#source.close()
	#args[-1]=source.name

	# Incorporate the model file
	if model=='englishPCFG':
		model_file='edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'
	args[-2]=model_file

	# Create a temporary file for the results	
	#target=tempfile.NamedTemporaryFile(delete=False)
	#target_name=target.name
	p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
	(result,stderrdata)=p.communicate(input=text)
	#target.close()
	#target=open(target_name,'r')
	#result=target.read()
	#target.close()

	return result.split('\n\n')[:-1]

if __name__ == '__main__':
	parsed=lexicalized_parser_parse(['This is a demo text!','And this is another sentence', 'This an utf-8 encoded: cámara'],output='penn')
	for p in parsed:
		print p 

	tagged=lexicalized_parser_tag(['This is a demo text!','And this is another sentence', 'This an utf-8 encoded: cámara'])
	for t in tagged:
		print t
