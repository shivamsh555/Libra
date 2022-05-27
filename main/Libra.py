#######################################
# IMPORTS
#######################################

from strings_with_arrows import *
import string
import os
import math

#######################################
# CONSTANTS
#######################################

DIGITS = '0123456789'
LETTERS= string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS
#######################################
# ERRORS
#######################################

class Error:
	def __init__(self, pos_start, pos_end, error_name, details):
		self.pos_start = pos_start
		self.pos_end = pos_end
		self.error_name = error_name
		self.details = details
	
	def as_string(self):
		result  = f'{self.error_name}: {self.details}\n'
		result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
		result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
		return result

class IllegalCharError(Error):
	def __init__(self, pos_start, pos_end, details):
		super().__init__(pos_start, pos_end, 'Illegal Character', details)

class ExpectedCharError(Error):
	def __init__(self, pos_start, pos_end, details):
		super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
	def __init__(self, pos_start, pos_end, details=''):
		super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RunTimeError(Error):
	def __init__(self, pos_start, pos_end, details, context):
		super().__init__(pos_start, pos_end, 'Runtime Error', details)
		self.context = context

	def as_string(self):
		result  = self.generate_traceback()
		result += f'{self.error_name}: {self.details}'
		result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
		return result

	def generate_traceback(self):
		result = ''
		pos = self.pos_start
		ctx = self.context

		while ctx:
			result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
			pos = ctx.parent_entry_pos
			ctx = ctx.parent

		return 'Traceback (most recent call last):\n' + result

#######################################
# POSITION
#######################################

class Position:
	def __init__(self, idx, ln, col, fn, ftxt):
		self.idx = idx
		self.ln = ln
		self.col = col
		self.fn = fn
		self.ftxt = ftxt

	def advance(self, current_char=None):
		self.idx += 1
		self.col += 1

		if current_char == '\n':
			self.ln += 1
			self.col = 0

		return self

	def copy(self):
		return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#######################################
# TOKENS
#######################################

TOK_INT		 = 'INT'
TOK_FLOAT    = 'FLOAT'
TOK_STRING	 = 'STRING'
TOK_IDENTIFIER = 'IDENTIFIER'
TOK_KEYWORD = 'KEYWORD'
TOK_PLUS     = 'PLUS'
TOK_MINUS    = 'MINUS'
TOK_MUL      = 'MUL'
TOK_DIV      = 'DIV'
TOK_POW      = 'POW'
TOK_EQS      = 'EQS'
TOK_LPAREN   = 'LPAREN'
TOK_RPAREN   = 'RPAREN'
TOK_LSQB     = 'LSQB'
TOK_RSQB     = 'RSQB'
TOK_EE 		 = 'EE'
TOK_NE 		 = 'NE'
TOK_LT 		 = 'LT'
TOK_GT 		 = 'GT'
TOK_LTE 	 = 'LTE'
TOK_GTE 	 = 'GTE'
TOK_MOD		 = 'MOD'
TOK_COMMA	 = 'COMMA'
TOK_COLON	 = 'COLON'
TOK_NEWL	 = 'NEWL'
TOK_EOF		 = 'EOF'

KEYWORDS=[
	'var',
	'AND',
	'OR',
	'NOT',
	'if',
	'then',
	'elsif',
	'else',
	'from',
	'to',
	'step',
	'until',
	'fun',
	'just',
	'ret',
	'cont',
	'brk'
]

class Token:
	def __init__(self, type_, value=None, pos_start=None, pos_end=None):
		self.type = type_
		self.value = value

		if pos_start:
			self.pos_start = pos_start.copy()
			self.pos_end = pos_start.copy()
			self.pos_end.advance()

		if pos_end:
			self.pos_end = pos_end.copy()

	def matches(self,type_,value):
		return self.type == type_ and self.value == value
	
	def __repr__(self):
		if self.value: return f'{self.type}:{self.value}'
		return f'{self.type}'

	


#######################################
# LEXER
#######################################

