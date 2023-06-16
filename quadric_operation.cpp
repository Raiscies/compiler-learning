#include <vector>
#include <iostream>

enum vocabulary: int {

	//nonterminals
	E = 0, 
	Ep,        // E'
	T, 
	Tp,        // T'
	F,  

	//terminals
	NUMBER = 5,  // numbers 
	LPARAN,      // (
	RPARAN,      // )
	ADD,         // +
	MNS,         // -
	MUL,         // *
	DIV,         // /

	EPS,         // ε
	EOS          // $
	
};



struct token {
	vocabulary category; // should be terminal
	union {
		long long value;
		void* field;
	} attr;

	operator std::string() const{
		std::string s;
		switch(category) {
			// case NUMBER: s = "{NUMBER: " + std::to_string(attr.value) + "}"; break;
			case NUMBER: s = std::to_string(attr.value); break;
			case LPARAN: s = "("; break;
			case RPARAN: s = ")"; break;
			case ADD:    s = " + "; break;
			case MNS:    s = " - "; break;
			case MUL:    s = " * "; break;
			case DIV:    s = " / "; break;
			case EOS:    s = " $ "; break;
			default: break;
		}
		return s;
	}
};

struct ast_node {
	bool is_terminal = false;
	union {
		ast_node* field[3];
		token tok;
	} attr;

	ast_node(const token& tok) {
		is_terminal = true;
		attr.tok = tok;
	}
	ast_node() {
		is_terminal = false;
		for(auto*& p: attr.field) p = nullptr;
	}
	
	ast_node* make_child(unsigned int index) {
		if(is_terminal) {
			std::cout << "error: at ast_node::make_child(): try to make a child in a terminal ast node\n";
			std::exit(1);
		}
		if(index > 2) {
			std::cout << "error: at ast_node::make_child(): wrong index: " << index << "\n";
			std::exit(1);
		}
		if(attr.field[index] != nullptr) {
			std::cout << "error: at ast_node::make_child(): try to make a child in a exists field, index: " << index << "\n";
			std::exit(1);
		}
		attr.field[index] = new ast_node();
		//returns the child
		return attr.field[index];
	}

	ast_node* make_child(unsigned int index, const token& tok) {
		if(is_terminal) {
			std::cout << "error: at ast_node::make_child(uint, tok&): try to make a child in a terminal ast node\n";
			std::exit(1);
		}
		if(index > 2) {
			std::cout << "error: at ast_node::make_child(uint, tok&): wrong index: " << index << "\n";
			std::exit(1);
		}
		if(attr.field[index] != nullptr) {
			std::cout << "error: at ast_node::make_child(uint, tok&): try to make a child in a exists field, index: " << index << "\n";
			std::exit(1);
		}
		attr.field[index] = new ast_node(tok);
		//returns the child
		return attr.field[index];
	}

	operator std::string() {
		if(is_terminal) {
			return std::string(attr.tok);
		}else {
			std::string s = "{";
			for(auto*& n: attr.field) {
				if(n == nullptr) break;
				s += (std::string(*n) + " ");
			}
			return s + "}";
		}
	}
};



void parsing_error_handler(const char* emsg, auto pos);
void lexing_error_handler(const char* emsg, const char* p);
long long parse_E(ast_node*);
long long parse_T(ast_node*);
long long parse_F(ast_node*);
long long parse_Ep(long long val, ast_node*);
long long parse_Tp(long long val, ast_node*);



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
			case '(':  tokens.push_back({LPARAN}); ++s; break;
			case ')':  tokens.push_back({RPARAN}); ++s; break;
			case '+':  tokens.push_back({ADD}); ++s; break;
			case '-':  tokens.push_back({MNS}); ++s; break;
			case '*':  tokens.push_back({MUL}); ++s; break;
			case '/':  tokens.push_back({DIV}); ++s; break;
			case '\0': tokens.push_back({EOS}); goto success;
			default: lexing_error_handler("at lexing(): unexpected character", s);
		}
	}
	success:
	return tokens;
}

std::vector<token> tokens = lexing("89 - (43*43 -2 + 321) - 553 / 3 * 2");
auto pos = tokens.begin();
ast_node* root;

void lexing_error_handler(const char* emsg, const char* pos) {
	std::cout << "meet a error: " << emsg  << "," << (pos == nullptr ? '$' : *pos) << "\n";
	std::exit(1);
}

void parsing_error_handler(const char* emsg, auto pos) {
	std::cout << "meet a error: " << emsg  << "," << (pos == tokens.end() ? std::string("$") : std::string(*pos)) << "\n";
	std::exit(2);
}

