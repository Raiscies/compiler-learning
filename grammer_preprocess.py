'''

grammer-preprocess.py

	generate some useful sets for grammer parsing, including:
	first-set
	follow-set
	nullable-set

	SLR(1) generator
	Canonical LR / LR(1) generator
	LALR(1) generator
	
	SLR(1) PDA
	LR(1)  PDA
	...
	
	

	BNF(CFG) grammer:
	G := (V, T, P, S), where S ∈ V

'''


import regex as re
import queue as que
from copy import copy
from enum import Enum, auto

class end_token:
	def __eq__(self, other):
		return isinstance(other, end_token) 
	def __ne__(self, other):
		return not isinstance(other, end_token)
	def __str__(self):
		return '%end%'
	def __repr__(self):
		return '%end%'
	def __hash__(self):
		return hash(repr(self))


class production: # grammer production type(BNF)
	head = str()
	body = list[str]()
	def __init__(self, head_: str, body_: list[str]):
		self.head = head_
		self.body = body_
	def __str__(self):
		return "{: <3} -> {}".format(self.head, ' '.join(self.body))
	def __eq__(self, other):
		if self.head != other.head or len(self.body) != len(other.body): return False
		for p, q in zip(self.body, other.body):
			if p != q: return False
		return True
	def __ne__(self, other):
		return not self == other
	def __hash__(self):
		return hash([self.head].extend(self.body))

	def __copy__(self):
		return production(self.head, self.body.copy())
		
def print_dictset(dictset: dict[str, set[str]]):
	for k, v in dictset.items():
		print('{: <5} : {}'.format(k, ', '.join(v)))

def print_itemset(items):
	(list_of_tiems := list(items)).sort(key = lambda item: item.is_kernel, reverse = True)
	print('{}\n'.format('\n'.join([str(item) for item in list_of_tiems])))


def print_productions(P: list[production]):
	# print('Start = <{}>'.format(P[0].head))
	for i, p in enumerate(P): print('{: <4} {}'.format(str(i) + '.', str(p)))

def print_all(gen):
	print('--------grammer--------')
	print('G := (V, T, P, S)')
	print('V: {}\nT: {}\nS: {}\nP:'.format(', '.join(gen.g.V), ', '.join(gen.g.T), gen.g.S))
	print_productions(gen.g.P)
	print('G is a LL(1) grammer.' if gen.check_ll1() else 'G is not a LL(1) grammer.')
	print('-------nullable--------')
	for v, b in gen.nullable.items(): 
		if v in gen.g.V: print('{: <5} : {}'.format(v, b))      # don't print the terminal's nullable set 
	print('--------first----------')
	print_dictset({k : v for k, v in gen.first.items() if k not in gen.g.T}) # don't print the terminal's first set 
	print('--------follow---------')
	print_dictset(gen.follow)
	print('--------select---------')
	for i, s in enumerate(gen.select): print('{: <3} {:<20} : {}'.format(str(i) + '.', str(gen.g.P[i]), ' '.join(s)))

class grammer:
	V = set[str]() # a grammer Variable set, each of a variable is a string.
	T = set[str]() # a grammer Terminal set, each of a terminal is a string.
	P = list[production]() # a grammer Principle set, contain objects of bnf
	S = str()    # Start Variable of the grammer

	def __init__(self, V = set(), T = set(), P = list(), S = str()):
		self.V = V
		self.T = T
		self.P = P
		self.S = S

	def __copy__(self):
		return grammer(self.V.copy(), self.T.copy(), self.P.copy(), self.S.copy())

def lex(s: str) -> list[production]:
	# bnf string ' A -> V1 op V2 num; '

	# separator is blank or some non-assosiated tokens
	result = list[production]()

	last_v = str()
	for p in s.strip(' \n\t\v\f\r').split('\n'):
		# print(p)
		if (p := p.strip(' \n\t\v\f\r')) == '': continue # skip empty line

		v = re.search(r"(?=\s*)\w+\'*(?=\s*\-\>.*)", p)
		body = re.findall(r"\w+\'*|[^\s\w]", p[v.span()[1]:] if v != None else p)[2:]
		result.append(production(v.group() if v != None else last_v.group(), body if len(body) != 0 else ['ε']))
		if v != None: last_v = v 
	return result