class Lexer:
	def __init__(self, fn, text):
		self.fn = fn
		self.text = text
		self.pos = Position(-1, 0, -1, fn, text)
		self.current_char = None
		self.advance()
	
	def advance(self):
		self.pos.advance(self.current_char)
		self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

	def make_tokens(self):
		tokens = []

		while self.current_char != None:
			if self.current_char in ' \t':
				self.advance()
			elif self.current_char in '!!':
				self.skip_comment()
			elif self.current_char in ';\n':
				tokens.append(Token(TOK_NEWL, pos_start=self.pos))
				self.advance()
			elif self.current_char in DIGITS:
				tokens.append(self.make_number())
			elif self.current_char in LETTERS:
				tokens.append(self.make_identifier())
			elif self.current_char == '"':
				tokens.append(self.make_string())
			elif self.current_char == '+':
				tokens.append(Token(TOK_PLUS, pos_start=self.pos))
				self.advance()
			elif self.current_char == '-':
				tokens.append(Token(TOK_MINUS, pos_start=self.pos))
				self.advance()
			elif self.current_char == '*':
				tokens.append(Token(TOK_MUL, pos_start=self.pos))
				self.advance()
			elif self.current_char == '/':
				tokens.append(Token(TOK_DIV, pos_start=self.pos))
				self.advance()
			elif self.current_char == '%':
				tokens.append(Token(TOK_MOD, pos_start=self.pos))
				self.advance()
			elif self.current_char == '^':
				tokens.append(Token(TOK_POW, pos_start=self.pos))
				self.advance()
			elif self.current_char == '(':
				tokens.append(Token(TOK_LPAREN, pos_start=self.pos))
				self.advance()
			elif self.current_char == ')':
				tokens.append(Token(TOK_RPAREN, pos_start=self.pos))
				self.advance()
			elif self.current_char == '[':
				tokens.append(Token(TOK_LSQB, pos_start=self.pos))
				self.advance()
			elif self.current_char == ']':
				tokens.append(Token(TOK_RSQB, pos_start=self.pos))
				self.advance()
			elif self.current_char == '!':
				tok,error=self.make_not_equals()
				if error:return [], error
				tokens.append(tok)
			elif self.current_char == '=':
				tokens.append(self.make_equals())
			elif self.current_char == '<':
				tokens.append(self.make_less_than())
			elif self.current_char == '>':
				tokens.append(self.make_greater_than())
			elif self.current_char == ':':
				tokens.append(self.make_colon())
			elif self.current_char == ',':
				tokens.append(Token(TOK_COMMA, pos_start=self.pos))
				self.advance()
			else:
				pos_start = self.pos.copy()
				char = self.current_char
				self.advance()
				return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

		tokens.append(Token(TOK_EOF, pos_start=self.pos))
		return tokens, None

	def make_number(self):
		num_str = ''
		dot_count = 0
		pos_start = self.pos.copy()

		while self.current_char != None and self.current_char in DIGITS + '.':
			if self.current_char == '.':
				if dot_count == 1: break
				dot_count += 1
				num_str += '.'
			else:
				num_str += self.current_char
			self.advance()

		if dot_count == 0:
			return Token(TOK_INT, int(num_str), pos_start, self.pos)
		else:
			return Token(TOK_FLOAT, float(num_str), pos_start, self.pos)

	def make_string(self):
		string = ''
		pos_start = self.pos.copy()
		escape_character = False
		self.advance()

		escape_characters = {
			'n': '\n',
			't': '\t'
		}

		while self.current_char != None and (self.current_char != '"' or escape_character):
			if escape_character:
				string += escape_characters.get(self.current_char, self.current_char)
			else:
				if self.current_char == '\\':
					escape_character = True
				else:
					string += self.current_char
			self.advance()
			escape_character = False
		
		self.advance()
		return Token(TOK_STRING, string, pos_start, self.pos)

	def make_identifier(self):
		id_str=''
		pos_start=self.pos.copy()
		while self.current_char!= None and self.current_char in LETTERS_DIGITS + '_':
			id_str+=self.current_char
			self.advance()
		tok_type=TOK_KEYWORD if id_str in KEYWORDS else TOK_IDENTIFIER
		return Token(tok_type,id_str,pos_start,self.pos)

	def make_colon(self):
		pos_start=self.pos.copy()
		if self.current_char==':':
			self.advance()
			tok_type=TOK_COLON

		return Token(tok_type,pos_start=pos_start,pos_end=self.pos)

	def make_not_equals(self):
		pos_start=self.pos.copy()
		self.advance()
		
		if self.current_char=='=':
			self.advance()
			return Token(TOK_NE,pos_start=pos_start,pos_end=self.pos),None

		self.advance()
		return None,ExpectedCharError(pos_start,self.pos,"'=' (after '!')")

	def make_equals(self):
		tok_type=TOK_EQS
		pos_start=self.pos.copy()
		self.advance()

		if self.current_char=='=':
			self.advance()
			tok_type=TOK_EE

		return Token(tok_type,pos_start=pos_start,pos_end=self.pos)

	def make_less_than(self):
		tok_type=TOK_LT
		pos_start=self.pos.copy()
		self.advance()

		if self.current_char=='=':
			self.advance()
			tok_type=TOK_LTE

		return Token(tok_type,pos_start=pos_start,pos_end=self.pos)
	
	def make_greater_than(self):
		tok_type=TOK_GT
		pos_start=self.pos.copy()
		self.advance()

		if self.current_char=='=':
			self.advance()
			tok_type=TOK_GTE

		return Token(tok_type,pos_start=pos_start,pos_end=self.pos)

	def skip_comment(self):
		self.advance()

		while self.current_char != '\n':
			self.advance()

		self.advance()

#######################################
# NODES
#######################################

class NumberNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok}'

class StringNode:
	def __init__(self, tok):
		self.tok = tok

		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end

	def __repr__(self):
		return f'{self.tok}'

class ListNode:
	def __init__(self, element_nodes, pos_start, pos_end):
		self.element_nodes = element_nodes
		self.pos_start = pos_start
		self.pos_end = pos_end

class VarAccessNode:
	def __init__(self,var_name_tok):
		self.var_name_tok = var_name_tok
		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.var_name_tok.pos_end 

class VarAssignNode:
	def __init__(self,var_name_tok,value_node):
		self.var_name_tok = var_name_tok
		self.value_node = value_node
		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.value_node.pos_end 

class BinOpNode:
	def __init__(self, left_node, op_tok, right_node):
		self.left_node = left_node
		self.op_tok = op_tok
		self.right_node = right_node

		self.pos_start = self.left_node.pos_start
		self.pos_end = self.right_node.pos_end

	def __repr__(self):
		return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
	def __init__(self, op_tok, node):
		self.op_tok = op_tok
		self.node = node

		self.pos_start = self.op_tok.pos_start
		self.pos_end = node.pos_end

	def __repr__(self):
		return f'({self.op_tok}, {self.node})'

class IfNode:
	def __init__(self,cases,else_case):
		self.cases=cases
		self.else_case=else_case

		self.pos_start=self.cases[0][0].pos_start
		self.pos_end=(self.else_case or self.cases[len(self.cases)-1])[0].pos_end

class FromNode:
	def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node,should_return_null):
		self.var_name_tok = var_name_tok
		self.start_value_node = start_value_node
		self.end_value_node = end_value_node
		self.step_value_node = step_value_node
		self.body_node = body_node
		self.should_return_null = should_return_null

		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.body_node.pos_end

class UntilNode:
	def __init__(self, condition_node, body_node,should_return_null):
		self.condition_node = condition_node
		self.body_node = body_node
		self.should_return_null = should_return_null

		self.pos_start = self.condition_node.pos_start
		self.pos_end = self.body_node.pos_end

