#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# version = 0.9
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

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

# Functions
def printRule(text):
	if verbose:
		print("  " + text)

def printBold(text):
	if verbose:
		print('\033[1m' + text + '\033[0m')

def printError(expected, token, lexeme, num):
	print("\033[1;31m  Syntax Error:\033[0m expected \033[1m{0:5}\033[0m but \033[1m{1:5}\033[0m {2} given, line {3}".format(expected, token, lexeme, num))
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

num = 1

def target(stage, n=1):
	try:
		with open(filename, 'r', 1) as f:
			array = []
			count = 0

			errors = 0

			if stage == 1:
				if debug:
					print("#", "\t", "TOKEN", "\t\t", "LEXEME")
				elif not test and not logfile:
					print("TOKEN", "\t\t", "LEXEME")

				if logfile:
					log = open("pyrat.log", 'w')
					lexer(array, count, errors, f, n, stage, log)
				else:
					lexer(array, count, errors, f, n, stage)

			elif stage == 2:
				if checkRat("start", array, count, errors, f, n, stage):
					while statementList(array, count, errors, f, n, stage):
						pass
					if checkRat("end", array, count, errors, f, n, stage):
						try:
							token, lexeme = lexer(array, count, errors, f, n, stage)
							if lexeme != None:
								printError("end of file", token, lexeme, num)
						except TypeError: "EOF"


	except ValueError: "cannot open file"
	f.close()


def checkRat(pos, array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if lexeme == "$$":
		if pos == "start":
			printRule("<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$")
	else:
		printError("separator", token, lexeme, num)
	return True

def compound(array, count, errors, f, n, stage):
	printRule("<Compound> ::= { <Statement List> }")
	return statementList(array, count, errors, f, n, stage)

def statementList(array, count, errors, f, n, stage):
	printRule("<Statement List> ::= <Statement> <Statement List>")
	return statement(array, count, errors, f, n, stage)
	#	print("==> yes 3")
	#return True

def statement(array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "identifier":
		return assign(array, count, errors, f, n, stage)
	elif token == "separator" and lexeme == "{":
		return compound(array, count, errors, f, n, stage)
	elif token == "keyword" and lexeme == "if":
		return ifCond(array, count, errors, f, n, stage)
	elif token == "keyword" and lexeme == "read":
		return readCond(array, count, errors, f, n, stage)
	elif token == "keyword" and lexeme == "return":
		return returnCond(array, count, errors, f, n, stage)
	elif token == "keyword" and lexeme == "while":
		return whileCond(array, count, errors, f, n, stage)
	elif token == "keyword" and lexeme == "write":
		return writeCond(array, count, errors, f, n, stage)
	elif token == "separator" and lexeme == "}":
		return False
	else:
		printError("<Statement>", token, lexeme, num)


def assign(array, count, errors, f, n, stage):
	printRule("<Statement> ::= <Assign>")
	printRule("<Assign> ::= <Identifier> = <Expression>")
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "operator" and lexeme == "=":
		return expression(array, count, errors, f, n, stage)
	else:
		printError("=", token, lexeme, num)

def expression(array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "identifier":
		printRule("<Expression> ::= <Term> <Expression Prime>")
		printRule("<Term> := <Factor> <Term Prime>")
		printRule("<Factor> := <Identifier>")
		return expressionPrime(array, count, errors, f, n, stage)
	else:
		printError("identifier", token, lexeme, num)

def expressionPrime(array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "operator" and (lexeme == "+" or lexeme == "-"):
		printRule("<Term Prime> := ɛ")
		printRule("<Expresion Prime> := + <Term> <Expression Prime>")
		return term(array, count, errors, f, n, stage)
	else:
		printError("+ or -", token, lexeme, num)

def term(array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "identifier":
		printRule("<Term> := <Factor> <Term Prime>")
		printRule("<Factor> := <Identifier>")
		return termPrime(array, count, errors, f, n, stage)
	else:
		printError("identifier", token, lexeme, num)

def termPrime(array, count, errors, f, n, stage):
	token, lexeme = lexer(array, count, errors, f, n, stage)
	printBold("Token: {0:15} Lexeme: {1}".format(token, lexeme))
	if token == "separator" and lexeme == ";":
		printRule("<Term Prime> := ɛ")
		printRule("<Expresion Prime> := ɛ")
	else:
		printError(";", token, lexeme, num)

	return True


def lexer(array, count, errors, f, n, stage, log=None):

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
			global num
			num += 1
		else:
			token, lexeme = fsm(f, char, array)

			if lexeme == None:
				if debug:
					print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format("", "", char, "", "stack: ", array))
			elif test:
				errors = compare_token(count, token, lexeme, errors, n)
				count += 1
			elif debug:
				print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format(num, "", token, lexeme, "stack: ", array))
			elif logfile:
				log.write("{0:15} {1}\n".format(token, lexeme))
			elif stage > 1:
				return token, lexeme
			else:
				print("{0:15} {1}".format(token, lexeme))

	if errors > 0:
		print("ARRRR: Unit test", n, "failed")


def fsm(f, char, array):
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
		f = open(filename, 'w')
		f.write(testcase)
	except ValueError: "cannot write file"
	f.close()

	print(testcase, "\n================")
	target(1, n)


def compare_token(count, token, lexeme, errors, n):
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
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [-d|-l|-s] [file]")
	print("USAGE: pyrat.py --test")
	exit(1)

# Check file exists
if filename == "--test" or filename == "-t":
	option = "--test"
	filename = "pyrat.tmp"
elif filename == "-h" or filename == "--help":
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [-d|-l|-s] [file]")
	print("USAGE: pyrat.py --test")
	exit(1)
elif not os.path.isfile(filename):
	print("ARRRR: Argument must be a valid file name")
	exit(2)

# Parse parameters
if option == "all":
	print("==> running lexer")
	target(1)
	print("==> saved to pyrat.log")
elif option == "--debug" or option == "-d":
	debug = True
	target(1)
elif option == "--lexer" or option == "-l":
	logfile = False
	target(1)
elif option == "--syntaxer" or option == "-s":
	logfile = False
	verbose = True
	target(2)
elif option == "--test" or option == "-t":
	test = True
	unit_test(1)
	unit_test(2)
	unit_test(3)
	unit_test(4)
	os.remove(filename)
else:
	print("ARRRR: unknown function call")
	exit(3)