long long parse_E(ast_node* n) {
	if(pos == tokens.end()) {
		parsing_error_handler("at parse_E(): no more tokens", pos);
		return -1; //never reach here
	}
	switch(pos->category) {
		// E -> T E'	
		case NUMBER:
		case LPARAN:
			// return parse_Ep(parse_T(n->attr.field[0] = new ast_node()), n->attr.field[1] = new ast_node());
			return parse_Ep(parse_T(n->make_child(0)), n->make_child(1));
		default:
			parsing_error_handler("at parse_E(): unexpected token", pos);
			return -1; //never reach here
	}
	
}

long long parse_T(ast_node* n) {
	if(pos == tokens.end()) {
		parsing_error_handler("at parse_T(): no more tokens", pos);
		return -1; //never reach here
	}
	long long val;
	switch(pos->category) {
		// T -> F T'
		case NUMBER:
		case LPARAN:
			// val = parse_F(n->attr.field[0] = new ast_node());
			val = parse_F(n->make_child(0));
			// std::cout << "{"<< val << " next: " << std::string(*pos) << "}";
			// return parse_Tp(val, n->attr.field[1] = new ast_node());
			return parse_Tp(val, n->make_child(1));
		default:
			parsing_error_handler("at parse_T(): unexpected token", pos);
			return -1; //never reach here
	}
}

long long parse_Ep(long long val, ast_node* n) {
	if(pos == tokens.end()) {
		parsing_error_handler("at parse_Ep(): no more tokens", pos);
		return -1; //never reach here
	}
	switch(pos->category) {
		case ADD:
			// E' -> + T E'
			// n->attr.field[0] = new ast_node(*pos);
			n->make_child(0, *pos);
			++pos;
			// return parse_Ep(val + parse_E(n->attr.field[1] = new ast_node()), n->attr.field[2] = new ast_node());
			return parse_Ep(val + parse_T(n->make_child(1)), n->make_child(2));
			
		case MNS:
			// E' -> - T E'
			// n->attr.field[0] = new ast_node(*pos);
			n->make_child(0, *pos);
			++pos;
			// return parse_Ep(val - parse_E(n->attr.field[1] = new ast_node()), n->attr.field[2] = new ast_node());
			return parse_Ep(val - parse_T(n->make_child(1)), n->make_child(2));
		case RPARAN:
			std::cout << "parse_Ep(): meet \'(\'\n";
		case EOS:
			// E' -> ε
			return val;
		default:
			parsing_error_handler("at parse_Ep(): unexpected token", pos);
			return -1;
	}
}

long long parse_Tp(long long val, ast_node* n) {
	
	
	if(pos == tokens.end()) {
		parsing_error_handler("at parse_Tp(): no more tokens", pos);
		return -1; //never reach here
	}
	switch(pos->category) {
		case MUL:
			// T' -> * F T'
			// n->attr.field[0] = new ast_node(*pos);
			n->make_child(0, *pos);
			++pos;
			// return parse_Tp(val * parse_F(n->attr.field[1] = new ast_node()), n->attr.field[2] = new ast_node());
			return parse_Tp(val * parse_F(n->make_child(1)), n->make_child(2));
		case DIV:
			// T' -> / F T'
			// n->attr.field[0] = new ast_node(*pos);
			n->make_child(0, *pos);
			++pos;
			// return parse_Tp(val / parse_F(n->attr.field[1] = new ast_node()), n->attr.field[2] = new ast_node());
			return parse_Tp(val / parse_F(n->make_child(1)), n->make_child(2));
		case RPARAN:
			std::cout << "parse_Tp(): meet \'(\'\n";
		case ADD:
		case MNS:
		case EOS:
			// T' -> ε
			return val;
		default:
			parsing_error_handler("at parse_Tp(): unexpected token", pos);
			return -1;
	}
}

long long parse_F(ast_node* n) {
	
	if(pos == tokens.end()) {
		parsing_error_handler("at parse_F(): no more tokens", pos);
		return -1; //never reach here
	}
	long long val;
	switch(pos->category) {
		case NUMBER:
			// F -> num
			// n->attr.tok = *pos;
			n->make_child(0, *pos);
			val = pos->attr.value;
			++pos;
			return val;
		case LPARAN:
			// F ->(E)
			// n->attr.field[0] = new ast_node(*pos);  
			n->make_child(0, *pos);
			++pos;
			// val = parse_E(n->attr.field[1] = new ast_node());
			val = parse_E(n->make_child(1));
			// n->attr.field[2] = new ast_node(*pos);
			n->make_child(2, *pos); 
			if(pos->category != RPARAN) {
				std::cout << "error at parse_F(): miss \')\', got \'" << pos->category << "\'\n";
				std::exit(1);
			}
			++pos; // eat ')'
			return val;
		default:
			parsing_error_handler("at parse_F(): unexpected token", pos);
			return -1; //never reach here
	
	}
}

long long parse() {
	return parse_E(root = new ast_node());
}


int main() {
	std::cout << "result:\n";
	std::cout << parse() << "\n";
	std::cout << "ast tree: \n" << std::string(*root) << "\n ended.";
}