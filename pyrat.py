#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# version = 1.2
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
jump = []
table = []
count = 0
errors = 0
index = 0
num = 1
n = 0
stage = 0

# Functions
def print_usage():
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [-d|-l|-s] [file]")
	print("USAGE: pyrat.py [--test|--rules]")

def print_token(text):
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

def print_rule(text):
	global logfile
	if logfile:
		log.write("  " + text + "\n")
	elif verbose:
		print("  " + text)

def print_bold(token, lexeme):
	global logfile
	if logfile:
		try:
			log.write("Token: {0:15} Lexeme: {1}\n".format(token, lexeme))
		except TypeError: "blank"
	elif verbose:
		try:
			print("\033[1mToken: {0:15} Lexeme: {1}\033[0m".format(token, lexeme))
		except TypeError: "blank"

def print_error(expected, token, lexeme):
	global logfile
	if logfile:
		try:
			print("Syntax Error: expected {0} but {1} {2} given, line {3}\n".format(expected, token, lexeme, num))
		except TypeError: "blank"
	else:
		try:
			print("\033[1;31m  Syntax Error:\033[0m expected \033[1m{0}\033[0m but \033[1m{1}\033[0m `{2}` given, line {3}".format(expected, token, lexeme, num))
		except TypeError: "blank"
	exit(10)

def get_token(n):
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
				check_rat("start", f)
				check_rat("mid", f)
				statement(f)
				statement(f)
				check_rat("end", f)
				dump_table()

	except ValueError: "cannot read file"
	f.close()

def get_lex(f):
	token = None
	lexeme = None
	try:
		token, lexeme = lexer(f)
	except TypeError: "EOF"
	return token, lexeme

def dump_table():
	print("\n\033[1m{0} {1:10} {2}\033[0m".format("Address", "Op", "oprnd"))
	global table
	if len(table) > 0:
		for row in table:
			if row[2] != None:
				print("{0:2}      {1:10} {2}".format(row[0], row[1], row[2]))

def check_rat(pos,f):
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)

	if lexeme == "$$":
		if pos == "start":
			print_rule("<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$")
	elif pos == "end":
		print_error("end of file", token, lexeme)
	else:
		print_error("$$", token, lexeme)

def statement(f):
	print_rule("<Statement List> ::= <Statement>")
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	token, lexeme = assign(f, token, lexeme)

def assign(f, token, lexeme):
	save = token
	print_rule("<Statement> ::= <Assign>")

	if token == "identifier":
		print_rule("<Assign> ::= <Identifier> = <Expression>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if lexeme == "=":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = express(f, token, lexeme)
			print_rule("<Expression Prime> := ɛ")
			addr = get_address(save)
			gen_instr("POPM", addr)
		else:
			print_error("=", token, lexeme)
	else:
		print_error("identifier", token, lexeme)

	return token, lexeme


def express(f, token, lexeme):
	print_rule("<Expression> := <Term> <Expression Prime>")
	token, lexeme = term(f, token, lexeme)
	token, lexeme = eprime(f, token, lexeme)
	return token, lexeme

def eprime(f, token, lexeme):
	print_rule("<Term Prime> := ɛ")
	if lexeme == "+":
		print_rule("<Expression Prime> := + <Term> <Expression Prime>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = term(f, token, lexeme)
		gen_instr("ADD", None)
		token, lexeme = eprime(f, token, lexeme)
	elif lexeme == "-":
		print_rule("<Expression Prime> := - <Term> <Expression Prime>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = term(f, token, lexeme)
		gen_instr("SUB", None)
		token, lexeme = eprime(f, token, lexeme)
	return token, lexeme


def term(f, token, lexeme):
	print_rule("<Term> := <Factor> <Term Prime>")
	token, lexeme = factor(f, token, lexeme)
	token, lexeme = tprime(f, token, lexeme)
	return token, lexeme


def tprime(f, token, lexeme):
	if lexeme == "*":
		print_rule("<Term Prime> := * <Factor>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		gen_instr("MUL", None)
		token, lexeme = tprime(f, token, lexeme)
	elif lexeme == "/":
		print_rule("<Term Prime> := / <Factor>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		gen_instr("DIV", None)
		token, lexeme = tprime(f, token, lexeme)
	return token, lexeme


def factor(f, token, lexeme):
	if token == "identifier":
		print_rule("<Factor> := <Identifier>")
		addr = get_address(token)
		gen_instr("PUSHM", addr)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
	else:
		print_error("identifier", token, lexeme)
	return token, lexeme

def while_loop(f, token, lexeme):
	if lexeme == "while":
		global index
		addr = index
		gen_instr("LABEL", None)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if lexeme == "(":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = condition(f, token, lexeme)
			if lexeme == ")":
				token, lexeme = get_lex(f)
				print_bold(token, lexeme)
				token, lexeme = statement(f, token, lexeme)
				gen_instr("JUMP", addr)
				back_patch(index)
			else:
				print_error(")", token, lexeme)
		else:
			print_error("(", token, lexeme)
	else:
		print_error("while", token, lexeme)

def back_patch(jump_addr):
	addr = jump.pop()
	t1, t2, t3 = table[addr]
	table.insert(addr, (t1, t2, jump_addr))

def condition(f, token, lexeme):
	token, lexeme = express(f, token, lexeme)
	if lexeme == "==" or lexeme == "!=" or lexeme == ">" or lexeme == "<":
		global index
		op = lexeme
		token, lexeme = express(f, token, lexeme)
		if op == "<":
			gen_instr("LES", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == ">":
			gen_instr("GRT", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == "==":
			gen_instr("EQU", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == "!=":
			gen_instr("NEQ", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		else:
			print_error("unknown state", token, lexeme)
	else:
		print_error("<, >, ==, !=", token, lexeme)


def gen_instr(op, oprnd):
	global index
	table.insert(index, (index, op, oprnd))
	index += 1


def get_address(token):
	return 5000



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
				print_token("{0:15} {1}".format(token, lexeme))

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

	token = get_token(state)

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
	print_usage()
	exit(1)

# Check file exists
if re.match(r"\-t|\-r|\-\-test|\-\-rules", option) and len(sys.argv) > 2:
	print_usage()
	exit(1)

if filename == "--test" or filename == "-t":
	filename = temp
	option = "--test"
elif filename == "--test2" or filename == "-tt":
	filename = temp
	option = "--test2"
elif filename == "-h" or filename == "--help":
	print_usage()
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
