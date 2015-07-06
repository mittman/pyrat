#!/usr/bin/env python3

# pyrat.py - Rat15su language compiler
# version = 1.8
# Copyright Kevin Mittman <kmittman@csu.fullerton.edu>
# (C) 2015 All Rights Reserved.

import os, sys, re

# Defaults
output = "rat15su.log"
temp = "pyrat.tmp"

# Flags
debug = False
test = False
rules = False
memory = False
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
known = []
ids = []
count = 0
icount = 0
errors = 0
index = 1
num = 1
n = 0
stage = 0
unit = 0
pos = 0
save = None
saveType = None

# Functions
def print_usage():
	print("USAGE: pyrat.py [file]")
	print("USAGE: pyrat.py [--|-a|-l|-s] [file]")
	print("USAGE: pyrat.py [--debug] [file]")
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

def print_row(col1, col2, col3=""):
	global count, errors, logfile, memory, unit
	if memory:

		errors = compare_asm(count, col1, col2, col3, unit)
		count += 1
	elif logfile:
		log.write("{0:3}      {1:15}   {2}\n".format(col1, col2, col3))
	else:
		print("{0:3}      {1:15}   {2}".format(col1, col2, col3))

def print_legend(col1, col2, col3=""):
	global icount, errors, logfile, memory, unit
	if memory:
		errors = compare_mem(icount, col1, col2, col3, unit)
		icount += 1
	elif logfile:
		log.write("{0:3}      {1:15}   {2}\n".format(col1, col2, col3))
	else:
		print("{0:3}      {1:15}   {2}".format(col1, col2, col3))

def print_rule(text):
	global count, errors, logfile, rules, unit
	if rules:
		errors = compare_rule(count, text, unit)
		count += 1
	elif logfile:
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
	global logfile, rules
	if logfile:
		try:
			print("Syntax Error: expected {0} but {1} {2} given, line {3}\n".format(expected, token, lexeme, num))
		except TypeError: "blank"
	else:
		try:
			print("\033[1;31m  Syntax Error:\033[0m expected \033[1m{0}\033[0m but \033[1m{1}\033[0m `{2}` given, line {3}".format(expected, token, lexeme, num))
		except TypeError: "blank"
	if not rules:
		dump_exit(10)

def print_exit(text):
	global logfile
	if logfile:
		print("Syntax Error: {0}, line {3}\n".format(text, num))
	else:
		print("\033[1;31m  Syntax Error:\033[0m \033[1m{0}\033[0m, line {3}".format(text, num))
	dump_exit(11)

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

			global array, ids, jump, known, table, count, errors, icount, pos, index, num
			del array[:], ids[:], jump[:], known[:], table[:]
			count = 0
			errors = 0
			icount = 0
			pos = 0
			index = 1
			num = 1

			if stage == 1:
				if debug:
					print("#", "\t", "TOKEN", "\t\t", "LEXEME")
				elif not test and not logfile:
					print("TOKEN", "\t\t", "LEXEME")
				lexer(f, n)

			elif stage == 2:
				# <Rat15su>
				token, lexeme = marker(f)
				# <Opt Function Definitions>
				token, lexeme = marker(f)
				# <Opt Declaration List> <Statement List>
				token, lexeme = opt_dec_list(f, token, lexeme)
				# End
				token, lexeme = marker(f)

			elif stage == 3:
				# <Rat15su>
				token, lexeme = marker(f)
				# <Opt Function Definitions>
				token, lexeme = marker(f)
				# <Opt Declaration List> <Statement List>
				token, lexeme = opt_dec_list(f, token, lexeme)
				# End
				token, lexeme = marker(f)
				# Output
				if not logfile:
					if verbose:
						banner()

					print("\033[1m{0}    {1:10} {2}\033[0m".format("Address", "Op\t", "  oprnd"))
					dump_table()
					print("\n\033[1m{0} {1:10} {2}\033[0m".format("Identifier", "MemoryLocation", "Type"))
					dump_symbols()
				else:
					banner()
					log.write("{0} {1:10} {2}\n".format("Address", "  Op\t", "  oprnd"))
					dump_table()
					log.write("\n{0} {1:10} {2}\n".format("Identifier", "MemoryLocation", "Type"))
					dump_symbols()

	except ValueError: "cannot read file"
	f.close()


