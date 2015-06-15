#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# version = 0.6
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

debug = False
test = False
logfile = True

# REGEX
keyword=r"(boolean|else|false|fi|function|if|integer|read|real|return|true|while|write)"
real=r"[0-9]+.[0-9]+"
integer=r"^[0-9]+"
identifier=r"[a-z]|([a-z]([0-9]|[a-z])+[a-z])"
operator=r"[><+*-/]"
separator=r"[,;(){}]"

# Functions
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

def readfile(stage, n=1):
	try:
		with open(filename, 'r', 1) as f:
			if stage > 0:
				array = []
				count = 0
				num = 1

				if debug:
					print("#", "\t", "TOKEN", "\t\t", "LEXEME")
				elif not test and not logfile:
					print("TOKEN", "\t\t", "LEXEME")

				if logfile:
					log = open("pyrat.log", 'w')

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
						token, lexeme = lexer(f, char, array, num)

						if test:
							if(lexeme != None):
								compare_token(count, token, lexeme, n)
								count += 1
						elif debug:
							if(lexeme != None):
								print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format(num, "", token, lexeme, "stack: ", array))
							else:
								print("{0:2} {1:4} {2:15} {3:10} {4:10} {5}".format("", "", char, "", "stack: ", array))
						elif logfile:
							if(lexeme != None):
								log.write("{0:15} {1}\n".format(token, lexeme))
						else:
							if(lexeme != None):
								print("{0:15} {1}".format(token, lexeme))


	except ValueError: "cannot open file"
	f.close()

def lexer(f, char, array, num):
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
			elif re.match(r"[0-9]", char):
				array.append(char)
				state = 2
			elif re.match(r"[a-z]", char):
				array.append(char)
				state = 3
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
			elif char.isspace():
				del array[:]
				state = 11
			else:
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
			elif re.match(integer, stack) and not re.match(r"[0-9]|\.", char):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 5
			elif re.match(r"[0-9]|\.", char):
				array.append(char)
				state = 2
			elif char.isspace():
				del array[:]
				state = 12
			else:
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
			elif re.match(identifier, stack) and not re.match(r"[a-z]", char):
				lexeme = stack
				del array[:]
				array.append(char)
				state = 9
			elif re.match(r"[0-9]|[a-z]", char):
				array.append(char)
				state = 3
			elif char.isspace():
				del array[:]
				state = 13
			else:
				del array[:]
				state = 13

	token = getToken(state)

	return token, lexeme

def unit_test(n):
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

	try:
		f = open(filename, 'w')
		f.write(testcase)
	except ValueError: "cannot write file"
	f.close()
	print(testcase, "\n================")
	readfile(1, n)

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
	else:
		print("ARRRR: Invalid test case")
		exit(4)

	if len(token_unit) > count and len(lexeme_unit) > count:
		if token_unit[count] == token and lexeme_unit[count] == lexeme:
			status = "OK"
		else:
			status = "FAIL"

		print("{0:10} {1:10} {2:15} {3:10} {4}".format(status, token_unit[count], lexeme_unit[count], token, lexeme))
	else:
		print("==> FATAL ERROR: unexpected EOF")
		exit(5)

# Sanity checks
option = "all"
if len(sys.argv) == 3:
	option = sys.argv[1]
	filename = sys.argv[2]
elif len(sys.argv) == 2:
	filename = sys.argv[1]
else:
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [--debug|--lexer] [file]")
	print("USAGE: pyrat.py --test")
	exit(1)

# Check file exists
if filename == "--test" or filename == "-t":
	option = "--test"
	filename = "pyrat.tmp"
elif not os.path.isfile(filename):
	print("ARRRR: Argument must be a valid file name")
	exit(2)

# Parse parameters
if option == "all":
	print("==> running lexer")
	readfile(1)
	print("==> saved to pyrat.log")
elif option == "--debug" or option == "-d":
	debug = True
	readfile(1)
elif option == "--lexer" or option == "-l":
	logfile = False
	readfile(1)
elif option == "--test" or option == "-t":
	test = True
	print("==> running unit test 1")
	unit_test(1)
	print("\n==> running unit test 2")
	unit_test(2)
	print("\n==> running unit test 3")
	unit_test(3)
	os.remove(filename)
else:
	print("ARRRR: unknown function call")
	exit(3)