class generator:
	g = grammer()
	nullable = dict[str, bool]()
	first    = dict[str, set[str]]()
	follow   = dict[str, set[str]]()
	select   = list[set[str]]()

	def __copy__(self):
		return generator(self.g.P.copy(), self.g.S)

	def generate_first(self, P: set[production]):
		V = {v.head for v in P} # variable set
		T = {x for p in P for x in p.body if x not in V and x != 'ε'} # terminal set
		T.add('$')

		# for p in P: 
		# 	for x in p.body: 
		# 		if x not in V and x != 'ε': T.add(x)

		# compute nullable set
		nullable = {x: False for x in V | T}
		for p in P:
			if(p.body[0] == 'ε'): nullable[p.head] = True

		(first := {x: set() for x in V } | {x: {x} for x in T }).pop('ε', None)

		while True:
			changed = False
			for p in P:

				if p.body[0] == 'ε': 
					# an empty expression body
					if 'ε' not in first[p.head]:
						first[p.head].add('ε')
						changed = True
					continue

				all_nullable = True

				for x in p.body:
					# for each token of the production x
					if not first[p.head].issuperset(first[x] - {'ε'}): 
						first[p.head] |= first[x] - {'ε'}
						changed = True
					if not nullable[x]:
						# interrupt the loop 
						all_nullable = False
						break
				if all_nullable and 'ε' not in first[p.head]:
					first[p.head].add('ε') 
					nullable[p.head] = True
					changed = True

			if not changed: break

		self.g.V = V
		self.g.T = T
		self.g.P = P
		self.nullable = nullable
		self.first = first

	def generate_follow(self, P: list[production], S: str):
		follow = {v: set() for v in self.g.V}
		follow[S].add('$')

		while True:
			changed = False
			for p in P:
				for i, tok in enumerate(p.body):
					if tok in self.g.T or tok == 'ε': continue # tok is a terminal or ε
					
					follow_all_nullable = True
					for follow_tok in (p.body[i+1:]):
						if not (new_follow_toks := self.first[follow_tok] - {'ε'}).issubset(follow[tok]):
							follow[tok] |= new_follow_toks
							changed = True
						if not self.nullable[follow_tok]:
							follow_all_nullable = False 
							break
					if follow_all_nullable:
						if not (new_follow_toks := follow[p.head]).issubset(follow[tok]):
							follow[tok] |= new_follow_toks
							changed = True


			if not changed: break
		self.g.S = S
		self.follow = follow


	def first_of_seq(self, seq: list[str]) -> set[str]:
		# generate the first set of a sequence seq
		if not seq: return {'ε'}
		if seq[0] == 'ε': return {'ε'}

		result = set[str]()
		for x in seq:
			if x in self.g.V:
				result |= self.first[x] - {'ε'}
				if not self.nullable[x]: 
					return result
			else:
				# x is T or some special symbols for techinical processing, but not a variable of V
				result.add(x)
				return result
		
		result.add('ε')
		return result

	def nullable_of_seq(self, seq: list[str]) -> bool:
		return (len(seq) == 1 and seq[0] == 'ε') or sum([self.nullable[tok] for tok in seq]) == len(seq) # all of the tokens are nullable

	def generate_select(self, P):
		select = list[set[str]]()
		for p in P:
			first_of_body = self.first_of_seq(p.body)
			select.append((first_of_body - {'ε'}) | self.follow[p.head] if 'ε' in first_of_body else first_of_body)
		self.select = select

	def find_empty_expression_of(self, v):
		for i, p in enumerate(self.g.P):
			if p.head != v: continue
			if p.body[0] == 'ε':
				return i
		return -1


	def add_non_empty_expression(self, v: str, p: production):
		
		q = que.SimpleQueue()
		q.put(p.body)
		while not q.empty():
			this_body = q.get()
			if len(this_body) == 1 and this_body[0] == v:
				continue # V -> αAβ, αβ = ε

			for i, tok in enumerate(this_body):
				if tok == v:
					(new_body := this_body.copy()).pop(i)
					new_p = production(p.head, new_body)
					if self.g.P.count(new_p) == 0:
						self.g.P.append(new_p)
						if new_body.count(v) != 0:
							q.put(new_body)

		
	def remove_empty_productions(self):
		# remove all of the productions that A -> ε, except of the start variable S if S is nullable
		if self.nullable[self.g.S]:
			new_s = self.g.S + '\''
			(P := [production(new_s, [self.g.S]), production(new_s, ['ε'])]).extend(self.g.P)
			# re-generate the grammer g
			self.generate_first(P)          # generate nullable, first and g(except of g.S)
			self.generate_follow(P, new_s)  # generate follow
			self.generate_select(P)         # generate select

		for v in self.g.V:
			if not self.nullable[v] or v == self.g.S: continue
			if (i := self.find_empty_expression_of(v)) != -1:
				self.g.P.pop(i)
			
			for p in self.g.P:
				# why?
				# if not self.nullable[p.head] or 
				if p.body.count(v) == 0: continue
				self.add_non_empty_expression(v, p)

		self.update_sets()

	def flatten_single_productions(self, root_variable, unflattened_variables, current_new_productions):
		# returns non_single_bodys

		# new_productions = []
		# (q := que.SimpleQueue()).put(root_variable)
		unflattened_variables.discard(root_variable)
		# non_single_bodys = set()
		for root_candidate in [p for p in self.g.P if p.head == root_variable]:
			if not (len(root_candidate.body) == 1 and root_candidate.body[0] in self.g.V):
				# not a single production
				current_new_productions.append(root_candidate)

			else:
				# is a single production
				if root_candidate.body[0] in unflattened_variables:
					self.flatten_single_productions(root_candidate.body[0], unflattened_variables, current_new_productions)
					# current_new_productions.extend([production(root_variable, p.body) for p in current_new_productions if p.head == root_candidate.body[0]])
				# else:
					# v := root_candidate.body[0] has been flattened
				current_new_productions.extend([production(root_variable, p.body) for p in current_new_productions if p.head == root_candidate.body[0]])


	def remove_single_productions(self):
		# if root_variable is None: root_variable = self.g.S
		new_productions = []
		unflattened_variables = self.g.V.copy()

		self.flatten_single_productions(self.g.S, unflattened_variables, new_productions)
		while unflattened_variables:
			self.flatten_single_productions(unflattened_variables.pop(), unflattened_variables, new_productions)

		self.g.P = new_productions
		self.update_sets()

	def remove_direct_left_recursion(self, v: str, P: list[production], allow_empty_production): 
		# remove direct left recursion of v - productions

		new_v = v + '\''
		new_productions = []
		v_recur_bodys_removed_first_v = []
		v_not_recur_bodys = []

		no_direct_left_recursion = True
		for p in P:
			if p.head == v:
				# for all v_candidates
				if p.body[0] == v:
					# assume not exists single production (X -> V ∉ P)
					v_recur_bodys_removed_first_v.append(p.body[1:]) 
					no_direct_left_recursion = False
				else:
					v_not_recur_bodys.append(p.body)
			else:
				# not v_candidates
				new_productions.append(p)

		if no_direct_left_recursion: 
			return P

		for β in v_not_recur_bodys:

			new_productions.append(production(v, β + [new_v]))
		if allow_empty_production:
			for α in v_recur_bodys_removed_first_v:
				new_productions.append(production(new_v, α + [new_v]))
			new_productions.append(production(new_v, ['ε']))
		else:
			for α in v_recur_bodys_removed_first_v:
				new_productions.append(production(new_v, α + [new_v]))
				new_productions.append(production(new_v, α))

		return new_productions

	def remove_left_recursion(self, allow_empty_production = False, by_order = False):
		new_productions = []
		replaced_variables = set()

		print('allowed empty production.' if allow_empty_production else 'not allow empty production.')
		print('order of remove left recursion: ', end = '')
		variable_seq = self.variable_order() if by_order else self.g.V
		for v in variable_seq:
			# print('--', end = ' ')
			print(v, end = ' ')
			# print('--')
			direct_v_candidates = []

			for v_candidate in [p for p in self.g.P if p.head == v]:
				if v_candidate.body[0] in replaced_variables:
					candidates_of_body_first = [p for p in new_productions if p.head == v_candidate.body[0]]
					# replace productions
					direct_v_candidates.extend([production(v, p.body + v_candidate.body[1:]) for p in candidates_of_body_first])
				else:
					direct_v_candidates.append(v_candidate)

			replaced_variables.add(v)
			new_productions.extend(self.remove_direct_left_recursion(v, direct_v_candidates, allow_empty_production))

		print()
		self.g.P = new_productions
		# print_productions(self.g.P)
		self.update_sets()

	def check_ll1(self):
		# check if g is a LL(1) grammer
		# Grammer G is LL(1)'s iff ∀ (A -> α | β) ∈ G, 
		# satisfied: 
		# 1. if α, β ≠>* ε, then first(α) ∩ first(β) = Φ
		# 2. α ≠>* ε or β ≠>* ε
		# 3. if α =>* ε, then first(β) ∩ follow(A) = Φ
		for v in self.g.V:
			v_candidates = [p for p in self.g.P if p.head == v]
			if self.nullable[v]:
				# check only one v_candidate is nullable
				nullable_index = -1
				for i, vc in enumerate(v_candidates):
					if self.nullable_of_seq(vc.body):
						if nullable_index == -1:
							nullable_index = i
						else: return False # more then one candidates are nullable
				v_candidates.pop(i)
				for vc in v_candidates: 
					if not (self.first_of_seq(vc.body) & self.first[v]): return False

			# v is not nullable or v is nullable but passed the privious test
			if len(v_candidates) == 0: return True
			u = self.first_of_seq(v_candidates[0].body)

			for vc in v_candidates[1:]: 
				if len(u & (f := self.first_of_seq(vc.body))) == 0:
					u |= f
				else: return False

		return True	
					


	def from_production(self, P: set[production], S: str):
		self.generate_first(P)      # generate nullable, first and g(except of g.S)
		self.generate_follow(P, S)  # generate follow
		self.generate_select(P)     # generate select
		# self.remove_empty_productions()

	def update_sets(self):
		self.generate_first(self.g.P)
		self.generate_follow(self.g.P, self.g.P[0].head)
		self.generate_select(self.g.P)


	def remove_verbose_producions_and_sort(self):
		q = que.SimpleQueue()
		order = [self.g.S]
		q.put(self.g.S)
		while not q.empty():
			v = q.get()
			for v_candidate in [p for p in self.g.P if p.head == v]:
				for tok in v_candidate.body:
					if tok in self.g.V and tok not in order:
						order.append(tok)
						q.put(tok)

		# remove all of the verbose producions and sort
		new_productions = []
		for v in order:
			new_productions.extend([p for p in self.g.P if p.head == v])
		self.g.P = new_productions
		self.update_sets()

	def variable_order(self):
		q = que.SimpleQueue()
		order = [self.g.S]
		q.put(self.g.S)
		while not q.empty():
			v = q.get()
			for v_candidate in [p for p in self.g.P if p.head == v]:
				for tok in v_candidate.body:
					if tok in self.g.V and tok not in order:
						order.append(tok)
						q.put(tok)
		return order

	def __init__(self, P, S = None):
		if not P: return
		if S == None: S = P[0].head 
		self.from_production(P.copy(), S)