def get_lex(f):
	token = None
	lexeme = None
	try:
		token, lexeme = lexer(f)
	except TypeError: "EOF"
	checkrat(f, token, lexeme)

	return token, lexeme


def marker(f):
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	if lexeme == None:
		pass
	elif lexeme != "$$":
		print_error("$$", token, lexeme)
	return token, lexeme


def checkrat(f, token, lexeme):
	global pos
	if lexeme == None:
		if pos < 3:
			print_exit("unexpected EOF")
		elif pos > 3:
			print_exit("end of file")
	elif lexeme == "$$":
		if pos == 0:
			rule1 = "<Rat15su> ::= $$ <Opt Function Definitions> "
			rule2 = "$$ <Opt Declaration List> <Statement List> $$"
			print_rule(rule1 + rule2)
		elif pos > 2:
			print_error("end of file", token, lexeme)
		pos += 1
	elif pos > 2:
		print_error("end of file", token, lexeme)


def gen_instr(op, oprnd):
	global index
	table.insert(index, (index, op, oprnd))
	index += 1


def get_address(token, lexeme):
	if lexeme in known:
		return 5000 + known.index(lexeme)
	else:
		if token == "identifier":
			ids.append(lexeme)
		known.append(lexeme)
		return 5000 + len(known) - 1


def dump_exit(n):
	global stage
	if stage > 2:
		dump_table()
		dump_symbols()
	exit(n)


def dump_table():
	global table
	if len(table) > 0:
		for row in table:
			if row[2] == None:
				print_row(row[0], row[1])
			else:
				print_row(row[0], row[1], row[2])


def dump_symbols():
	global icount, ids
	icount = len(ids)-1
	for s in range(0, len(ids)):
		print_legend(ids[s], 5000+s, "integer")


def opt_dec_list(f, token, lexeme):
	print_rule("<Opt Declaration List> ::= <Declaration List>")
	token, lexeme, declared = declaration_list(f, token, lexeme)
	token, lexeme = statement_list(f, token, lexeme, declared)	
	return token, lexeme


def declaration_list(f, token, lexeme):
	print_rule("<Declaration List> ::= <Declaration>;")
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	token, lexeme = declaration(f, token, lexeme)
	if lexeme == ";":
		return token, lexeme, False
	return token, lexeme, True


def declaration(f, token, lexeme):
	if lexeme == "integer":
		print_rule("<Declaration> ::= integer")
		#gen_instr("PUSHI", 0)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = dprime(f, token, lexeme, "integer")
		if lexeme != ";":
			print_error(";", token, lexeme)
	elif lexeme == "boolean":
		print_rule("<Declaration> ::= boolean")
		#gen_instr("PUSHI", 0)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = dprime(f, token, lexeme, "boolean")
		if lexeme != ";":
			print_error(";", token, lexeme)
	elif lexeme == "real":
		print_rule("<Declaration> ::= real")
		#gen_instr("PUSHI", 0)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = dprime(f, token, lexeme, "real")
		if lexeme != ";":
			print_error(";", token, lexeme)

	return token, lexeme


def dprime(f, token, lexeme, qualifier):
	if token == "identifier":
		print_rule("<Qualifier> ::= " + qualifier)
		get_address(token, lexeme)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if lexeme == ",":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = dprime(f, token, lexeme, qualifier)

	return token, lexeme


def statement_list(f, token, lexeme, declared=False):
	print_rule("<Statement List> ::= <Statement>")

	if not declared:
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)

	if lexeme != "}" and lexeme != None:
		token, lexeme = statement(f, token, lexeme)
		if lexeme != "$$":
			token, lexeme = statement_list(f, token, lexeme)
	return token, lexeme