class FuncDefNode:
	def __init__(self, var_name_tok, arg_name_toks, body_node,should_auto_return):
		self.var_name_tok = var_name_tok
		self.arg_name_toks = arg_name_toks
		self.body_node = body_node
		self.should_auto_return = should_auto_return

		if self.var_name_tok:
			self.pos_start = self.var_name_tok.pos_start
		elif len(self.arg_name_toks) > 0:
			self.pos_start = self.arg_name_toks[0].pos_start
		else:
			self.pos_start = self.body_node.pos_start

		self.pos_end = self.body_node.pos_end

class CallNode:
	def __init__(self, node_to_call, arg_nodes):
		self.node_to_call = node_to_call
		self.arg_nodes = arg_nodes

		self.pos_start = self.node_to_call.pos_start

		if len(self.arg_nodes) > 0:
			self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
		else:
			self.pos_end = self.node_to_call.pos_end

class RetNode:
	def __init__(self, node_to_return, pos_start, pos_end):
		self.node_to_return = node_to_return

		self.pos_start = pos_start
		self.pos_end = pos_end

class ContNode:
	def __init__(self, pos_start, pos_end):
		self.pos_start = pos_start
		self.pos_end = pos_end

class BrkNode:
	def __init__(self, pos_start, pos_end):
		self.pos_start = pos_start
		self.pos_end = pos_end


#######################################
# PARSE RESULT
#######################################

class ParseResult:
	def __init__(self):
		self.error = None
		self.node = None
		self.last_reg_adv_count = 0
		self.adv_count=0
		self.to_rev_count = 0

	def register_advance(self):
		self.last_reg_adv_count=1
		self.adv_count+=1

	def register(self, res):
		self.last_reg_adv_count = res.adv_count
		self.adv_count+=res.adv_count
		if res.error:self.error = res.error
		return res.node

	def try_register(self, res):
		if res.error:
			self.to_rev_count = res.adv_count
			return None
		return self.register(res)

	def success(self, node):
		self.node = node
		return self

	def failure(self, error):
		if not self.error or self.last_reg_adv_count==0:
			self.error = error
		return self

#######################################
# PARSER
#######################################

class Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		self.tok_idx = -1
		self.advance()

	def advance(self, ):
		self.tok_idx += 1
		self.update_current_tok()
		return self.current_tok

	def reverse(self, amount=1):
		self.tok_idx -= amount
		self.update_current_tok()
		return self.current_tok

	def update_current_tok(self):
		if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
			self.current_tok = self.tokens[self.tok_idx]

	def parse(self):
		res = self.statements()
		if not res.error and self.current_tok.type != TOK_EOF:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
			))
		return res

	###################################
	
	def statements(self):
		res = ParseResult()
		statements = []
		pos_start = self.current_tok.pos_start.copy()
		
		while self.current_tok.type == TOK_NEWL:
			res.register_advance()
			self.advance()

		statement = res.register(self.statement())
		if res.error: return res
		statements.append(statement)
		
		more_statements = True

		while True:
			newline_count = 0
			while self.current_tok.type == TOK_NEWL:
				res.register_advance()
				self.advance()
				newline_count += 1
			if newline_count == 0:
				more_statements = False
      		
			if not more_statements: break
			statement = res.try_register(self.statement())
			if not statement:
				self.reverse(res.to_rev_count)
				more_statements = False
				continue
			statements.append(statement)
		
		return res.success(ListNode(
      statements,
      pos_start,
      self.current_tok.pos_end.copy()
    ))

	def statement(self):
		res = ParseResult()
		pos_start = self.current_tok.pos_start.copy()

		if self.current_tok.matches(TOK_KEYWORD, 'ret'):
			res.register_advance()
			self.advance()

			expr = res.try_register(self.expr())
			if not expr:
				self.reverse(res.to_reverse_count)
			return res.success(RetNode(expr, pos_start, self.current_tok.pos_start.copy()))
    
		if self.current_tok.matches(TOK_KEYWORD, 'cont'):
			res.register_advance()
			self.advance()
			return res.success(ContNode(pos_start, self.current_tok.pos_start.copy()))
      
		if self.current_tok.matches(TOK_KEYWORD, 'brk'):
			res.register_advance()
			self.advance()
			return res.success(BrkNode(pos_start, self.current_tok.pos_start.copy()))

		expr = res.register(self.expr())
		if res.error:
			return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected 'ret', 'cont', 'brk', 'var', 'if', 'from', 'until', 'fun', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
      ))
		return res.success(expr)


	def if_expr(self):
		res = ParseResult()
		all_cases = res.register(self.if_expr_cases('if'))
		if res.error: return res
		cases, else_case = all_cases
		return res.success(IfNode(cases, else_case))
	
	def if_expr_b(self):
		return self.if_expr_cases('elsif')
    
	def if_expr_c(self):
		res = ParseResult()
		else_case = None

		if self.current_tok.matches(TOK_KEYWORD, 'else'):
			res.register_advance()
			self.advance()
			if self.current_tok.type == TOK_NEWL:
				res.register_advance()
				self.advance()
				
				statements = res.register(self.statements())
				if res.error: return res
				else_case = (statements, True)
				
				if self.current_tok.matches(TOK_KEYWORD, 'just'):
					res.register_advance()
					self.advance()
				else:
					return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'just'"))
			else:
				expr = res.register(self.statement())
				if res.error: return res
				else_case = (expr, False)
		
		return res.success(else_case)

	def if_expr_b_or_c(self):
		res = ParseResult()
		cases, else_case = [], None

		if self.current_tok.matches(TOK_KEYWORD, 'elsif'):
			all_cases = res.register(self.if_expr_b())
			if res.error: return res
			cases, else_case = all_cases
		else:
			else_case = res.register(self.if_expr_c())
			if res.error: return res
		
		return res.success((cases, else_case))

	def if_expr_cases(self, case_keyword):
		res = ParseResult()
		cases = []
		else_case = None

		if not self.current_tok.matches(TOK_KEYWORD, case_keyword):
			return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '{case_keyword}'"
      ))

		res.register_advance()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TOK_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'then'"
      ))

		res.register_advance()
		self.advance()

		if self.current_tok.type == TOK_NEWL:
			res.register_advance()
			self.advance()

			statements = res.register(self.statements())
			if res.error: return res
			cases.append((condition, statements, True))

			if self.current_tok.matches(TOK_KEYWORD, 'just'):
				res.register_advance()
				self.advance()
			else:
				all_cases = res.register(self.if_expr_b_or_c())
				if res.error: return res
				new_cases, else_case = all_cases
				cases.extend(new_cases)
		else:
			expr = res.register(self.statement())
			if res.error: return res
			cases.append((condition, expr, False))

			all_cases = res.register(self.if_expr_b_or_c())
			if res.error: return res
			new_cases, else_case = all_cases
			cases.extend(new_cases)

		return res.success((cases, else_case))

	def from_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(TOK_KEYWORD, 'from'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'from'"
			))

		res.register_advance()
		self.advance()

		if self.current_tok.type != TOK_IDENTIFIER:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected identifier"
			))

		var_name = self.current_tok
		res.register_advance()
		self.advance()

		if self.current_tok.type != TOK_EQS:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '='"
			))
		
		res.register_advance()
		self.advance()

		start_value = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TOK_KEYWORD, 'to'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'to'"
			))
		
		res.register_advance()
		self.advance()

		end_value = res.register(self.expr())
		if res.error: return res

		if self.current_tok.matches(TOK_KEYWORD, 'step'):
			res.register_advance()
			self.advance()

			step_value = res.register(self.expr())
			if res.error: return res
		else:
			step_value = None

		if not self.current_tok.matches(TOK_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'then'"
			))
		res.register_advance()
		self.advance()

		if self.current_tok.type == TOK_NEWL:
			res.register_advance()
			self.advance()

			body = res.register(self.statements())
			if res.error: return res

			if not self.current_tok.matches(TOK_KEYWORD, 'just'):
				return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'just'"
        ))

			res.register_advance()
			self.advance()
			return res.success(FromNode(var_name, start_value, end_value, step_value, body, True))

		body = res.register(self.statement())
		if res.error: return res

		return res.success(FromNode(var_name, start_value, end_value, step_value, body,False))

	def until_expr(self):
		res = ParseResult()

		if not self.current_tok.matches(TOK_KEYWORD, 'until'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'until'"
			))

		res.register_advance()
		self.advance()

		condition = res.register(self.expr())
		if res.error: return res

		if not self.current_tok.matches(TOK_KEYWORD, 'then'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'then'"
			))

		res.register_advance()
		self.advance()

		if self.current_tok.type == TOK_NEWL:
			res.register_advance()
			self.advance()

			body = res.register(self.statements())
			if res.error: return res

			if not self.current_tok.matches(TOK_KEYWORD, 'just'):
				return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'just'"
        ))

			res.register_advance()
			self.advance()

			return res.success(UntilNode(condition, body, True))

		body = res.register(self.statement())
		if res.error: return res

		return res.success(UntilNode(condition, body,False))

	def power(self):
		return self.bin_op(self.call, (TOK_POW, ), self.factor)

	def call(self):
		res = ParseResult()
		atom = res.register(self.atom())
		if res.error: return res

		if self.current_tok.type == TOK_LPAREN:
			res.register_advance()
			self.advance()
			arg_nodes = []

			if self.current_tok.type == TOK_RPAREN:
				res.register_advance()
				self.advance()
			else:
				arg_nodes.append(res.register(self.expr()))
				if res.error:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected ')', 'var', 'if', 'from', 'until', 'fun', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
					))

				while self.current_tok.type == TOK_COMMA:
					res.register_advance()
					self.advance()

					arg_nodes.append(res.register(self.expr()))
					if res.error: return res

				if self.current_tok.type != TOK_RPAREN:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Expected ',' or ')'"
					))

				res.register_advance()
				self.advance()
			return res.success(CallNode(atom, arg_nodes))
		return res.success(atom)


	def atom(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (TOK_INT, TOK_FLOAT):
			res.register_advance()
			self.advance()
			return res.success(NumberNode(tok))

		if tok.type in (TOK_STRING):
			res.register_advance()
			self.advance()
			return res.success(StringNode(tok))
			
		elif tok.type == TOK_IDENTIFIER:
			res.register_advance()
			self.advance()
			return res.success(VarAccessNode(tok))

		elif tok.type == TOK_LPAREN:
			res.register_advance()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			if self.current_tok.type == TOK_RPAREN:
				res.register_advance()
				self.advance()
				return res.success(expr)
			else:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ')'"
				))

		elif tok.type == TOK_LSQB:
			list_expr = res.register(self.list_expr())
			if res.error: return res
			return res.success(list_expr)

		elif tok.matches(TOK_KEYWORD,'if'):
			if_expr=res.register(self.if_expr())
			if res.error: return res
			return res.success(if_expr)

		elif tok.matches(TOK_KEYWORD, 'from'):
			from_expr = res.register(self.from_expr())
			if res.error: return res
			return res.success(from_expr)

		elif tok.matches(TOK_KEYWORD, 'until'):
			until_expr = res.register(self.until_expr())
			if res.error: return res
			return res.success(until_expr)

		elif tok.matches(TOK_KEYWORD, 'fun'):
			func_def = res.register(self.func_def())
			if res.error: return res
			return res.success(func_def)

		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			"Expected int, float, identifier, '+', '-' or '(', '[', 'if', 'from', 'until', 'fun' "
		))

	def list_expr(self):
		res = ParseResult()
		element_nodes = []
		pos_start = self.current_tok.pos_start.copy()
		if self.current_tok.type != TOK_LSQB:
			return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,f"Expected '['"))
			
		res.register_advance()
		self.advance()
		
		if self.current_tok.type == TOK_RSQB:
			res.register_advance()
			self.advance()
		else:
			element_nodes.append(res.register(self.expr()))
			if res.error:
				return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,"Expected ']', 'var', 'if', 'from', 'until', 'fun', int, float, identifier, '+', '-', '(', '[' or 'NOT'"))
			
			while self.current_tok.type == TOK_COMMA:
				res.register_advance()
				self.advance()
				element_nodes.append(res.register(self.expr()))
				if res.error: return res
			if self.current_tok.type != TOK_RSQB:
				return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,f"Expected ',' or ']'"))
			res.register_advance()
			self.advance()
		return res.success(ListNode(element_nodes,pos_start,self.current_tok.pos_end.copy()))

	def factor(self):
		res = ParseResult()
		tok = self.current_tok

		if tok.type in (TOK_PLUS, TOK_MINUS):
			res.register_advance()
			self.advance()
			factor = res.register(self.factor())
			if res.error: return res
			return res.success(UnaryOpNode(tok, factor))
		
		return self.power()

	def term(self):
		return self.bin_op(self.factor, (TOK_MUL, TOK_DIV, TOK_MOD))

	def art_expr(self):
		return self.bin_op(self.term,(TOK_PLUS,TOK_MINUS))

	def comp_expr(self):
		res=ParseResult()
		if self.current_tok.matches(TOK_KEYWORD,"NOT"):
			op_tok = self.current_tok
			res.register_advance()
			self.advance()

			node= res.register(self.comp_expr())
			if res.error:return res
			return res.success(UnaryOpNode(op_tok,node))
		node=res.register(self.bin_op(self.art_expr,(TOK_EE,TOK_NE,TOK_LT,TOK_GT,TOK_LTE,TOK_GTE)))

		if res.error:
			return res.failure(InvalidSyntaxError(self.current_tok.pos_start,self.current_tok.pos_end,
			"Expected int, float, identifier, '+', '-', '(','[', 'NOT'"))
		return res.success(node)

	def expr(self):
		res=ParseResult()
		if self.current_tok.matches(TOK_KEYWORD, 'var'):
			res.register_advance()
			self.advance()

			if self.current_tok.type != TOK_IDENTIFIER:
				return res.failure(InvalidSyntaxError(self.current_tok.pos_start,self.current_tok.pos_end,'Expected identifier'))
			var_name=self.current_tok
			res.register_advance()
			self.advance()

			if self.current_tok.type != TOK_EQS:
				return res.failure(InvalidSyntaxError(self.current_tok.pos_start,self.current_tok.pos_end,"Expected '='"))
			res.register_advance()
			self.advance()
			expr=res.register(self.expr())

			if res.error: return res
			return res.success(VarAssignNode(var_name,expr))


		node= res.register(self.bin_op(self.comp_expr, ((TOK_KEYWORD,"AND"),(TOK_KEYWORD,"OR"))))
		if res.error:
			return res.failure(InvalidSyntaxError(self.current_tok.pos_start,self.current_tok.pos_end,"Expected 'var', 'if', 'from', 'until', 'fun', int, float, identifier, '+', '-' or '(', '[' "))
		return res.success(node)

	def func_def(self):
		res = ParseResult()

		if not self.current_tok.matches(TOK_KEYWORD, 'fun'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'fun'"
			))

		res.register_advance()
		self.advance()

		if self.current_tok.type == TOK_IDENTIFIER:
			var_name_tok = self.current_tok
			res.register_advance()
			self.advance()
			if self.current_tok.type != TOK_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected '('"
				))
		else:
			var_name_tok = None
			if self.current_tok.type != TOK_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected identifier or '('"
				))
		
		res.register_advance()
		self.advance()
		arg_name_toks = []

		if self.current_tok.type == TOK_IDENTIFIER:
			arg_name_toks.append(self.current_tok)
			res.register_advance()
			self.advance()
			
			while self.current_tok.type == TOK_COMMA:
				res.register_advance()
				self.advance()

				if self.current_tok.type != TOK_IDENTIFIER:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Expected identifier"
					))

				arg_name_toks.append(self.current_tok)
				res.register_advance()
				self.advance()
			
			if self.current_tok.type != TOK_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected ',' or ')'"
				))
		else:
			if self.current_tok.type != TOK_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected identifier or ')'"
				))

		res.register_advance()
		self.advance()

		if self.current_tok.type == TOK_COLON:
			res.register_advance()
			self.advance()

			body = res.register(self.expr())
			if res.error: return res
			return res.success(FuncDefNode(
        var_name_tok,
        arg_name_toks,
        body,
        True
      ))
    
		if self.current_tok.type != TOK_NEWL:
			return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected ':' or NEWLINE"
      ))

		res.register_advance()
		self.advance()

		body = res.register(self.statements())
		if res.error: return res

		if not self.current_tok.matches(TOK_KEYWORD, 'just'):
			return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'just'"
      ))

		res.register_advance()
		self.advance()
    
		return res.success(FuncDefNode(
      var_name_tok,
      arg_name_toks,
      body,
	  False
    ))

	###################################

	def bin_op(self, func_a, ops, func_b=None):
		if func_b == None:
			func_b = func_a

		res = ParseResult()
		left = res.register(func_a())
		if res.error: return res

		while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
			op_tok = self.current_tok
			res.register_advance()
			self.advance()
			right = res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)

		return res.success(left)