# LR(0) item
class item_lr0:
	prod = None # production
	ppos = 0    # point position

	is_kernel = False # identifiy the kernel
	# ppos:      0 1 2 3
	#            . . . .
	# prod:  A -> p q r
	# prod index: 0 1 2

	def __init__(self, prod, ppos = 0, is_kernel = False):
		self.prod = prod
		if self.prod.body[0] == 'ε': ppos = 1
		else: self.ppos = ppos

		self.is_kernel = is_kernel

	def __eq__(self, other):
		return self.ppos == other.ppos and self.prod == other.prod;
	def __ne__(self, other):
		return not self == other
	def __hash__(self):
		return hash((self.prod, self.ppos))
	# def __copy__(self):
	# 	return item_lr0(prod, ppos, is_kernel) 

	def __str__(self):
		s = '{}{} {: <3} -> '.format('!' if self.is_kernel else ' ', '$' if self.is_reduction_item() else ' ', self.prod.head)
		
		if len(self.prod.body) == 1 and self.prod.body[0] == 'ε': 
			return s + '· '
		
		for i, b in enumerate(self.prod.body):

			if i == self.ppos:
				s += '· '
				s += ' '.join(self.prod.body[i:])
				return s
			s += b
			s += ' '
		return s + '· '
		# return "{: <3} -> {}".format(self.prod.head, ' '.join(self.prod.body))

	def current_tok(self):
		return self.prod.body[self.ppos] if self.ppos < len(self.prod.body) else 'ε'
	def next(self):
		if self.prod.body[0] == 'ε': 
			return self.copy()

		return item_lr0(self.prod, (self.ppos + 1 if self.ppos <= len(self.prod.body) else len(self.prod.body)), is_kernel = True)

		# is a reduction item OR an acctption item
	def is_reduction_item(self):
		return self.ppos >= len(self.prod.body)