def statement(f, token, lexeme):
	if token == "identifier":
		print_rule("<Statement> ::= <Assign>")
		token, lexeme = assign(f, token, lexeme)
		if lexeme != ";":
			print_error(";", token, lexeme)
	elif lexeme == "if":
		print_rule("<Statement> ::= <If>")
		token, lexeme = if_state(f, token, lexeme)
	elif lexeme == "while":
		print_rule("<Statement> ::= <While>")
		token, lexeme = while_loop(f, token, lexeme)
	elif lexeme == "read":
		print_rule("<Statement> ::= <Read>")
		token, lexeme = read_state(f, token, lexeme)
	elif lexeme == "write":
		print_rule("<Statement> ::= <Write>")
		token, lexeme = write_state(f, token, lexeme)
	elif lexeme == "{":
		print_rule("<Statement> ::= <Compound>")
		token, lexeme = compound(f, token, lexeme)
		if lexeme != "}":
			print_error("}", token, lexeme)
	elif lexeme == "$$":
		pass
	else:
		print_error("<Statement>", token, lexeme)

	return token, lexeme


def compound(f, token, lexeme):
	token, lexeme = statement_list(f, token, lexeme)
	return token, lexeme


def assign(f, token, lexeme):
	global save, saveType
	save = lexeme
	saveType = token
	addr = get_address(saveType, save)
	print_rule("<Statement> ::= <Assign>")

	if token == "identifier":
		print_rule("<Assign> ::= <Identifier> = <Expression>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if lexeme == "=":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			if token == "integer":
				gen_instr("PUSHI", lexeme)
			token, lexeme = express(f, token, lexeme)
			gen_instr("POPM", addr)
			print_rule("<Expression Prime> := ɛ")
		else:
			print_error("=", token, lexeme)
	else:
		print_error("identifier", token, lexeme)

	return token, lexeme


def express(f, token, lexeme):
	print_rule("<Expression> := <Term> <Expression Prime>")
	addr = get_address(token, lexeme)
	token, lexeme = term(f, token, lexeme)
	token, lexeme = eprime(f, token, lexeme, addr)
	return token, lexeme


def eprime(f, token, lexeme, addr=None):
	print_rule("<Term Prime> := ɛ")
	if lexeme == "+":
		print_rule("<Expression Prime> := + <Term> <Expression Prime>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if addr != None:
			gen_instr("PUSHM", addr)
		if token == "identifier":
			addr = get_address(token, lexeme)
			gen_instr("PUSHM", addr)
		else:
			gen_instr("PUSHI", lexeme)
		token, lexeme = term(f, token, lexeme)
		gen_instr("ADD", None)
		token, lexeme = eprime(f, token, lexeme)
	elif lexeme == "-":
		print_rule("<Expression Prime> := - <Term> <Expression Prime>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		if addr != None:
			gen_instr("PUSHM", addr)
		if token == "identifier":
			addr = get_address(token, lexeme)
			gen_instr("PUSHM", addr)
		else:
			gen_instr("PUSHI", lexeme)
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
	global saveType, save
	if token == "identifier":
		print_rule("<Factor> := <Identifier>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
	elif token == "integer":
		print_rule("<Factor> := <Integer>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
	else:
		print_error("identifier or integer", token, lexeme)
	return token, lexeme


def while_loop(f, token, lexeme):
	global index
	addr = index
	gen_instr("LABEL", None)
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	if lexeme == "(":
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		gen_instr("PUSHM", get_address(token, lexeme))
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

	return token, lexeme


def back_patch(jump_addr):
	addr = jump.pop()
	t1, t2, t3 = table[addr-1]
	table[addr-1] = (t1, t2, jump_addr)


def condition(f, token, lexeme):
	token, lexeme = express(f, token, lexeme)
	if lexeme == "==" or lexeme == "!=" or lexeme == ">" or lexeme == "<":
		global index
		op = lexeme
		token, lexeme = get_lex(f)
		addr = get_address(token, lexeme)
		print_bold(token, lexeme)
		token, lexeme = express(f, token, lexeme)

		if op == "<":
			gen_instr("PUSHM", addr)
			gen_instr("LES", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == ">":
			gen_instr("PUSHM", addr)
			gen_instr("GRT", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == "==":
			gen_instr("PUSHM", addr)
			gen_instr("EQU", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		elif op == "!=":
			gen_instr("PUSHM", addr)
			gen_instr("NEQ", None)
			jump.append(index)
			gen_instr("JUMPZ", None)
		else:
			print_error("unknown state", token, lexeme)
	else:
		print_error("<, >, ==, !=", token, lexeme)
	return token, lexeme


def if_state(f, token, lexeme):
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	if lexeme == "(":
		addr = index
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		gen_instr("PUSHM", get_address(token, lexeme))
		token, lexeme = condition(f, token, lexeme)
		if lexeme == ")":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = statement(f, token, lexeme)
			if lexeme != ";":
				print_error(";", token, lexeme)
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = else_state(f, token, lexeme)
			back_patch(index)
			if lexeme == "fi":
				token, lexeme = get_lex(f)
				print_bold(token, lexeme)
			else:
				print_error("fi", token, lexeme)
		else:
			print_error(")", token, lexeme)
	else:
		print_error("(", token, lexeme)
	return token, lexeme


def else_state(f, token, lexeme):
	if lexeme == "else":
		print_rule("<Statement> ::= <Else>")
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = statement(f, token, lexeme)
		if lexeme != ";":
			print_error(";", token, lexeme)
		else:
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
	return token, lexeme

def id_list(f, token, lexeme):
	if token == "identifier":
		get_address(token, lexeme)
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)

		if lexeme == ",":
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			token, lexeme = id_list(f, token, lexeme)
		else:
			return token, lexeme
	return token, lexeme


def read_state(f, token, lexeme):
	print_rule("<Read> ::= read ( <IDs> );")
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	if lexeme == "(":
		print_rule("<IDs> ::= <Identifier>")
		token, lexeme = get_lex(f)
		addr = get_address(token, lexeme)
		print_bold(token, lexeme)
		token, lexeme = id_list(f, token, lexeme)
		if lexeme == ")":
			gen_instr("PUSHS", None)
			gen_instr("POPM", addr)
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			if lexeme != ";":
				print_error(";", token, lexeme)
		else:
			print_error(")", token, lexeme)
	else:
		print_error("(", token, lexeme)
	return token, lexeme


def write_state(f, token, lexeme):
	token, lexeme = get_lex(f)
	print_bold(token, lexeme)
	if lexeme == "(":
		token, lexeme = get_lex(f)
		print_bold(token, lexeme)
		token, lexeme = express(f, token, lexeme)
		if lexeme == ")":
			gen_instr("POPS", None)
			token, lexeme = get_lex(f)
			print_bold(token, lexeme)
			if lexeme != ";":
				print_error(";", token, lexeme)
		else:
			print_error(")", token, lexeme)
	else:
		print_error("(", token, lexeme)
	return token, lexeme


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
	elif n == 5:
		testcase = """
$$
$$
    if(a < b) a = c; fi
$$
"""
	elif n == 6:
		testcase = """
$$
$$
	while(i < max) i = i + 1;
$$
"""
	elif n == 7:
		testcase = """
$$
$$
  integer i,max,sum;

  sum = 0;
  i = 1;

  read(max);
  while (i < max) {
    sum = sum + i;
    i = i + 1; }
  write(sum+max);
$$
"""


	try:
		f = open(temp, 'w')
		f.write(testcase)
	except ValueError: "cannot write file"
	f.close()

	print(testcase, "\n================")
	global unit
	unit = n
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
			status = "\033[1;31mFAIL\033[0m"
			global errors
			errors += 1

		print("{0:10} {1:10} {2:15} {3:10} {4}".format(status, token_unit[count], lexeme_unit[count], token, lexeme))
	else:
		print("==> FATAL ERROR: unexpected EOF")
		exit(5)

	return errors

def compare_rule(count, syntax, unit):
	if unit == 5:
		syntax_unit = ['<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$',\
					   '<Opt Declaration List> ::= <Declaration List>', '<Declaration List> ::= <Declaration>;',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <If>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression> := <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>',\
					   '<Term Prime> := ɛ', '<Statement> ::= <Assign>', '<Statement> ::= <Assign>',\
					   '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ', '<Expression Prime> := ɛ']
	elif unit == 6:
		syntax_unit = ['<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$',\
					   '<Opt Declaration List> ::= <Declaration List>', '<Declaration List> ::= <Declaration>;',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <While>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression> := <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>',\
					   '<Term Prime> := ɛ', '<Statement> ::= <Assign>', '<Statement> ::= <Assign>',\
					   '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression Prime> := + <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Integer>',
					   '<Term Prime> := ɛ', '<Expression Prime> := ɛ', '<Statement List> ::= <Statement>']
	elif unit == 7:
		syntax_unit = ['<Rat15su> ::= $$ <Opt Function Definitions> $$ <Opt Declaration List> <Statement List> $$',\
					   '<Opt Declaration List> ::= <Declaration List>', '<Declaration List> ::= <Declaration>;',\
					   '<Declaration> ::= integer', '<Qualifier> ::= integer', '<Qualifier> ::= integer', '<Qualifier> ::= integer',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <Assign>', '<Statement> ::= <Assign>',\
					   '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Integer>', '<Term Prime> := ɛ', '<Expression Prime> := ɛ',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <Assign>', '<Statement> ::= <Assign>',\
					   '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Integer>', '<Term Prime> := ɛ', '<Expression Prime> := ɛ',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <Read>', '<Read> ::= read ( <IDs> );', '<IDs> ::= <Identifier>',\
					   '<Statement List> ::= <Statement>', '<Statement> ::= <While>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression> := <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>',\
					   '<Term Prime> := ɛ', '<Statement> ::= <Compound>', '<Statement List> ::= <Statement>', '<Statement> ::= <Assign>',\
					   '<Statement> ::= <Assign>', '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression Prime> := + <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>',\
					   '<Term Prime> := ɛ', '<Expression Prime> := ɛ', '<Statement List> ::= <Statement>', '<Statement> ::= <Assign>',\
					   '<Statement> ::= <Assign>', '<Assign> ::= <Identifier> = <Expression>', '<Expression> := <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ',\
					   '<Expression Prime> := + <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>', '<Factor> := <Integer>',\
					   '<Term Prime> := ɛ', '<Expression Prime> := ɛ', '<Statement List> ::= <Statement>', '<Statement List> ::= <Statement>',\
					   '<Statement> ::= <Write>', '<Expression> := <Term> <Expression Prime>', '<Term> := <Factor> <Term Prime>',\
					   '<Factor> := <Identifier>', '<Term Prime> := ɛ', '<Expression Prime> := + <Term> <Expression Prime>',\
					   '<Term> := <Factor> <Term Prime>', '<Factor> := <Identifier>', '<Term Prime> := ɛ', '<Statement List> ::= <Statement>']
	else:
		print("ARRRR: Invalid test case")
		exit(4)

	if len(syntax_unit) > count:
		if syntax_unit[count] == syntax:
			status = "OK"
		else:
			status = "\033[1;31mFAIL\033[0m"
			global errors
			errors += 1

		print("  {0}\n  {1}\n{2}".format(syntax_unit[count], syntax, status))
	else:
		print("==> FATAL ERROR: unexpected EOF")
		exit(5)

	return errors

def compare_asm(count, address, op, oprnd, unit):
	if unit == 5:
		address_unit = ['1', '2', '3', '4', '5', '6']
		op_unit = ['PUSHM', 'PUSHM', 'LES', 'JUMPZ', 'PUSHM', 'POPM']
		oprnd_unit = ['5000', '5001', '', '7', '5002', '5000']
	elif unit == 6:
		address_unit = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
		op_unit = ['LABEL', 'PUSHM', 'PUSHM', 'LES', 'JUMPZ', 'PUSHM', 'PUSHM', 'ADD', 'POPM', 'JUMP']
		oprnd_unit = ['', '5000', '5001', '', '11', '5000', '5001', '', '5000', '1']
	elif unit == 7:
		address_unit = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18',\
                        '19', '20', '21', '22', '23', '24']
		op_unit = ['PUSHI', 'POPM', 'PUSHI', 'POPM', 'PUSHS', 'POPM', 'LABEL', 'PUSHM', 'PUSHM', 'LES', 'JUMPZ', 'PUSHM',\
                   'PUSHM', 'ADD', 'POPM', 'PUSHM', 'PUSHI', 'ADD', 'POPM', 'JUMP', 'PUSHM', 'PUSHM', 'ADD', 'POPS']
		oprnd_unit = ['0', '5002', '1', '5000', '', '5001', '', '5000', '5001', '', '21', '5002', '5000', '', '5002', '5000',\
                     '1', '', '5000', '7', '5002', '5001', '', '']
	else:
		print("ARRRR: Invalid test case")
		exit(4)

	if len(address_unit) > count and len(op_unit) > count and len(oprnd_unit) > count:
		if address_unit[count] == str(address) and op_unit[count] == str(op) and oprnd_unit[count] == str(oprnd):
			status = "OK"
		else:
			status = "\033[1;31mFAIL\033[0m"
			global errors
			errors += 1

		print("{0}         {1:5}            {2:5}     {3}".format(address_unit[count], op_unit[count], oprnd_unit[count], ""))
		print("{0}         {1:5}            {2:5}     {3}\n".format(str(address), str(op), str(oprnd), status))
	else:
		print("==> FATAL ERROR: unexpected EOF")
		exit(5)

	return errors

def compare_mem(icount, varid, location, vartype, unit):
	global ids
	i = icount-len(ids)+1

	if unit == 5:
		varid_unit = ['a', 'b', 'c']
		location_unit = ['5000', '5001', '5002']
		vartype_unit = ['integer', 'integer', 'integer']
	elif unit == 6:
		varid_unit = ['i', 'max']
		location_unit = ['5000', '5001']
		vartype_unit = ['integer', 'integer']
	elif unit == 7:
		varid_unit = ['i', 'max', 'sum']
		location_unit = ['5000', '5001', '5002']
		vartype_unit = ['integer', 'integer', 'integer']
	else:
		print("ARRRR: Invalid test case")
		exit(4)

	if len(varid_unit) > i and len(location_unit) > i and len(vartype_unit) > i:
		if varid_unit[i] == str(varid) and location_unit[i] == str(location) and vartype_unit[i] == str(vartype):
			status = "OK"
		else:
			status = "\033[1;31mFAIL\033[0m"
			global errors
			errors += 1

		print("{0:5}        {1:5}        {2:8}     {3}".format(varid_unit[i], location_unit[i], vartype_unit[i], ""))
		print("{0:5}        {1:5}        {2:8}     {3}\n".format(str(varid), str(location), str(vartype), status))

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
if re.match(r"\-t|\-r|\-m|\-\-test|\-\-rules|\-\-memory", option) and len(sys.argv) > 2:
	print_usage()
	exit(1)

if filename == "--test" or filename == "-t":
	filename = temp
	option = "--test"
elif filename == "--rules" or filename == "-r":
	filename = temp
	option = "--rules"
elif filename == "--memory" or filename == "-m":
	filename = temp
	option = "--memory"
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
	print("==> running compiler")
	stage = 3
	target()
	print("==> saved to " + output)
elif option == "--":
	logfile = False
	verbose = True
	print("==> running lexer")
	stage = 1
	target()
	banner()
	print("==> running compiler")
	stage = 3
	target()
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
elif option == "--assembly" or option == "-a":
	logfile = False
	verbose = False
	stage = 3
	target()
elif option == "--test" or option == "-t":
	test = True
	stage = 1
	unit_test(1)
	unit_test(2)
	unit_test(3)
	unit_test(4)
	os.remove(temp)
elif option == "--rules" or option == "-r":
	logfile = False
	rules = True
	verbose = True
	stage = 2
	unit_test(5)
	unit_test(6)
	unit_test(7)
	os.remove(temp)
elif option == "--memory" or option == "-m":
	logfile = False
	memory = True
	verbose = False
	stage = 3
	unit_test(5)
	unit_test(6)
	unit_test(7)
	os.remove(temp)
else:
	print("ARRRR: unknown function call")
	exit(3)
