#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

# REGEX
keyword=r"(boolean|else|false|fi|function|if|integer|read|real|return|true|while|write)"
real=r"[0-9]+.[0-9]+"
integer=r"[0-9]+"
identifier=r"[a-z]|([a-z]([0-9]|[a-z])+[a-z])"
operator=r"[><+/]"
separator=r"[,;(){}]"
debug = False

# Functions
def getToken(n):
	token = "------"
	if n == 1:
		token = "keyword"
	elif n == 2:
		token = "operator"
	elif n == 3:
		token = "separator"
	elif n == 4:
		token = "real\t"
	elif n == 5:
		token = "integer"
	elif n == 6:
		token = "identifier"
	elif n == 7:
		token = "unknown"
	return token

def fsm(state, char, array):
	# Keywords
	stack = ''.join(str(e) for e in array)
	if re.match(keyword, stack):
		del array[:]
		if not char.isspace():
			array.append(char)
		return 1, stack
	elif re.match(keyword, stack+char):
		del array[:]
		return 1, stack+char
	# Real
	elif re.match(real, stack) and not re.match(r"[0-9]", char):
		del array[:]
		if not char.isspace():
			array.append(char)
		return 4, stack
	# Integer
	elif re.match(integer, stack) and not re.match(r"[0-9]|.", char):
		del array[:]
		if not char.isspace():
			array.append(char)
		return 5, stack
	# Identifier
	elif re.match(identifier, stack) and not re.match(r"[a-z]", char):
		del array[:]
		if not char.isspace():
			array.append(char)
		return 6, stack
	# Operators
	elif re.match(operator, stack):
		array.pop()
		return 2, stack
	elif re.match(operator, char):
		return 2, char
	elif re.match(r"[!|=]", stack) and char == "=":
		array.pop()
		return 2, stack+char
	elif stack == "=" and char != "=":
		array.pop()
		return 2, stack
	# Separators
	elif re.match(separator, stack):
		array.pop()
		return 3, stack
	elif re.match(separator, char):
		return 3, char
	elif stack == "$" and char == "$":
		array.pop()
		return 3, stack+char
	# Whitespace
	elif char.isspace():
		#print("%%%%%%%%")
		del array[:]
		return 0, None
	# Unknown
	else:
		if not char.isspace():
			array.append(char)
		return 0, char

def lexer():
	try:
		f = open(filename, 'r')
	except ValueError: "cannot open file"

	print("#", "\t", "TOKEN", "\t\t", "LEXEME")
	token = "unknown"
	num = 0
	state = 0
	char = []
	array = []

	for line in f:
		num += 1
		line = line.rstrip()
		line = line.lower()

		for i in range(len(line)):
			char = line[i]

			state, lexeme = fsm(state, char, array)
			token = getToken(state)

			if debug:
				if(token != "------"):
					print(num, "\t", token, "\t", lexeme, "\t\tstack: ", array)
				else:
					print("\t\t\t", char, "\t\tstack: ", array)
			else:
				if(token != "------"):
					print(num, "\t", token, "\t", lexeme)

	f.close()


# Sanity checks
option = "all"
if len(sys.argv) == 3:
	option = sys.argv[1]
	filename = sys.argv[2]
elif len(sys.argv) == 2:
	filename = sys.argv[1]
else:
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [file] [function]")
	exit(1)

# Check file exists
if not os.path.isfile(filename):
	print("ERROR: Argument must be a valid file name")
	exit(2)

# Parse parameters
if option == "all":
	print("==> running lexer")
	lexer()
elif option == "--debug":
	debug = True
	lexer()
elif option == "lexer" or option == "--lexer":
	lexer()
else:
	print("ARRRR: unknown function call")
	exit(3)
