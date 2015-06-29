#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# version = 1.1
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

# Defaults
output = "rat15su.log"
temp = "pyrat.tmp"

# Flags
debug = False
test = False
logfile = True
verbose = False

# REGEX
keyword = r"boolean|else|false|fi|function|if|integer|read|real|return|true|while|write"
real = r"^[0-9]+\.[0-9]+$"
integer = r"^[0-9]+$"
identifier = r"^[a-z]([0-9]|[a-z])*[a-z]$|^[a-z]$"
operator = r"[></]|[+*-]"
separator = r"[,;\(\){}]"
symbols = r"[></]|[+*-]|[,;\(\){}]"

# Global
array = []
count = 0
errors = 0
num = 1
n = 0
stage = 0

# Functions
def printUsage():
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [-d|-l|-s] [file]")
	print("USAGE: pyrat.py [--test|--rules]")

def printToken(text):
	global logfile, stage
	if stage == 1:
		if logfile:
			log.write(text + "\n")
		elif verbose:
			print(text)

def banner():
	text = "\n===========================\n"
	global logfile
	if logfile:
		log.write(text + "\n")
	elif verbose:
		print(text)

def printRule(text):
	global logfile
	if logfile:
		log.write("  " + text + "\n")
	elif verbose:
		print("  " + text)

def printBold(token, lexeme):
	global logfile
	if logfile:
		try:
			log.write("Token: {0:15} Lexeme: {1}\n".format(token, lexeme))
		except TypeError: "blank"
	elif verbose:
		try:
			print("\033[1mToken: {0:15} Lexeme: {1}\033[0m".format(token, lexeme))
		except TypeError: "blank"

def printError(expected, token, lexeme):
	global logfile
	if logfile:
		try:
			print("Syntax Error: expected {0:5} but {1:5} {2} given, line {3}\n".format(expected, token, lexeme, num))
		except TypeError: "blank"
	else:
		try:
			print("\033[1;31m  Syntax Error:\033[0m expected \033[1m{0:5}\033[0m but \033[1m{1:5}\033[0m {2} given, line {3}".format(expected, token, lexeme, num))
		except TypeError: "blank"
	#exit(10)
	return False

def getToken(n):
	# State 1, 2, 3 are non-accepting states
	if n == 1 or n == 2 or n == 3:
		token = None
	elif n == 4:
		token = "real"
	elif n == 5:
		token = "integer"
	elif n == 6:
		token = "separator"
	elif n == 7:
		token = "operator"
	elif n == 8:
		token = "keyword"
	elif n == 9:
		token = "identifier"
	else:
		token = "unknown"
	return token

def target(n=1):
	try:
		with open(filename, 'r', 1) as f:

			global array, count, errors
			del array[:]
			count = 0
			errors = 0

			if stage == 1:
				if debug:
					print("#", "\t", "TOKEN", "\t\t", "LEXEME")
				elif not test and not logfile:
					print("TOKEN", "\t\t", "LEXEME")
				lexer(f, n)

			elif stage == 2:
				if checkRat("start", f):
					while statementList(f):
						pass
					if checkRat("end", f):
						try:
							token, lexeme = getLex(f)
							if lexeme != None:
								printError("end of file", token, lexeme)
						except TypeError: "EOF"


	except ValueError: "cannot read file"
	f.close()

def getLex(f):
	token = None
	lexeme = None
	try:
		token, lexeme = lexer(f)
	except TypeError: "EOF"
	return token, lexeme