class action_category(Enum):
	SHIFT = 's'
	REDUCE  = 'r'
	ACCEPT  = 'acc'
	ERROR   = 'x' 
	GOTO    = 'goto '

	NONE    = 'N' # a placeholder



# a SLR(1) PushDown Automaton
class slr_pda:

	# G := (V, T, P, S)
	# SLR(1) PDA M := ( Q = {q}, 
	#                   Σ = T, 
	#                   Γ = items_collection, 
	#                   δ = action,
	#                   q0 = q,
	#                   z0 = $,
	#                   F = Φ ) 

	g: grammer # used to reduction 
	action = None # : list[dict[str | {end_token}, tuple[action_category, int]]]

	def generate_action(self, follow, items_collection, goto_table: list[dict[str, int]]):
		# follow = self.g.follow
		# V = self.g.V
		T = self.g.T
		self.action = [] # : list[dict[str | {end_token}, tuple[action_category, int]]]
		for index, items in enumerate(items_collection):
			# index: index of this item set
			# items: a set of productions with points
			self.action.append(dict())
			# self.action[index]...
			for item in items:
				if item.is_reduction_item():
					if item.prod.head == self.g.S:
						# item is an acception item set
						self.action[index][end_token()] = (action_category.ACCEPT, None)
					else:
						for x in follow[item.prod.head]:
							# item is a reduction item set
							index_of_production = self.g.P.index(item.prod)
							self.action[index][x if x != '$' else end_token()] = (action_category.REDUCE, index_of_production)
				else: # this item isn't a reduction item
					for x, target_index in goto_table[index].items():
						if x in T:
							self.action[index][x] = (action_category.SHIFT, target_index)
						else: # x in V
							self.action[index][x] = (action_category.GOTO, target_index)

	 # action : list[dict[str | {end_token}, tuple[action_category, int]]]
	def print_action(self):
		# for d in self.action:
		for index, d in enumerate(self.action):
			print('{: <3}'.format(str(index) + '.'))
			if not d: 
				# print('  Φ')
				continue
			for k, v in d.items():
				if v[0] == action_category.ACCEPT:
					print('  {}: {}  '.format(str(k), v[0].value), end = '')
				# elif v[0] == action_category.GOTO:
				# 	print('  {}: goto {}  '.format(str(k), v[1]), end = '')		
				else:
					print('  {}: {}{}  '.format(str(k), v[0].value, v[1]), end = '')
			print()


	# test a tok sequence toks whether to be accepted by this SLR PDA
	def test(self, toks):
		toks = toks.copy()
		toks.append(end_token())
		stack = [0] # saves the index of item set
		# alias
		push = lambda x: stack.append(x)
		pop  = lambda  : stack.pop()
		top  = lambda  : stack[-1]
		P    = self.g.P
		action = self.action # action[state_index][x] -> (action_category, shift_state_index or reduce_production_index or None)

		tok_index = 0
		print(toks)
		while True:
			tok = toks[tok_index]
			print(stack)
			# print(tok)
			# print(action[top()])
			if tok in action[top()]:
				category, arg = action[top()][tok]
				# select action:
				if category == action_category.SHIFT:
					# shift
					push(arg)
					tok_index += 1
				elif category == action_category.REDUCE:
					# reduce
					# quary the reduce production
					p = P[arg]
					for i in range(len(p.body)): pop()
					push(action[top()][p.head][1]) # actually is push(goto[top()][p.head])
				elif category == action_category.ACCEPT:
					# accept
					return(True, tok_index - 1)
				else:
					# bad action table
					return (False, 'bad teble at index ' + str(tok_index))
			else:
				# error
				return (False, tok_index)

		return (False, len(toks) - 1)

	def __init__(self, slrgen):
		self.g = slrgen.g
		self.generate_action(slrgen.gen.follow, slrgen.items_collection, slrgen.goto)


