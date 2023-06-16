
"""

argument format:

nonterminal_list: ["N1", "N2", ..., "Nn"]
bnf_set: {"N1": ["v1 v2 ... vn", "v1 v2 ... vn", ...]
          "N2": ...
          ...:
          Nn: ...
	}

"""

def make_nullable(nonterminal_list, bnf_set):
	nullable = dict()
	for n in nonterminal_list:
		nullable[n] = False

	while True:
		changed = False
		for Vn in nonterminal_list:                  # for each nonterminal vocabulary
			for candidate in bnf_set[Vn]:           # for each candidate

				all_token_nullable = True
				for token in candidate.split(' '):      # for each vocabulary of bnf's rhs
					if (token not in nonterminal_list):
						if token != 'ε':
							all_token_nullable = False
					elif nullable[token] == False: 
						all_token_nullable = False
				if all_token_nullable:
					if not nullable[Vn] == True:
						nullable[Vn] = True
						changed = True
		if not changed: break
	return nullable

def make_first(nonterminal_list, bnf_set):
	nullable = make_nullable(nonterminal_list, bnf_set)
	first = dict()

	#initialize first set
	for Vn in nonterminal_list:
		first[Vn] = set() 

	while True:
		changed = False
		for Vn in nonterminal_list:
			for candidate in bnf_set[Vn]:
				# for each bnf				
				previous_tokens_nullable = True
				for token in candidate.split(' '):
					if token not in nonterminal_list:
						if previous_tokens_nullable:
							if token not in first[Vn]:
								first[Vn] |= {token}
								changed = True
							previous_tokens_nullable = False

						if (token not in first) and (token != 'ε'):
							first[token] = {token}
							changed = True
					else: 
						# must be a nonterminal
						if previous_tokens_nullable:
							if not (first[token] - {'ε'}).issubset(first[Vn]):
								first[Vn] |= (first[token] - {'ε'})
								changed = True
						if not nullable[token]:
							previous_tokens_nullable = False
				if previous_tokens_nullable:
					if 'ε' not in first[Vn]:
						first[Vn].add('ε')
						changed = True
		if not changed:
			break
	return (nullable, first)

def make_follow(nonterminal_list, bnf_set):
	# assume the first nonterminal of nonterminal_list is the beginning symbol

	nullable, first = make_first(nonterminal_list, bnf_set)
	follow = dict()
	#initialize
	for Vn in nonterminal_list:
		follow[Vn] = set()
	follow[nonterminal_list[0]] = {'$'}

	while True:
		changed = False
		for Vn in nonterminal_list:
			for candidate in bnf_set[Vn]:
				# for each bnf				
				tokens = candidate.split(' ')
				for i in range(0, len(tokens)):
					if tokens[i] not in nonterminal_list:
						continue
					previous_tokens_nullable = True
					for j in range(i + 1, len(tokens)):
						if tokens[j] in nonterminal_list:
							if not follow[tokens[i]].issuperset(first[tokens[j]] - {'ε'}):
								follow[tokens[i]] |= (first[tokens[j]] - {'ε'})
								changed = True
							if not nullable[tokens[j]]:
								previous_tokens_nullable = False
								break
						else:
							# tokens[j] is a terminal
							previous_tokens_nullable = False
							if tokens[j] not in follow[tokens[i]]:
								follow[tokens[i]] |= {tokens[j]}
								changed = True
							break
					if previous_tokens_nullable:
						if not follow[tokens[i]].issuperset(follow[Vn]): 
							follow[tokens[i]] |= follow[Vn]
							changed = True
		if not changed:
			break
	return (nullable, first, follow)

def make(nonterminal_list, bnf_set):
	return make_follow(nonterminal_list, bnf_set)

ns   = ['Expr', 'Expr_', 'Term', 'Term_', 'Atom', 'Stars']
bnfs = {'Expr': ['Term Expr_'], 
        'Expr_': ['| Term', 'ε'],
        'Term': ['Atom Term_'],
        'Term_': ['Term', 'ε'], 
        'Atom' : ['( Expr ) Stars', 'α Stars'], 
        'Stars': ['* Stars', 'ε']
        } 