def checkRat(pos, f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if lexeme == "$$":
		if pos == "start":
			printRule("<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$")
		return True
	else:
		printError("separator", token, lexeme)

def statementList(f):
	printRule("<Statement List> ::= <Statement> <Statement List>")
	while statement(f):
		pass

def statement(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "identifier":
		return assign(f)
	elif token == "separator" and lexeme == "{":
		return compound(f)
	elif token == "keyword" and lexeme == "if":
		return ifCond(f)
	elif token == "keyword" and lexeme == "read":
		return readCond(f)
	elif token == "keyword" and lexeme == "return":
		return returnCond(f)
	elif token == "keyword" and lexeme == "while":
		return whileCond(f)
	elif token == "keyword" and lexeme == "write":
		return writeCond(f)
	elif token == "separator" and lexeme == "}":
		return True
	else:
		printError("<Statement>", token, lexeme)

def assign(f):
	printRule("<Statement> ::= <Assign>")
	printRule("<Assign> ::= <Identifier> = <Expression>")
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "operator" and lexeme == "=":
		if expression(f):
			return termPrime(f)
	else:
		printError("=", token, lexeme)

def compound(f):
	printRule("<Compound> ::= { <Statement List> }")
	return statementList(f)

def ifCond(f):
	printRule("<If> ::= if ( <Condition> ) <Statement> fi |")
	printRule("         if ( <Condition> ) <Statement> else <Statement> fi")
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "separator" and lexeme == "(":
		if conditionPrime(f):
			if statement(f):
				token, lexeme = getLex(f)
				printBold(token, lexeme)
				if token == "keyword" and lexeme == "fi":
					return False
				elif token == "keyword" and lexeme == "else":
					if statement(f):
						token, lexeme = getLex(f)
						printBold(token, lexeme)
						if token == "keyword" and lexeme == "fi":
							return True
		return True
	else:
		printError("(", token, lexeme)

def conditionPrime(f):
	if condition(f):
		token, lexeme = getLex(f)
		printBold(token, lexeme)
		if token == "separator" and lexeme == ")":
			return False
		else:
			printError(")", token, lexeme)

def condition(f):
	printRule("<Condition> ::= <Expression> <Relop> <Expression>")
	if expression(f):
		if relop(f):
			return True
	return False

def readCond(f):
	return

def returnCond(f):
	return

def whileCond(f):
	return

def writeCond(f):
	return

def relop(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if lexeme == "==" or lexeme == "!=" or lexeme == ">" or lexeme == "<":
		return expression(f)
	else:
		printError("== or != or > or <", token, lexeme)

def expression(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "identifier":
		printRule("<Expression> ::= <Term> <Expression Prime>")
		printRule("<Term> := <Factor> <Term Prime>")
		printRule("<Factor> := <Identifier>")
		return expressionPrime(f)
	else:
		printError("identifier", token, lexeme)

def expressionPrime(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "operator" and (lexeme == "+" or lexeme == "-"):
		printRule("<Term Prime> := ɛ")
		printRule("<Expresion Prime> := + <Term> <Expression Prime>")
		return term(f)
	else:
		printError("+ or -", token, lexeme)

def term(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "integer":
		printRule("<Term> := <Factor> <Term Prime>")
		printRule("<Factor> := <Integer>")
		#return termPrime(f)
		return True
	elif token == "identifier":
		printRule("<Term> := <Factor> <Term Prime>")
		printRule("<Factor> := <Identifier>")
		#return termPrime(f)
		return True
	else:
		printError("identifier", token, lexeme)

def termPrime(f):
	token, lexeme = getLex(f)
	printBold(token, lexeme)
	if token == "separator" and lexeme == ";":
		printRule("<Term Prime> := ɛ")
		printRule("<Expresion Prime> := ɛ")
	else:
		printError(";", token, lexeme)
	return True


def lexer(f, n=0):
	global array, count, errors, num, stage
	run = True

	# Read file one character at a time
	while run:
		if array:
			char = array[-1]
			array.pop()
		else:
			char = f.read(1)
			char = char.lower()

		if not char:
			break
		elif char == '\n':
			num += 1
		else:
			token, lexeme = fsm(f, char)
			if lexeme == None:
				if debug:
					print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format("", "", char, "", "stack: ", array))
			elif test:
				errors = compare_token(count, token, lexeme, n)
				count += 1
			elif stage > 1:
				return token, lexeme
			elif debug:
				print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format(num, "", token, lexeme, "stack: ", array))
			else:
				printToken("{0:15} {1}".format(token, lexeme))

	if errors > 0:
		print("ARRRR: Unit test", n, "failed")


def fsm(f, char):
	global array
	token = None
	lexeme = None
	state = 0

	while state <= 3:
		# Ad-hoc
		if state == 0:
			if re.match(separator, char):
				lexeme = char
				state = 6
			elif re.match(operator, char):
				lexeme = char
				state = 7
			elif re.match(r"[!|=]", char):
				array.append(char)
				state = 1
			elif char == "$":
				array.append(char)
				state = 1
			elif re.match(r"[0-9]|\.", char):
				array.append(char)
				state = 2
			elif re.match(r"[a-z]", char):
				array.append(char)
				state = 3
			elif re.match(r"\.", char):
				array.append(char)
				state = 10
			elif char.isspace():
				del array[:]
				state = 10
			else:
				lexeme = char
				del array[:]
				state = 10
		# Finite State Machine (2 char operator or separator)
		elif state == 1:
			char = f.read(1)
			char = char.lower()
			char = char.lower()
			stack = ''.join(str(e) for e in array)
			if stack+char == "$$":
				lexeme = stack+char
				array.pop()
				state = 6
			elif stack == "$" and char != "$":
				lexeme = stack
				array.pop()
				array.append(char)
				state = 11
			elif re.match(r"[!|=]", stack) and char == "=":
				lexeme = stack+char
				array.pop()
				state = 7
			elif stack == "=" and char != "=":
				lexeme = stack
				array.pop()
				array.append(char)
				state = 7
			else:
				lexeme = stack
				del array[:]
				state = 11
		# Finite State Machine (real or integer)
		elif state == 2:
			char = f.read(1)
			char = char.lower()
			stack = ''.join(str(e) for e in array)
			if re.match(real, stack) and not re.match(r"[0-9]", char):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 4
			elif re.match(integer, stack) and not re.match(r"[0-9]", char) and (re.match(symbols, char) or char.isspace()):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 5
			elif not char.isspace():
				array.append(char)
				state = 2
			else:
				lexeme = stack
				del array[:]
				state = 12
		# Finite State Machine (keyword or identifier)
		elif state == 3:
			char = f.read(1)
			char = char.lower()
			stack = ''.join(str(e) for e in array)
			if re.match(keyword, stack) and not re.match(r"[a-z]", char):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 8
			elif re.match(identifier, stack) and not re.match(r"[0-9]|[a-z]", char) and (re.match(symbols, char) or char.isspace()):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 9
			elif not char.isspace():
				array.append(char)
				state = 3
			else:
				lexeme = stack
				del array[:]
				state = 13

		if debug and not char.isspace():
			print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format("", "=> ", char, "", "stack: ", array))

	token = getToken(state)

	return token, lexeme

def unit_test(n):
	print("==> running unit test", n)

	if n == 1:
		testcase = """
while (fahr < upper) a = 23.00;"""
	elif n == 2:
		testcase = """
$$
function meaningOf(integer)
{
	if(integer == 42)
		return true
	else
		return false
	fi
}
$$"""
	elif n == 3:
		testcase = """
$$
function convert(fahr integer)
{
	return 5*(fahr-32)/9;
}

$$
	integer	low, high, step;

	read(low, high, step);
	while(low < high)
	{
		write(low);
		write(convert(low));
		low = low + step;
	}
$$"""
	elif n == 4:
		testcase = """
        Function 000 
   (  ) ;   :
 {  } int  IDs     boolean, rEAL :=  begin end 
  if  (Condition) else Statement fi  while   do 
 return; read write
  =     !=       <<> ==      + -//  *  $$
123.000 0.0 Rat11SS
true     false     axy123r  a
&  123abc .123  !  a_x   a123 123.

"""

	try:
		f = open(temp, 'w')
		f.write(testcase)
	except ValueError: "cannot write file"
	f.close()

	print(testcase, "\n================")
	global stage
	stage = 1
	target(n)


def compare_token(count, token, lexeme, n):
	if n == 1:
		token_unit = ['keyword', 'separator', 'identifier', 'operator', 'identifier',\
					  'separator', 'identifier', 'operator', 'real', 'separator']
		lexeme_unit = ['while', '(', 'fahr', '<', 'upper', ')', 'a', '=', '23.00', ';']
	elif n == 2:
		token_unit = ['separator', 'keyword', 'identifier', 'separator', 'keyword',\
					  'separator', 'separator', 'keyword', 'separator', 'keyword',\
					  'operator', 'integer', 'separator', 'keyword', 'keyword', 'keyword',\
					  'keyword', 'keyword', 'keyword', 'separator', 'separator']
		lexeme_unit = ['$$', 'function', 'meaningof', '(', 'integer', ')', '{', 'if', '(',\
					  'integer', '==', '42', ')', 'return', 'true', 'else', 'return', 'false',\
					  'fi', '}', '$$']
	elif n == 3:
		token_unit = ['separator', 'keyword', 'identifier', 'separator', 'identifier', 'keyword',\
					  'separator', 'separator', 'keyword', 'integer', 'operator', 'separator',\
					  'identifier', 'operator', 'integer', 'separator', 'operator', 'integer', \
					  'separator', 'separator', 'separator', 'keyword', 'identifier', 'separator',\
					  'identifier', 'separator', 'identifier', 'separator', 'keyword', 'separator',\
					  'identifier', 'separator', 'identifier', 'separator', 'identifier', 'separator', \
					  'separator', 'keyword', 'separator', 'identifier', 'operator', 'identifier',\
					  'separator', 'separator', 'keyword', 'separator', 'identifier', 'separator',\
					  'separator', 'keyword', 'separator', 'identifier', 'separator', 'identifier',\
					  'separator', 'separator', 'separator', 'identifier', 'operator', 'identifier',\
					  'operator', 'identifier', 'separator', 'separator', 'separator']
		lexeme_unit = ['$$', 'function', 'convert', '(', 'fahr', 'integer', ')', '{', 'return',\
					   '5', '*', '(', 'fahr', '-', '32', ')', '/', '9', ';', '}', '$$', 'integer',\
					   'low', ',', 'high', ',', 'step', ';', 'read', '(', 'low', ',', 'high', ',', \
					   'step', ')', ';', 'while', '(', 'low', '<', 'high', ')', '{', 'write', '(', 'low',\
					   ')', ';', 'write', '(', 'convert', '(', 'low', ')', ')', ';', 'low', '=', 'low',\
					   '+', 'step', ';', '}', '$$']
	elif n == 4:
		token_unit = ['keyword', 'integer', 'separator', 'separator', 'separator', 'unknown', 'separator',\
					  'separator', 'identifier', 'identifier', 'keyword', 'separator', 'keyword', 'unknown',\
					   'operator', 'identifier', 'identifier', 'keyword', 'separator', 'identifier', 'separator',\
					   'keyword', 'identifier', 'keyword', 'keyword', 'identifier', 'keyword', 'separator',\
					   'keyword', 'keyword', 'operator', 'operator', 'operator', 'operator', 'operator', 'operator',\
					   'operator', 'operator', 'operator', 'operator', 'operator', 'separator', 'real', 'real',\
					   'identifier', 'keyword', 'keyword', 'identifier', 'identifier', 'unknown', 'unknown', 'unknown',\
					   'unknown', 'unknown', 'unknown', 'unknown' ]
		lexeme_unit = ['function', '000', '(', ')', ';', ':', '{', '}', 'int', 'ids', 'boolean', ',',\
					   'real', ':', '=', 'begin', 'end', 'if', '(', 'condition', ')', 'else', 'statement', 'fi',\
					   'while', 'do', 'return', ';', 'read', 'write', '=', '!=', '<', '<', '>', '==', '+',\
					   '-', '/', '/', '*', '$$', '123.000', '0.0', 'rat11ss', 'true', 'false', 'axy123r', 'a',\
					   '&', '123abc', '.123', '!', 'a_x', 'a123', '123.']
	else:
		print("ARRRR: Invalid test case")
		exit(4)

	if len(token_unit) > count and len(lexeme_unit) > count:
		if token_unit[count] == token and lexeme_unit[count] == lexeme:
			status = "OK"
		else:
			status = "FAIL"
			global errors
			errors += 1

		print("{0:10} {1:10} {2:15} {3:10} {4}".format(status, token_unit[count], lexeme_unit[count], token, lexeme))
	else:
		print("==> FATAL ERROR: unexpected EOF")
		exit(5)

	return errors

# Sanity checks
option = "all"
if len(sys.argv) == 3:
	option = sys.argv[1]
	filename = sys.argv[2]
elif len(sys.argv) == 2:
	filename = sys.argv[1]
else:
	printUsage()
	exit(1)

# Check file exists
if re.match(r"\-t|\-r|\-\-test|\-\-rules", option) and len(sys.argv) > 2:
	printUsage()
	exit(1)

if filename == "--test" or filename == "-t":
	filename = temp
	option = "--test"
elif filename == "--test2" or filename == "-tt":
	filename = temp
	option = "--test2"
elif filename == "-h" or filename == "--help":
	printUsage()
	exit(1)
elif not os.path.isfile(filename):
	print("ARRRR: Argument must be a valid file name")
	exit(2)

# Write to file
if logfile:
	try:
		log = open(output, 'w')
	except ValueError: "cannot write file"

# Parse parameters
if option == "all":
	print("==> running lexer")
	stage = 1
	target()
	banner()
	print("==> running syntaxer")
	stage = 2
	target()
	print("==> saved to " + output)
elif option == "--debug" or option == "-d":
	debug = True
	stage = 1
	target()
elif option == "--lexer" or option == "-l":
	logfile = False
	verbose = True
	stage = 1
	target()
elif option == "--syntaxer" or option == "-s":
	logfile = False
	verbose = True
	stage = 2
	target()
elif option == "--test" or option == "-t":
	test = True
	unit_test(1)
	unit_test(2)
	unit_test(3)
	unit_test(4)
	os.remove(temp)
elif option == "--rules" or option == "-r":
	test = True
	verbose = True
	unit_test(1)
	unit_test(2)
	unit_test(3)
	unit_test(4)
	os.remove(temp)
else:
	print("ARRRR: unknown function call")
	exit(3)