# SLR generator
class slr_generator:
	gen = None
	g = None

	exists_conflict = False

	# LR(0) / SLR(1) automaton:
	items_collection = list[set]() # [I0, I1, I2, ...]
	goto = list[dict[str, int]]() # goto(i, X) -> i  (i is index of I, X ∈ V | T)


	def print_items(self):
		for index, items in enumerate(self.items_collection):
			# print kernel items first
			(list_of_tiems := list(items)).sort(key = lambda item: item.is_kernel, reverse = True)

			print('{: <3} \n{}\n'.format(str(index) + '.', '\n'.join([str(item) for item in list_of_tiems])))

	def print_goto(self):
		print('valid grammer.' if not self.exists_conflict else 'invalid grammer, exists conflict')
		for index, d in enumerate(self.goto):
			print('{: <3}'.format(str(index) + '.'))
			if not d: 
				# print('  Φ')
				continue
			for k, v in d.items():
				print('  {}: {}  '.format(k, v), end = '')
			print()

	# LR(0) closure
	def closure(self, I: set):
		J = I.copy()
		while True:
			changed = False

			for v in {j.current_tok() for j in J if j.current_tok() in self.gen.g.V}:
				for v_item in {item_lr0(p, is_kernel = False) for p in self.gen.g.P if p.head == v}:
					if v_item not in J:
						J.add(v_item)
						changed = True

			if not changed: break
		return J

	def try_goto(self, I: set, X: str):
		J = set()
		for i in I: 
			if i.current_tok() == X:
				J.add(i.next())
		return self.closure(J) if len(J) != 0 else J

	# LR(0), generate item_lr0 set collection 
	# items function generates items_collection and goto table
	def items(self):
		# C should be a list because GOTO function need to target the items set by index
		C = [ self.closure( { item_lr0(self.g.P[0], is_kernel = True) } ) ] # gen.g.P[0] == [CLOSURE(S' -> ·S)]
		
		goto = [dict()]
		X = self.g.V | self.g.T
		while True:
			changed = False
			for index, I in enumerate(C):
				for x in X:
					if len(J := self.try_goto(I, x)) != 0:
						if J not in C:
							C.append(J)
							goto.append(dict())
							# goto: I * X -> I list[dict[str, int]]
							if x not in goto[index]:
								goto[index][x] = len(C) - 1
							else:
								# a conflict
								goto[index][x] = -1
								exists_conflict = True
							changed = True
						else: # J in C
							goto[index][x] = C.index(J)

			if not changed: break

		self.items_collection = C
		self.goto = goto


	def __init__(self, gen):
		self.gen = copy(gen)
		self.g = self.gen.g
		# widen grammer
		self.g.P.insert(0, production(gen.g.S + '\'', [gen.g.S]))
		self.gen.update_sets()
		self.items()