nullable, first, follow = make(ns, bnfs)

print("nullable set is: {}\nfirst set is: {}\nfollow set is: {}\n".format(nullable, first, follow))	

'''
nullable set is: {'Expr': False, 'Expr_': True, 'Term': False, 'Term_': True, 'Atom': False, 'Stars': True}
first set is: {
	'Expr': {'α', '('}, 
	'Expr_': {'|', 'ε'}, 
	'Term': {'α', '('}, 
	'Term_': {'α', 'ε', '('}, 
	'Atom': {'α', '('}, 
	'Stars': {'*', 'ε'}, 
	'|': {'|'}, 
	'(': {'('}, 
	')': {')'}, 
	'α': {'α'}, 
	'*': {'*'}
}
follow set is: {
	'Expr': {')', '$'}, 
	'Expr_': {')', '$'}, 
	'Term': {')', '$', '|'}, 
	'Term_': {'$', ')', '|'}, 
	'Atom': {'$', 'α', '(', ')', '|'}, 
	'Stars': {'$', 'α', '(', ')', '|'}
}
'''

'''

Regular Expression Grammer:

Expr  -> Term Expr'
Expr' -> | Term
      -> ε
Term  -> Atom Term'
Term' -> . Term
      -> ε
Atom  -> ( Expr ) Stars
      -> α Stars
Stars -> * Stars
      -> ε

// Expr_ == Expr'
// Term_ == Term'
// α is any meta character in the alphabet
// . is expression combine operator
Output:


nullable set is: {'Expr': False, 'Expr_': True, 'Term': False, 'Term_': True, 'Atom': False, 'Stars': True}
first set is: {
	'Expr': {'α', '('}, 
	'Expr_': {'ε', '|'}, 
	'Term': {'α', '('}, 
	'Term_': {'ε', '.'}, 
	'Atom': {'α', '('}, 
	'Stars': {'*', 'ε'}, 
	'|': {'|'}, 
	'.': {'.'}, 
	'(': {'('}, 
	')': {')'}, 
	'α': {'α'}, 
	'*': {'*'}}
follow set is: {
	'Expr': {'$', ')'}, 
	'Expr_': {'$', ')'}, 
	'Term': {'$', ')', '|'}, 
	'Term_': {'$', '|', ')'}, 
	'Atom': {'.', '$', '|', ')'}, 
	'Stars': {'.', '$', '|', ')'}
}

'''
'''
my bnf:


[ExprList] : list 
"string"   : string
integer    : integer
true/false : boolean
null       : meta_n
(a, b, ...)->(Expr) : lambda expression

'''

'''
output 1(formatted by hand):

nullable set is: {'E': False, 'EList': True, 'Name': False}
first set is: {
'E': {'(', 'string', 'identifier', 'keyword', 'number'}, 
'EList': {'string', 'ε', 'identifier', 'keyword', '(', 'number'}, 
'Name': {'identifier', 'keyword'}, 
'(': {'('}, 
')': {')'}, 
'number': {'number'}, 
'string': {'string'}, 
'identifier': {'identifier'}, 
'keyword': {'keyword'}
}
follow set is: {
'E': {'(', 'keyword', '$', ')', 'identifier', 'number', 'string'}, 
'EList': {')'}, 
'Name': {'(', 'keyword', '$', ')', 'identifier', 'number', 'string'}}

'''

'''
output 2
nullable set is: {'E': False, 'EList': True, 'Name': False}
first set is: {
'E': {'string', 'number', '(', 'keyword', '[', 'identifier'}, 
'EList': {'(', 'keyword', 'identifier', 'string', 'number', 'ε', '['}, 
'Name': {'keyword', 'identifier'}, '(': {'('}, ')': {')'}, 'number': {'number'}, 
'string': {'string'}, 
'[': {'['}, 
']': {']'}, 
'identifier': {'identifier'}, 
'keyword': {'keyword'}}
follow set is: {
'E': {'(', 'keyword', ')', 'identifier', 'string', 'number', ']', '[', '$'}, 
'EList': {')', ']'}, 
'Name': {')', 'identifier', '[', '$', '(', 'keyword', 'string', 'number', ']'}}
'''
