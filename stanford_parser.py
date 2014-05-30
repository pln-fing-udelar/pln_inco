# -*- coding: utf-8 -*- 
import subprocess
import shlex
import codecs
import tempfile
"""
Working with the Stanford Parser. Every function here assumes you have installed the Stanford Parser and set the CLASSPATH to:
export STANFORD_PARSER=$HOME/bin/stanford-parser-full-2014-01-04
export CLASSPATH=$STANFORD_PARSER/stanford-parser.jar:$STANFORD_PARSER/stanford-parser-3.3.1-models.jar

TODO: utf-8!
"""
	
def lexicalized_parser_parse(sentences,model='englishPCFG',output='penn'):
	""" 
	Given a list of sentences, parse them with the Lexicalized Stanford Parser, and return the results.
	Uses the englishPCFG.ser.gz
	
	@arg sentences: List of C{String} containing the sentences  
	@model: model to use. For the moment, the only valid value is 'englishPCFG' 
	@output: type of output for the Stanford Parser. Valid values: penn (default), dependencies
	"""

	# Build a text for parsing. Just one sentence for each line
	text='\n'.join(sentences)
	

#	command_line='java -mx1000m edu.stanford.nlp.parser.lexparser.LexicalizedParser -sentences newline -tokenized -escaper edu.stanford.nlp.process.PTBEscapingProcessor -tagSeparator / -outputFormat -  - -'
	command_line='java -mx1000m edu.stanford.nlp.parser.lexparser.LexicalizedParser -sentences newline -escaper edu.stanford.nlp.process.PTBEscapingProcessor -tagSeparator / -outputFormat -  - -'
	args=shlex.split(command_line)

	# Create a temporary file for storing the text. Pass it to the command line as an argument
	source=tempfile.NamedTemporaryFile(delete=False)
	source.write(text)
	source.close()
	args[-1]=source.name

	# Incorporate the model file
	if model=='englishPCFG':
		model_file='edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'
	args[-2]=model_file

	# Incorporate  the output format
	args[-3]=output



	# Create a temporary file for the results	
	target=tempfile.NamedTemporaryFile(delete=False)
	target_name=target.name
	p=subprocess.Popen(args,stdout=target)
	p.wait()
	target.close()
	target=open(target_name,'r')
	result=target.read()
	target.close()

	return result.split('\n\n')[:-1]
	
if __name__ == '__main__':
	parsed=lexicalized_parser_parse(['This is a demo text!','And this is another sentence', 'This an utf-8 encoded: cámara'],output='typedDependencies')
	for p in parsed:
		print parsed[0]