# LR(1) item
class item_lr1(item_lr0):
	lookahead: str #look ahead token of an item

	def __init__(self, prod, lookahead, ppos = 0, is_kernel = False):
		super().__init__(prod, ppos, is_kernel)
		self.lookahead = lookahead

	#construct a LR(1) item from a LR(0) item(core) and a look ahead character
	@classmethod
	def from_core(cls, core, lookahead):
		return item_lr1(core.prod, lookahead, core.ppos, core.is_kernel)

	def __eq__(self, other):
		return self.ppos == other.ppos and self.prod == other.prod and self.lookahead == other.lookahead;
	def __ne__(self, other):
		return not self == other
	def __hash__(self):
		return hash((self.prod, self.ppos, self.lookahead))

	def __str__(self):
		# print(self.lookahead != end_token(), self.lookahead)
		# return '[' + super().__str__() + ', ' + (self.lookahead if self.lookahead != end_token() else '$') + ']'
		return '{: <20} {: >5}'.format(super().__str__(), '(' + (self.lookahead if self.lookahead != end_token() else '$') + ')')

	def next(self):
		if self.prod.body[0] == 'ε': 
			return self.copy()

		return item_lr1(self.prod, self.lookahead, (self.ppos + 1 if self.ppos <= len(self.prod.body) else len(self.prod.body)), is_kernel = True)

	def closure_lookaheads(self, gen):
		# for an item [A -> αBβ, a]
		# returns a set: first(βa)
		return gen.first_of_seq(self.prod.body[self.ppos + 1:] + [self.lookahead if self.lookahead != end_token() else '$'])

	def core(self):
		return item_lr0(self.prod, self.ppos, self.is_kernel)

	def is_reduction_item(self, lookahead = None):
		return self.ppos >= len(self.prod.body) and (lookahead is None or self.lookahead == lookahead)

# LR(1) Grammer PushDown Automaton
class lr1_pda(slr_pda):


	def __init__(self, lr1gen):
		self.g = lr1gen.g
		self.generate_action(lr1gen.items_collection, lr1gen.goto)

	def generate_action(self, items_collection, goto_table):
		action = []

		for index, items in enumerate(items_collection):
			action.append(dict())
			for item in items:
				if item.is_reduction_item():
					if item.prod.head == self.g.S and item.lookahead == end_token():
						# item is an acception item set
						action[index][end_token()] = (action_category.ACCEPT, None)
					else:
						# item is a reduction item set
						index_of_production = self.g.P.index(item.prod)
						action[index][item.lookahead] = (action_category.REDUCE, index_of_production)
				else: # this item isn't a reduction item
					# shift or goto 
					for x, target_index in goto_table[index].items():
						if x in self.g.T:
							action[index][x] = (action_category.SHIFT, target_index)
						else: # x in V
							action[index][x] = (action_category.GOTO, target_index)

		self.action = action


# Canonical LR(1) Generator 
class lr1_generator:
	gen = None
	g = None # grammer

	# Canonical LR(1) automaton:
	items_collection = list[set]() # [I0, I1, I2, ...]
	goto = list[dict[str, int]]() # goto(i, X) -> i  (i is index of I, X ∈ V | T)


	exists_conflict = False

	def __init__(self, gen, make_augumented_grammer = True):
		self.gen = copy(gen)
		self.g = self.gen.g
		# widen grammer
		if make_augumented_grammer:
			self.g.P.insert(0, production(gen.g.S + '\'', [gen.g.S]))
		self.gen.update_sets()
		self.items()

	# LR(1) automaton:
	items_collection = list[set[item_lr1]]() # [I0, I1, I2, ...]
	goto = list[dict[str, int]]() # goto(i, X) -> i  (i is index of I, X ∈ V | T)

	def print_items(self):
		for index, items in enumerate(self.items_collection):
			# print kernel items first
			(list_of_tiems := list(items)).sort(key = lambda item: item.is_kernel, reverse = True)

			print('{: <3} \n{}\n'.format(str(index) + '.', '\n'.join([str(item) for item in list_of_tiems])))

	def print_goto(self):
		print('valid grammer.' if not self.exists_conflict else 'invalid grammer, exists conflict')
		for index, d in enumerate(self.goto):
			print('{: <3}'.format(str(index) + '.'))
			if not d: 
				# print('  Φ')
				continue
			for k, v in d.items():
				print('  {}: {}  '.format(k, v), end = '')
			print()

	# Canonical LR(1) construction

	# closure of LR(1) item set
	def closure(self, I: set[item_lr1]):
		J = I.copy()
		while True:
			changed = False

			for item in {j for j in J if j.current_tok() in self.gen.g.V}:
				for p in {p for p in self.g.P if p.head == item.current_tok()}:
					for b in item.closure_lookaheads(self.gen):
						if (new_item := item_lr1(p, (b if b != '$' else end_token()), is_kernel = False)) not in J:
							J.add(new_item)
							changed = True
			if not changed: break
		# print_itemset(J)
		return J

	def try_goto(self, I, X):
		J = set()
		for item in I:
			if item.current_tok() == X:
				J.add(item.next())
		return self.closure(J)

	def items(self):
		C = [ self.closure( { item_lr1(gen.g.P[0], lookahead = end_token(), is_kernel = True) } ) ] # gen.g.P[0] == [CLOSURE(S' -> ·S)]
		goto = [dict()]
		
		X = self.g.V | self.g.T

		while True:
			changed = False
			for index, items in enumerate(C):
				for x in X:
					if len(J := self.try_goto(items, x)) != 0:
						if J not in C:
							C.append(J)
							goto.append(dict())
							# goto: I * X -> I list[dict[str, int]]
							if x not in goto[index]:
								goto[index][x] = len(C) - 1
							else:
								# a conflict
								goto[index][x] = -1
								exists_conflict = True
							changed = True
						else: # J in C
							goto[index][x] = C.index(J)
			if not changed: break

		self.items_collection = C
		self.goto = goto

