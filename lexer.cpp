#include <cstdlib>
#include <iostream>
#include <vector>
#include <string>



enum vocabulary: int {

	//nonterminals
	E = 0, 
	Ep,        // E'
	T, 
	Tp,        // T'
	F,  

	//terminals
	NUMBER = 5,  // numbers 
	LPAREN,      // (
	RPAREN,      // )
	ADD,         // +
	MNS,         // -
	MUL,         // *
	DIV,         // /

	EPS          // ε
	
};


constexpr int nonterminal_num = 5;
constexpr int    terminal_num = 7;
constexpr int  vocabulary_num = nonterminal_num + terminal_num;
constexpr int max_candidate_num = 3;
constexpr int max_candidate_len = 3;

/*
	language BNF:
	E  -> T E'
	E' -> + E E' | - E E' | eps
	T  -> F T'
	T' -> * T T' | / T T' | eps
	F  -> num | ( E )

*/

struct bnf {
	vocabulary left; // 产生式左部
	// vocabulary candidate[max_candidate_num][max_candidate_len]; //候选式(右部)
	std::vector<std::vector<vocabulary>> candidate;
} 
bnfs[]  = {
	{E,  {{T, Ep}}                           },
	{Ep, {{ADD, E, Ep}, {MNS, E, Ep}, {EPS}} },
	{T,  {{F, Tp}}                           },
	{Tp, {{MUL, T, Tp}, {DIV, T, Tp}, {EPS}} }, 
	{F,  {{NUMBER}, {LPAREN, E, RPAREN}}     }
};

bool FIRST[vocabulary_num][vocabulary_num] = {false};  //FIRST[N][a] == true: a ∈ FIRST(N)
bool FOLLOW[nonterminal_num][terminal_num] = {false}; //FOLLOW[N][a] == true: a ∈ FOLLOW(N)
bool nullable[nonterminal_num] = false;


constexpr bool is_terminal(vocabulary x) noexcept{ return x >= 5 && x <= 12; }
constexpr bool is_nonterminal(vocabulary x) noexcept{ return x >= 0 && x <= 4; }
constexpr bool is_nullable(bnf& b) {
	for(auto& c: b.candidate) {
		for(auto& v: c) {
			if(c == EPS) return true;
		}
	}
	return false;
}

void generate_nullable_table() {
	for(int i = 0; i < nonterminal_num; ++i) {
		if(is_nullable(bnfs[i])) nullable[i] = true;
	}
}

// a ∪= b
//returns whether a changed
bool union_FIRST(vocabulary a, vocabulary b) {
	bool changed = false;
	for(int i = 0; i < vocabulary_num; ++i) {
		for(int j = 0; j < vocabulary_num; ++j) {
			if(b[i][j]) {
				if(!a[i][j]) {
					a[i][j] = true;
					changed = true;
				}
			}
		} 
	} 
	return changed;
}

void generate_FIRST_table() {
	for(int i = 5; i < 12; i++) {
		//set terminals 
		FIRST[i][i] = true; //including themselves: FIRST(a) = {a}
	}

	bool changed = false;
	do {
		//repeat:
		for(auto& b: bnfs) { 
			for(auto& c: b.candidate) { //for all candidates

			}
		}


	}while(changed);

}

struct token {
	vocabulary category; // should be terminal
	union {
		long long value;
		void* field;
	} attr;

	operator std::string() const{
		std::string s;
		switch(category) {
			case NUMBER: s = "{NUMBER: " + std::to_string(attr.value) + "}"; break;
			case LPAREN: s = "("; break;
			case RPAREN: s = ")"; break;
			case ADD:    s = " + "; break;
			case MNS:    s = " - "; break;
			case MUL:    s = " * "; break;
			case DIV:    s = " / "; break;
		}
		return s;
	}
};

struct ast_node {
	ast_node* left, 
	        * right;
	token data;
};

const char* parse_number(const char* p, std::vector<token>& tokens) {
	long long n = 0;
	while(*p >= '0' && *p <= '9') {
		n = n * 10 + (*p - '0');
		++p;
	}
	token t = {NUMBER};
	t.attr.value = n;
	tokens.push_back(t);
	return p;
}

void error_handler(const char* p) {
	std::cout << "meet an error: \'" << *p << '\'';
	std::exit(1);
} 

std::vector<token> lexing(const char* s) {
	std::vector<token> tokens{};
	while(true) {
		switch(*s) {
			case ' ':
			case '\n':
			case '\t':
			case '\v':
			case '\f':
			case '\r': ++s; break;
			case '0' ... '9': s = parse_number(s, tokens); break;
			case '(': tokens.push_back({LPAREN}); ++s; break;
			case ')': tokens.push_back({RPAREN}); ++s; break;
			case '+': tokens.push_back({ADD}); ++s; break;
			case '-': tokens.push_b\\\\\\\\\\ack({MNS}); ++s; break;
			case '*': tokens.push_back({MUL}); ++s; break;
			case '/': tokens.push_back({DIV}); ++s; break;
			case '\0': goto success;
			default: error_handler(s);
		}
	}
	success:
	return tokens;
}


ast_node* parsing(const std::vector<token>& tokens) {
	return nullptr;
}



int main(int argc, const char **argv) {
	std::cout << "start to lexing:\n";
	if(argc == 1) return 0;
	std::cout << argv[1] << '\n';
	std::vector<token> tokens = lexing(argv[1]);
	for(const auto& t: tokens) {
		std::cout << std::string(t);
	}
	return 0;
}