#######################################
# RUNTIME RESULT
#######################################

class RTResult:
	def __init__(self):
		self.reset()

	def reset(self):
		self.value = None
		self.error = None
		self.func_return_value = None
		self.loop_should_continue = False
		self.loop_should_break = False

	def register(self, res):
		self.error = res.error
		self.func_return_value = res.func_return_value
		self.loop_should_continue = res.loop_should_continue
		self.loop_should_break = res.loop_should_break
		return res.value

	def success(self, value):
		self.reset()
		self.value = value
		return self

	def success_ret(self, value):
		self.reset()
		self.func_return_value = value
		return self
  
	def success_cont(self):
		self.reset()
		self.loop_should_continue = True
		return self

	def success_brk(self):
		self.reset()
		self.loop_should_break = True
		return self

	def failure(self, error):
		self.reset()
		self.error = error
		return self

	def should_return(self):# Note: this will allow you to continue and break outside the current function
		return (
      self.error or
      self.func_return_value or
      self.loop_should_continue or
      self.loop_should_break
    )

#######################################
# VALUES
#######################################

class Value:
	def __init__(self):
		self.set_pos()
		self.set_context()

	def set_pos(self, pos_start=None, pos_end=None):
		self.pos_start = pos_start
		self.pos_end = pos_end
		return self

	def set_context(self, context=None):
		self.context = context
		return self

	def added_to(self, other):
		return None, self.illegal_operation(other)

	def subbed_by(self, other):
		return None, self.illegal_operation(other)

	def multed_by(self, other):
		return None, self.illegal_operation(other)

	def dived_by(self, other):
		return None, self.illegal_operation(other)

	def powed_by(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_eq(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_ne(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_lt(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_gt(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_lte(self, other):
		return None, self.illegal_operation(other)

	def get_comparison_gte(self, other):
		return None, self.illegal_operation(other)

	def anded_by(self, other):
		return None, self.illegal_operation(other)

	def ored_by(self, other):
		return None, self.illegal_operation(other)

	def notted(self,other):
		return None, self.illegal_operation(other)

	def execute(self, args):
		return RTResult().failure(self.illegal_operation())

	def copy(self):
		raise Exception('No copy method defined')

	def is_true(self):
		return False

	def illegal_operation(self, other=None):
		if not other: other = self
		return RunTimeError(
			self.pos_start, other.pos_end,
			'Illegal operation',
			self.context
		)

class Number(Value):
	def __init__(self, value):
		super().__init__()
		self.value = value

	def added_to(self, other):
		if isinstance(other, Number):
			return Number(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def subbed_by(self, other):
		if isinstance(other, Number):
			return Number(self.value - other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def multed_by(self, other):
		if isinstance(other, Number):
			return Number(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def dived_by(self, other):
		if isinstance(other, Number):
			if other.value == 0:
				return None, RunTimeError(
					other.pos_start, other.pos_end,
					'Division by zero',
					self.context
				)

			return Number(self.value / other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def moded_by(self, other):
		if isinstance(other, Number):
			return Number(self.value % other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def powed_by(self, other):
		if isinstance(other, Number):
			return Number(self.value ** other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_eq(self, other):
		if isinstance(other, Number):
			return Number((self.value == other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_ne(self, other):
		if isinstance(other, Number):
			return Number((self.value != other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_lt(self, other):
		if isinstance(other, Number):
			return Number((self.value < other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_gt(self, other):
		if isinstance(other, Number):
			return Number((self.value > other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_lte(self, other):
		if isinstance(other, Number):
			return Number((self.value <= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def get_comp_gte(self, other):
		if isinstance(other, Number):
			return Number((self.value >= other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def anded_by(self, other):
		if isinstance(other, Number):
			return Number((self.value and other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def ored_by(self, other):
		if isinstance(other, Number):
			return Number((self.value or other.value)).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def notted(self):
		return Number(True if self.value == 0 else False).set_context(self.context), None

	def copy(self):
		copy = Number(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)
		return copy

	def is_true(self):
		return self.value != 0

	def __str__(self):	
		return str(self.value)
	
	def __repr__(self):
		return str(self.value)

Number.null=Number(0)
Number.false=Number(0)
Number.true=Number(1)
Number.mpi=Number(math.pi)

class String(Value):
	def __init__(self, value):
		super().__init__()
		self.value = value

	def added_to(self, other):
		if isinstance(other, String):
			return String(self.value + other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def multed_by(self, other):
		if isinstance(other, Number):
			return String(self.value * other.value).set_context(self.context), None
		else:
			return None, Value.illegal_operation(self, other)

	def is_true(self):
		return len(self.value) > 0

	def copy(self):
		copy = String(self.value)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)
		return copy

	def __str__(self):
		return self.value

	def __repr__(self):
		return f'"{self.value}"'

class List(Value):
	def __init__(self, elements):
		super().__init__()
		self.elements = elements
	
	def added_to(self, other):
		new_list = self.copy()
		new_list.elements.append(other)
		return new_list, None
		
	def subbed_by(self, other):
		if isinstance(other, Number):
			new_list = self.copy()
			try:
				new_list.elements.pop(other.value)
				return new_list, None
			except:
				return None, RunTimeError(
          other.pos_start, other.pos_end,
          'Element at this index could not be removed from list because index is out of bounds',
          self.context
        )
		else:
			return None, Value.illegal_operation(self, other)
	
	def multed_by(self, other):
		if isinstance(other, List):
			new_list = self.copy()
			new_list.elements.extend(other.elements)
			return new_list, None
		else:
			return None, Value.illegal_operation(self, other)
			
	def dived_by(self, other):
		if isinstance(other, Number):
			try:
				return self.elements[other.value], None
			except:
				return None, RunTimeError(
          other.pos_start, other.pos_end,
          'Element at this index could not be retrieved from list because index is out of bounds',
          self.context
        )
		else:
			return None, Value.illegal_operation(self, other)
  	
	def copy(self):
		copy = List(self.elements)
		copy.set_pos(self.pos_start, self.pos_end)
		copy.set_context(self.context)
		return copy
	def __str__(self):
		return ", ".join([str(x) for x in self.elements])
	def __repr__(self):
		return f'[{", ".join([repr(x) for x in self.elements])}]'

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.pos_start)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(RunTimeError(
        self.pos_start, self.pos_end,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(RunTimeError(
        self.pos_start, self.pos_end,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.should_return(): return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)

class Function(BaseFunction):
	def __init__(self, name, body_node, arg_names,should_auto_return):
		super().__init__(name)
		self.body_node = body_node
		self.arg_names = arg_names
		self.should_auto_return=should_auto_return

	def execute(self, args):
		res = RTResult()
		interpreter = Interpreter()
		exec_ctx = self.generate_new_context()

		res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
		if res.should_return() : return res

		value = res.register(interpreter.visit(self.body_node, exec_ctx))
		if res.should_return() and res.func_return_value== None: return res

		ret_value= (value if self.should_auto_return else None) or res.func_return_value or Number.null
		return res.success(ret_value)

	def copy(self):
		copy = Function(self.name, self.body_node, self.arg_names,self.should_auto_return)
		copy.set_context(self.context)
		copy.set_pos(self.pos_start, self.pos_end)
		return copy

	def __repr__(self):
		return f"<function {self.name}>"

class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  def execute_print(self,exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return RTResult().success(Number.null)
  execute_print.arg_names = ['value']
  
  def execute_print_ret(self, exec_ctx):
    return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
  execute_print_ret.arg_names = ['value']
  
  def execute_input(self,exec_ctx):
    text = input()
    return RTResult().success(String(text))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f"'{text}' must be an integer. Try again!")
    return RTResult().success(Number(number))
  execute_input_int.arg_names = []

  def execute_clrscr(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls') 
    return RTResult().success(Number.null)
  execute_clrscr.arg_names = []

  def execute_isnum(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_isnum.arg_names = ["value"]

  def execute_isstr(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_isstr.arg_names = ["value"]

  def execute_islist(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_islist.arg_names = ["value"]

  def execute_isfun(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_isfun.arg_names = ["value"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    list_.elements.append(value)
    return RTResult().success(Number.null)
  execute_append.arg_names = ["list", "value"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        'Element at this index could not be removed from list because index is out of bounds',
        exec_ctx
      ))
    return RTResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_ccat(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "Second argument must be list",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RTResult().success(Number.null)
  execute_ccat.arg_names = ["listA", "listB"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_exec(self, exec_ctx):
    fn = exec_ctx.symbol_table.get("fn")

    if not isinstance(fn, String):
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        "Second argument must be string",
        exec_ctx
      ))

    fn = fn.value

    try:
      with open(fn, "r") as f:
        script = f.read()
    except Exception as e:
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        f"Failed to load script \"{fn}\"\n" + str(e),
        exec_ctx
      ))

    _, error = exec(fn, script)
    
    if error:
      return RTResult().failure(RunTimeError(
        self.pos_start, self.pos_end,
        f"Failed to finish executing script \"{fn}\"\n" +
        error.as_string(),
        exec_ctx
      ))

    return RTResult().success(Number.null)
  execute_exec.arg_names = ["fn"]

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clrscr      = BuiltInFunction("clrscr")
BuiltInFunction.isnum       = BuiltInFunction("isnum")
BuiltInFunction.isstr       = BuiltInFunction("isstr")
BuiltInFunction.islist      = BuiltInFunction("islist")
BuiltInFunction.isfun 	    = BuiltInFunction("isfun")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.ccat        = BuiltInFunction("ccat")
BuiltInFunction.len         = BuiltInFunction("len")
BuiltInFunction.exec        = BuiltInFunction("exec")


#######################################
# CONTEXT
#######################################

class Context:
	def __init__(self, display_name, parent=None, parent_entry_pos=None):
		self.display_name = display_name
		self.parent = parent
		self.parent_entry_pos = parent_entry_pos
		self.symbol_table = None

#######################################
# SYMBOL TABLE
#######################################

class SymbolTable:
	def __init__(self, parent=None):
		self.symbols = {}
		self.parent = parent

	def get(self, name):
		value = self.symbols.get(name, None)
		if value == None and self.parent:
			return self.parent.get(name)
		return value

	def set(self, name, value):
		self.symbols[name] = value

	def remove(self, name):
		del self.symbols[name]



#######################################
# INTERPRETER
#######################################

class Interpreter:
	def visit(self, node, context):
		method_name = f'visit_{type(node).__name__}'
		method = getattr(self, method_name, self.no_visit_method)
		return method(node, context)

	def no_visit_method(self, node, context):
		raise Exception(f'No visit_{type(node).__name__} method defined')

	###################################

	def visit_NumberNode(self, node, context):
		return RTResult().success(
			Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_StringNode(self, node, context):
		return RTResult().success(
			String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
		)

	def visit_ListNode(self, node, context):
		res = RTResult()
		elements = []
		for element_node in node.element_nodes:
			elements.append(res.register(self.visit(element_node, context)))
			if res.should_return(): return res
		return res.success(
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )

	def visit_VarAccessNode(self,node,context):
		res=RTResult()
		var_name=node.var_name_tok.value
		value=context.symbol_table.get(var_name)
		if not value:
			return res.failure(RunTimeError(node.pos_start,node.pos_end,f"'{var_name}' is not defined",context))
		value=value.copy().set_pos(node.pos_start,node.pos_end).set_context(context)
		return res.success(value)

	def visit_VarAssignNode(self,node,context):
		res=RTResult()
		var_name=node.var_name_tok.value
		value=res.register(self.visit(node.value_node,context))
		if res.should_return():  return res
		context.symbol_table.set(var_name,value)
		return res.success(value)

	def visit_BinOpNode(self, node, context):
		res = RTResult()
		left = res.register(self.visit(node.left_node, context))
		if res.should_return(): return res
		right = res.register(self.visit(node.right_node, context))
		if res.should_return(): return res

		if node.op_tok.type == TOK_PLUS:
			result, error = left.added_to(right)
		elif node.op_tok.type == TOK_MINUS:
			result, error = left.subbed_by(right)
		elif node.op_tok.type == TOK_MUL:
			result, error = left.multed_by(right)
		elif node.op_tok.type == TOK_DIV:
			result, error = left.dived_by(right)
		elif node.op_tok.type == TOK_MOD:
			result, error = left.moded_by(right)
		elif node.op_tok.type == TOK_POW:
			result, error = left.powed_by(right)
		elif node.op_tok.type == TOK_EE:
			result, error = left.get_comp_eq(right)
		elif node.op_tok.type == TOK_NE:
			result, error = left.get_comp_ne(right)
		elif node.op_tok.type == TOK_LT:
			result, error = left.get_comp_lt(right)
		elif node.op_tok.type == TOK_GT:
			result, error = left.get_comp_gt(right)
		elif node.op_tok.type == TOK_LTE:
			result, error = left.get_comp_lte(right)
		elif node.op_tok.type == TOK_GTE:
			result, error = left.get_comp_gte(right)
		elif node.op_tok.matches(TOK_KEYWORD, 'AND'):
			result, error = left.anded_by(right)
		elif node.op_tok.matches(TOK_KEYWORD, 'OR'):
			result, error = left.ored_by(right)

		if error:
			return res.failure(error)
		else:
			return res.success(result.set_pos(node.pos_start, node.pos_end))

	def visit_UnaryOpNode(self, node, context):
		res = RTResult()
		number = res.register(self.visit(node.node, context))
		if res.should_return(): return res

		error = None

		if node.op_tok.type == TOK_MINUS:
			number, error = number.multed_by(Number(-1))

		elif node.op_tok.matches(TOK_KEYWORD, 'NOT'):	
			number, error = number.notted()

		if error:
			return res.failure(error)
		else:
			return res.success(number.set_pos(node.pos_start, node.pos_end))

	def visit_IfNode(self, node, context):
		res = RTResult()

		for condition, expr, should_return_null in node.cases:
			condition_value = res.register(self.visit(condition, context))
			if res.should_return(): return res

			if condition_value.is_true():
				expr_value = res.register(self.visit(expr, context))
				if res.should_return(): return res
				return res.success(Number.null if should_return_null else expr_value)

		if node.else_case:
			expr,should_return_null=node.else_case
			else_value = res.register(self.visit(expr, context))
			if res.should_return(): return res
			return res.success(Number.null if should_return_null else else_value)

		return res.success(Number.null)

	def visit_FromNode(self, node, context):
		res = RTResult()
		elements=[]
		start_value = res.register(self.visit(node.start_value_node, context))
		if res.should_return(): return res

		end_value = res.register(self.visit(node.end_value_node, context))
		if res.should_return(): return res

		if node.step_value_node:
			step_value = res.register(self.visit(node.step_value_node, context))
			if res.should_return(): return res
		else:
			step_value = Number(1)

		i = start_value.value

		if step_value.value >= 0:
			condition = lambda: i < end_value.value
		else:
			condition = lambda: i > end_value.value
		
		while condition():
			context.symbol_table.set(node.var_name_tok.value, Number(i))
			i += step_value.value

			value =res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue==False and res.loop_should_break==False: return res
			if res.loop_should_continue:
				continue
      
			if res.loop_should_break:
				break

			elements.append(value)

		return res.success(
			Number.null if node.should_return_null else
			List(elements).set_context(context).set_pos(node.pos_start,node.pos_end))

	def visit_UntilNode(self, node, context):
		res = RTResult()
		elements=[]

		while True:
			condition = res.register(self.visit(node.condition_node, context))
			if res.should_return(): return res

			if not condition.is_true(): break

			value=res.register(self.visit(node.body_node, context))
			if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

			if res.loop_should_continue:
				continue
      
			if res.loop_should_break:
				break

			elements.append(value)

		return res.success(
			Number.null if node.should_return_null else
			List(elements).set_context(context).set_pos(node.pos_start,node.pos_end))

	def visit_FuncDefNode(self, node, context):
		res = RTResult()

		func_name = node.var_name_tok.value if node.var_name_tok else None
		body_node = node.body_node
		arg_names = [arg_name.value for arg_name in node.arg_name_toks]
		func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)
		
		if node.var_name_tok:
			context.symbol_table.set(func_name, func_value)

		return res.success(func_value)

	def visit_CallNode(self, node, context):
		res = RTResult()
		args = []

		value_to_call = res.register(self.visit(node.node_to_call, context))
		if res.should_return(): return res
		value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

		for arg_node in node.arg_nodes:
			args.append(res.register(self.visit(arg_node, context)))
			if res.should_return(): return res

		return_value = res.register(value_to_call.execute(args))
		if res.should_return(): return res
		return_value=return_value.copy().set_pos(node.pos_start,node.pos_end).set_context(context)
		return res.success(return_value)

	def visit_RetNode(self, node, context):
			res = RTResult()

			if node.node_to_return:
				value = res.register(self.visit(node.node_to_return, context))
				if res.should_return(): return res
			else:
				value = Number.null
    
			return res.success_ret(value)

	def visit_ContNode(self, node, context):
			return RTResult().success_cont()

	def visit_BrkNode(self, node, context):
			return RTResult().success_brk()

#######################################
# RUN
#######################################

global_symbol_table=SymbolTable()
global_symbol_table.set("NULL",Number.null)
global_symbol_table.set("FALSE", Number.false)	
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("mpi", Number.mpi)
global_symbol_table.set("print", BuiltInFunction.print)
global_symbol_table.set("print_ret", BuiltInFunction.print_ret)
global_symbol_table.set("input", BuiltInFunction.input)
global_symbol_table.set("input_int", BuiltInFunction.input_int)
global_symbol_table.set("clear", BuiltInFunction.clrscr)
global_symbol_table.set("clrscr", BuiltInFunction.clrscr)
global_symbol_table.set("isnum", BuiltInFunction.isnum)
global_symbol_table.set("isstr", BuiltInFunction.isstr)
global_symbol_table.set("islist", BuiltInFunction.islist)
global_symbol_table.set("isfun", BuiltInFunction.isfun)
global_symbol_table.set("append", BuiltInFunction.append)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("ccat", BuiltInFunction.ccat)
global_symbol_table.set("len", BuiltInFunction.len)
global_symbol_table.set("exec", BuiltInFunction.exec)

def exec(fn, text):
	# Generate tokens
	lexer = Lexer(fn, text)
	tokens, error = lexer.make_tokens()
	if error: return None, error
	
	# Generate AST
	parser = Parser(tokens)
	ast = parser.parse()
	if ast.error: return None, ast.error

	# Run program
	interpreter = Interpreter()
	context = Context('<program>')
	context.symbol_table=global_symbol_table
	result = interpreter.visit(ast.node, context)

	return result.value, result.error