# LALR(1)(Look Ahead LR(1)) Generator
class lalr_generator(slr_generator):
	# gen = None
	# g = None # grammer

	# # LR(0) 
	# items_collection = list[set]() # [I0, I1, I2, ...]
	# goto = list[dict[str, int]]() # goto(i, X) -> i  (i is index of I, X ∈ V | T)

	# exists_conflict = False

	def __init__(self, gen):
		self.gen = copy(gen)
		self.g = self.gen.g
		# widen grammer
		self.g.P.insert(0, production(gen.g.S + '\'', [gen.g.S]))
		self.gen.update_sets()
		self.items()

	def erase_non_kernel_and_indexing(self):
		# erase all of the non-kernel item from the items_collection
		# and convert the item set type from set to list
		self.items_collection = [[item for item in items if item.is_kernel] for items in self.items_collection] # where item is LR(0) item


	def generate_lookahead_propagate_list(self, lr1gen):
		first = self.gen.first_of_seq


		propagate_list = dict[tuple[int, int], set[tuple[int, int]]]()

		# list contains the look ahead grammer symbols of the production 
		# new_items_collection = [list[tuple[item_lr0, list]]() for i in range(len(self.items_collection))]
		lookahead_list = [[set() for item in items] for items in self.items_collection]
		# kernel item [S' -> ·S, $] is spontaneously generated
		# item_collection index: 0 -> { [S' -> ·S] }
		# item index           : 0 -> [S' -> ·S]
		lookahead_list[0][0].add(end_token())
		# new_items_collection[0].add((self.items_collection[0][0], [end_token()]))
		# new_items_collection[0].add(item_lr1.from_core(self.items_collection[0][0], end_token()))

		for i, kernels in enumerate(self.items_collection):
			for j, kernel in enumerate(kernels):
				# for all kernel item: A -> α·β
				# if kernel.current_tok() not in self.g.V: continue # ... in self.g.T is wrong, because of 'ε'
				# for all kernel item: A -> α·Bω

				for item in lr1gen.closure({item_lr1.from_core(kernel, None)}): # LR(1) closure
					if item.is_reduction_item(): continue

					goto_item_set_i = self.goto[i][item.current_tok()]
					goto_item_i = self.items_collection[goto_item_set_i].index(item.next().core())
					target = (goto_item_set_i, goto_item_i)
					# print(item)
					if item.lookahead is None:
						# this lookahead symbol is propagated from kernel
						if (i, j) not in propagate_list: 
							propagate_list[(i, j)] = set()
						propagate_list[(i, j)].add(target)
					else:
						# this lookahead symbol is spontaneously generate
						lookahead_list[goto_item_set_i][goto_item_i].add(item.next().lookahead)

		return lookahead_list, propagate_list


	def propagate(self, lookahead_list, propagate_list):
		while True:
			changed = False

			for start, targets in propagate_list.items():
				# start_items_i, start_item_i = start
				start_lookaheads = lookahead_list[start[0]][start[1]] 
				if len(start_lookaheads) != 0:
					for items_i, item_i in targets:
						target_lookaheads = lookahead_list[items_i][item_i]
						if not target_lookaheads.issuperset(start_lookaheads):
							# propagates from start to target
							target_lookaheads.update(start_lookaheads)
							changed = True
				# print(lookahead_list)
			if not changed: break

		# generate new items_collection
		# new_items_collection = [list[tuple[item_lr0, list]]() for i in range(len(self.items_collection))]
		new_items_collection = list()
		for items_i, items in enumerate(self.items_collection):
			new_items_collection.append(set())
			for item_i, item in enumerate(items):
				new_items_collection[items_i].update({item_lr1.from_core(item, b) for b in lookahead_list[items_i][item_i]})
		self.items_collection = new_items_collection

	def items(self):
		super().items() # generate LR(0) items_collection and goto
		self.erase_non_kernel_and_indexing() 
		
		lr1gen = lr1_generator(self.gen, False)
		lookahead_list, propagate_list = self.generate_lookahead_propagate_list(lr1gen) # new_item_collection is a LALR(1) item set collection
		self.propagate(lookahead_list, propagate_list)
		# print_itemset(self.items_collection)
		

