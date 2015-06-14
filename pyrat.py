#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

debug = False

# REGEX
keyword=r"(boolean|else|false|fi|function|if|integer|read|real|return|true|while|write)"
real=r"[0-9]+.[0-9]+"
integer=r"^[0-9]+"
identifier=r"[a-z]|([a-z]([0-9]|[a-z])+[a-z])"
operator=r"[><+*-/]"
separator=r"[,;(){}]"

# Functions
def getToken(n):
	if n == 1 or n == 2 or n == 3:
		token = None
	elif n == 4:
		token = "real\t"
	elif n == 5:
		token = "integer"
	elif n == 6:
		token = "operator"
	elif n == 7:
		token = "separator"
	elif n == 8:
		token = "keyword"
	elif n == 9:
		token = "identifier"
	else:
		token = "unknown"
	return token

def readfile(stage):
	try:
		with open(filename, 'r', 1) as f:
			if stage > 0:
				print("#", "\t", "TOKEN", "\t\t", "LEXEME")
				num = 1
				array = []

				run = True
				while run:
					if array:
						char = array[-1]
						array.pop()
					else:
						char = f.read(1)

					if not char: 
						break
					elif char == '\n':
						num += 1
					else:
						lexer(f, char, array, num)

	except ValueError: "cannot open file"
	f.close()

def lexer(f, char, array, num):
	token = None
	lexeme = None
	state = 0

	while state <= 3:
		if state == 0:
			if re.match(operator, char):
				lexeme = char
				state = 6
			elif re.match(separator, char):
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
			else:
				del array[:]
				state = 10
		elif state == 1:
			char = f.read(1)
			stack = ''.join(str(e) for e in array)
			if re.match(r"[!=|==]", stack+char):
				lexeme = stack+char
				array.pop()
				state = 6
			elif stack+char == "$$":
				lexeme = stack+char
				array.pop()
				state = 7
			else:
				del array[:]
				state = 11
		elif state == 2:
			char = f.read(1)
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
			else:
				del array[:]
				state = 12
		elif state == 3:
			char = f.read(1)
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
			else:
				del array[:]
				state = 13

	token = getToken(state)

	if debug:
		if(lexeme != None):
			print(num, "\t", token, "\t", lexeme, "\t\tstack: ", array)
		else:
			print("\t\t\t", char, "\t\tstack: ", array)
	else:
		if(lexeme != None):
			print(num, "\t", token, "\t", lexeme)

	return token, lexeme


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
	print("ARRRR: Argument must be a valid file name")
	exit(2)

# Parse parameters
if option == "all":
	print("==> running lexer")
	readfile(1)
elif option == "--debug":
	debug = True
	readfile(1)
elif option == "lexer" or option == "--lexer":
	readfile(1)
else:
	print("ARRRR: unknown function call")
	exit(3)