# # test
# P = lex(r'''
# 		S' -> S
# 		S -> E
# 		E -> T | E
# 		T -> F T
# 		F -> char
# 		  -> (E)
# 		  -> F*
# 		  -> F+
#  	''')

# P = lex(r'''
# 	E -> E + T
# 	  -> T
# 	T -> T * F
# 	  -> F
# 	F -> (E)
# 	  -> id
#  ''')

# P = lex('''
# 	S -> C C
# 	C -> c C
# 	  -> d
# ''')

# P = lex(r'''
# 	S -> L = R 
# 	  -> R
# 	L -> * R 
# 	  -> id
# 	R -> L
# ''')

P = lex(r'''

	S -> DeclList Expr 

	DeclList	-> id = literal DeclList'
				-> :
	DeclList'	-> , id = literal DeclList'
				-> :

	Expr	-> Expr binop Expr
			-> preop Expr
			-> ( Expr )
			-> id ( Expr )
			-> [ ExprList ]
			-> IfExpr
			-> WhileExpr
			-> id
			-> literal

	IfExpr		-> if(Expr): Expr ElseExpr
	ElseExpr	-> elif(Expr): Expr ElseExpr
				-> else: Expr
	WhileExpr	-> while(Expr): Expr

	ExprList	-> Expr ExprList'
				->
	ExprList'	-> , Expr ExprList'
				->


''')

# P = lex(r'''
# 	S -> E
# 	E -> E + T
# 	  -> E - T
# 	  -> T
# 	T -> T * F
# 	  -> T / F
# 	  -> F
# 	F -> num
# 	  -> (E)

# 	''')

# P = lex('''
# 	S	-> a A d
# 		-> b B d
# 		-> a B e
# 		-> b A e
# 	A	-> c
# 	B	-> c
# ''')

# P = lex(r'''
# 	S -> A a
# 	  -> b
# 	A -> A c
# 	  -> S d
# 	  -> 
# ''')

# P = lex(r'''
# 	S -> A
# 	  -> w
# 	A -> B
# 	  -> m
# 	B -> b
# 	C -> D
# 	D -> A
# 	  -> S
# 	  ->
# 	S -> S a S b
# 	  -> B B S
# 	''')

gen = generator(P)
print_productions(gen.g.P)
print('-------remove-empty-production--------')
gen.remove_empty_productions()
print_all(gen)
# print('-------remove-single-production-------')
# gen.remove_single_productions()
# print_productions(gen.g.P)
# print('--------remove-left-recursion---------')
# gen.remove_left_recursion(by_order = True, allow_empty_production = True)
# print_productions(
# gen.remove_direct_left_recursion('S', gen.g.P)
# )
# print_productions(gen.g.P)
# print('--------remove-verbose-productions---------')
# gen.remove_verbose_producions_and_sort()
# print_productions(gen.g.P)
# print_all(gen)
# print('---------------SLR-Generator---------------')
# slr_gen = slr_generator(copy(gen))
# print_all(slr_gen.gen)
# print('-------------------items-------------------')
# slr_gen.print_items()
# print('-------------------goto--------------------')
# slr_gen.print_goto()
# print('-----------------SLR-PDA-------------------')
# slr = slr_pda(slr_gen)
# slr.print_action()
# print('-----------------test-PDA------------------')
# seq = ['id', '*', 'id']
# print(' '.join(seq))
# print(slr.test(seq))
# print('----------Canonical-LR-Generator-----------')
# lr1_gen = lr1_generator(generator(copy(P)))
# print_all(lr1_gen.gen)
# print('-------------------items-------------------')
# lr1_gen.print_items()
# print('-------------------goto--------------------')
# lr1_gen.print_goto()
# print('-----------------LR(1)-PDA-----------------')
# lr1 = lr1_pda(lr1_gen)
# lr1.print_action()
# print('-----------------test-PDA------------------')
# seq = ['*', 'id', '=', 'id']
# print(' '.join(seq))
# print(lr1.test(seq))
print('--------------LALR-Generator---------------')
lalr_gen = lalr_generator(gen)
# print_all(lalr_gen.gen)
print('-------------------items-------------------')
lalr_gen.print_items()
print('-------------------goto--------------------')
lalr_gen.print_goto()
print('------------LALR/LR(1)-PDA-----------------')
lalr = lr1_pda(lalr_gen)
lalr.print_action()
print('-----------------test-PDA------------------')
seq = ['id', '=', 'literal', ':', 'id']
print(' '.join(seq))
print(lalr.test(seq))