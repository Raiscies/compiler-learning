#include <type_traits>
#include <cstdlib>
#include <cstdint>
#include <cctype>
#include <utility>
#include <vector>
#include <string>
#include <iostream>


namespace rais {

using std::size_t;
using std::uint8_t;

namespace lisp_interpreter_detail {

/*
	lisp BNFs:
	E      -> (Name EList)
	        | number
	        | string
	        | identifier
	        | keyword
	EList  -> E EList
	        | ε
	Name   -> identifier 
	        | keyword
	
	FIRST(E)      = {(, number, string, identifier}
	FIRST(EList)  = {(, number, string, identifier, ε}
	FIRST(Name)   = {identifier, keyword}
	FOLLOW(E)     = {$, ), (, number, string, identifier}
	FOLLOW(EList) = {)}
	FOLLOW(Name)  = {(, ), number, string, identifier}

	it's a LL(1) Grammer.
	
	lexical details:
	number     := [[0x[0-9a-fA-F]+] [0-9]* [1-9][0-9]+ ]                         (does not support float point numbers yet)
	string     := "[ascii-codes ∪ [\[' " ? \ a b f n r t v [0-9]³ x[0-9]² ]]]*"
	identifier := [a-zA-Z_][a-zA-Z0-9_-]*
	keyword    := {
		+, -, *, /, 
		=, != <, >, >=, <=,
		t, nil,
		if, loop, for, print,
		(to be enrich...)
	}
	
*/

class lisp_interpreter {

enum vocabulary {
	// terminals
	LPAREN,     // (
	RPAREN,     // )
	NUMBER,     // number
	STRING,     // string
	IDENTIFIER, // identifier
	KEYWORD,    // keyword
	ENDING,     // ending token

	// non-terminals
	E, EList, Name
};

static std::string vocabulary_string(vocabulary v) noexcept{
	switch(v) {
		case LPAREN:     return {'('};
		case RPAREN:     return {')'};
		case NUMBER:     return {" number "};
		case STRING:     return {" string "};
		case IDENTIFIER: return {" id "};
		case KEYWORD:    return {" keyword "};
		case ENDING:     return {'$'};
		default:         return {"{unknown token}"};
	}
}

enum keyword_category {
	KW_PLUS = 0, // +
	KW_MINUS,    // -
	KW_MUL,      // *
	KW_DIV,      // /
	KW_EQUAL,    // =
	KW_NEQUAL,   // !=
	KW_LESSEQ,   // <=
	KW_LARGEREQ, // >=
	KW_LESS,     // <
	KW_LARGER,   // >
	KW_T,        // t
	KW_NIL,      // nil
	KW_IF,       // if
	KW_LOOP,     // loop
	KW_FOR,      // for
	KW_PRINT,    // print
	// ...

	KW_NOT_A_KEYWORD = -1
};

static constexpr const char* keywords[] = {
	"+", "-", "*", "/", 
	"=", "!=", "<=", ">=", "<", ">", 
	"t", "nil",
	"if", 
	"loop", 
	"for", 
	"print"	
};


struct token {
	vocabulary v;
	union {
		long long number; 
		keyword_category keyword;
		size_t string_index;     // saves strings' index in strings
		size_t identifier_index; // saves identifiers' index in identifiers
		void* reserved_field;
	} attr;

	token(vocabulary v_) noexcept: v(v_) {attr.reserved_field = nullptr; }
	template <typename T>
	token(vocabulary v_, T attr_val): v(v_) {
		switch(v) {
			case KEYWORD:
				if constexpr(std::is_convertible_v<T, keyword_category>) {attr.keyword = attr_val; }
				else error_handler("constructor: attr_val is not a keyword category");
				break;
			case NUMBER: 
				if constexpr(std::is_convertible_v<T, long long>) {attr.number = attr_val; }
				else error_handler("constructor: attr_val is not a number");
				break;
			case STRING: 
				if constexpr(std::is_convertible_v<T, size_t>) {attr.string_index = attr_val; }
				else error_handler("constructor: attr_val is not a string");		
				break;
			case IDENTIFIER: 
				if constexpr(std::is_convertible_v<T, size_t>) {attr.identifier_index = attr_val; }
				else error_handler("constructor: attr_val is not a identifier index");
				break;
			case E:
			case EList:
			case Name:
				error_handler("constructor: a non-terminal token should'n take a attribute value");
				break;
			default: 
				if constexpr(std::is_convertible_v<T, void*>) {attr.reserved_field = attr_val; }
				else error_handler("constructor: attr_val is not a reserved field pointer");
				break;
		}
	}

	error_handler(const char* emsg) const{
		std::cerr << "error at struct token: {v = " << v << "} " << emsg << "\n";
		std::exit(-1);
	}
}; // struct token

class lexer;

struct ast_node {
	using child_list_t = std::vector<ast_node>;
	bool is_terminal;
	
	union attr_field {
		const token* tok;
		child_list_t* childs;

		attr_field(const token& tok_): tok(&tok_) {}
		attr_field(child_list_t* childs_): childs(childs_) {} 

	} attr;


	ast_node(const token& tok_) noexcept: is_terminal(true), attr(tok_) {}
	ast_node(): is_terminal(false), attr(new child_list_t{}) {}
	~ast_node() {
		if(!is_terminal) {
			delete attr.childs;
		}
	}

	ast_node& add_child() {
		if(is_terminal) error_handler("cannot add a child to a terminal");
		attr.childs->push_back({});
		return attr.childs->back(); //create a non-terminal node
	}
	ast_node& add_child(const token& tok_) {
		if(is_terminal) error_handler("cannot add a child to a terminal");
		attr.childs->emplace_back(tok_); //create a terminal node
		return *this; //return itself
	}

	std::string to_string(const lexer& lex, size_t align_len = 0) const{
		if(is_terminal) {
			return std::string(align_len, '\t') + lex.token_to_string(*attr.tok);
		}else {
			std::string result;
			for(const ast_node& child: *attr.childs) {
				result += (child.to_string(lex, align_len + 1) + '\n');

			}
			return result;
		}
	}

	error_handler(const char* emsg) {
		std::cerr << "error at ast_node: " << emsg << "\n";
		std::exit(-1);
	}
};

public:

using token_list_t      = std::vector<token>;
using identifier_list_t = std::vector<std::string>;
using string_list_t     = std::vector<std::string>;

class lexer {

public:


	token_list_t      tokens;
	identifier_list_t identifiers;
	string_list_t     strings;

	lexer() {}

	//main function
	//simply returns tokens&
	token_list_t& lexing(const char* target) {
		tokens.clear();
		identifiers.clear();
		strings.clear();

		const char* p = target;
		/*
			number     := [[0x[0-9a-fA-F]+] [0-9]* [1-9][0-9]+ ] 
			string     := "[ascii-codes ∪ [\[' " ? \ a b f n r t v [0-9]³ x[0-9]² ]]]*"
			identifier := [a-zA-Z_][a-zA-Z0-9_-]*
			keyword    := {
				+, -, *, /, 
				=, != <, >, >=, <=,
				t, nil,
				if, loop, for, print,
				(to be enrich...)
			}
		*/
		while(*p != '\0') {
			switch(*p) {
				case '\x9' ... '\xd': // '\t' '\n' '\v' '\f' '\r'
				case ' ': {
					//is spaces
					++p; //skip white spaces
					break;
				}
				case ';': {
					//is a line of comment
					skip_comment(p); 
					//now p was shifted to the next line
					break;
				}
				case '(': {
					//is LPAREN
					tokens.push_back({LPAREN});
					++p;
					break;
				}
				case ')': {
					//is RPAREN
					tokens.push_back({RPAREN});
					++p;
					break;
				}
				case '\"': {
					//is STRING
					strings.push_back(parse_string(p));
					tokens.push_back({STRING, strings.size() - 1});
					//now p was shifted, so we dont need p += len(str) something
					break;
				}
				case '0' ... '9': {
					//is NUMBER
					tokens.push_back({NUMBER, parse_number(p)});
					//now p was shifted, so we dont need p += len(str) something
					break;
				} 
				default: {
					//is Name (KEYWORD or IDENTIFIER)
					//try to match keyword
					keyword_category category = match_keyword(p);
					if(category == KW_NOT_A_KEYWORD) {
					// is IDENTIFIER
						identifiers.push_back(parse_identifier(p));
						tokens.push_back({IDENTIFIER, identifiers.size() - 1});
					}else {
					// is KEYWORD
						tokens.push_back({KEYWORD, category});
					}
					break;
				}
			}
		}
		tokens.emplace_back(ENDING);
		return tokens;
	}

private:

	void skip_comment(const char*& p) const{
		do {
			++p;
		}while(*p != '\0' && *p != '\n');
		if(*p == '\n') ++p;
	}

	long long parse_number(const char*& p) const{
		//the std::strtoll(const char*, char**, int) parameter list is confused, why are the second param is non-const?
		return std::strtoll(p, const_cast<char**>(&p), 0);
	}

	std::string parse_string(const char*& p) const{

		std::string result;
		++p; //eat the leading "
		while(true) {
			switch(*p) {
				case '\\': {
					//is escape character
					++p; //eat the leading backslash  
					switch(*p) {
						case '\'': result.push_back('\''); ++p; break; // "\\\'"
						case '\"': result.push_back('\"'); ++p; break; // "\\\""
						case '\\': result.push_back('\\'); ++p; break; // "\\\\" 
						case 'a':  result.push_back('\a'); ++p; break; // "\\a"
						case 'b':  result.push_back('\b'); ++p; break; // "\\b"
						case 'f':  result.push_back('\f'); ++p; break; // "\\f"
						case 'n':  result.push_back('\n'); ++p; break; // "\\n"
						case 'r':  result.push_back('\r'); ++p; break; // "\\r"
						case 't':  result.push_back('\t'); ++p; break; // "\\t"
						case 'v':  result.push_back('\v'); ++p; break; // "\\v"
						case 'x': {
							// a hex character value
							unsigned long long val = std::strtoull(p, const_cast<char**>(&p), 16);
							result.push_back(static_cast<char>(val));
							break;
						}
						case '0' ... '7': {
							// an octal number value
							// \nnn only (3 times n)
							uint16_t val = *p - '0';
							++p;
							for(int i = 0;i < 2; ++i) {
								if(*p >= '0' && *p <= '7') {
									val = val * 8 + (*p - '0');
								}else break;
								++p;
							}
							result.push_back(static_cast<char>(val));
							break;
						}
						default: {
							error_handler("bad escape character");
							break;
						}
					}	
					break;
				}
				case '\0':
					//error
					error_handler("bad string");
				case '\"':
					//success
					++p;
					return result;
				default: 
					result.push_back(*p);
					++p;
					break;
			}
		}
		return result;
	} 
	std::string parse_identifier(const char*& s) const{
		//identifier := [a-zA-Z_][a-zA-Z0-9_-]*
		std::string id;
		if(std::isalpha(*s) || (*s == '_')) {
			id.push_back(*s);
			++s;
		}else {
			error_handler("bad identifier");
		}
		while(*s != '\0' && (std::isalnum(*s) || (*s == '_'))) {
			id.push_back(*s);
			++s;
		}
		return id;
	}

	keyword_category match_keyword(const char*& s) const{
		//returns KW_NOT_A_KEYWORD if not a keyword
		//using the trivial algorithm
		for(size_t i = 0; i < (sizeof(keywords) / sizeof(const char*)); ++i) {
			const char* p = s;
			for(const char* c = keywords[i]; *c != '\0'; ++c) {
				if(*p != *c) goto next_kw; // continue the outer for loop 
				++p;
			}
			//success to match a keyword
			s = p; //shift to the next token
			return static_cast<keyword_category>(i);

			next_kw:
			; //fail to match a keyword
		}

		//fail to match any keyword
		//does not shift the s pointer
		return KW_NOT_A_KEYWORD;
	}
	void error_handler(const char* emsg) const{
		std::cerr << "error at lexer: " << emsg << "\n";
		exit(-1);
	}

public:

	std::string token_to_string(const token& tok) const{
		switch(tok.v) {
			case LPAREN:     return {'('};
			case RPAREN:     return {')'};
			case NUMBER:     return std::string("{number:") + std::to_string(tok.attr.number) + "}";
			case STRING:     return std::string("{string:") + strings.at(tok.attr.string_index) + "}";
			case IDENTIFIER: return std::string("{id:") + identifiers.at(tok.attr.identifier_index) + "}";
			case KEYWORD:    return std::string("{keyword:") + keywords[tok.attr.keyword] + "}";
			case ENDING:     return {'$'};
			default:         return {"{unknown token}"};
		}
	}

	std::string token_list_to_string() const{
		std::string result = "{";
		for(const auto& tok: tokens) {
			result += (token_to_string(tok) + " ");
		}
		return result + "}";
	}

} lex; //class lexer

class parser {

public:
	using token_iterator_t = token_list_t::const_iterator;

	ast_node root;

private:

	token_iterator_t it;
	const lexer* lex;

	/*
		lisp BNFs:
		E      -> (Name EList)
		        | number
		        | string
		        | identifier
		        | keyword
		EList  -> E EList
		        | ε
		Name   -> identifier 
		        | keyword
		
		FIRST(E)      = {(, number, string, identifier}
		FIRST(EList)  = {(, number, string, identifier, ε}
		FIRST(Name)   = {identifier, keyword}
		FOLLOW(E)     = {$, ), (, number, string, identifier}
		FOLLOW(EList) = {)}
		FOLLOW(Name)  = {(, ), number, string, identifier}

		it's a LL(1) Grammer.
	*/

public:

	parser() {}
	~parser() {

	}

	ast_node& parsing(const lexer& lex_) {
		lex = &lex_;
		it = lex->tokens.cbegin();
		parse_E(root);

		return root; 
	}

private:

	void parse_E(ast_node& node) {
		switch(it->v) {
			case LPAREN: {
				// E -> (Name EList)
				++it; // eat the left parenthese
				parse_Name(node);
				parse_EList(node);
				if(it->v != RPAREN) {
					error_handler("at parse_E(): missing the right parenthese \')\'", node);
				}
				++it; // eat the right parenthese

				break;
			}
			case NUMBER:
			case STRING: 
			case IDENTIFIER: 
			case KEYWORD: {
				// E -> number | string | keyword
				node.add_child({*it});
				++it;
				break;
			}
			case ENDING: {
				//finished parsing the token list 
				++it;
				break;
			}
			default: {
				error_handler("at parse_E(): unexpected token: ", node);
				break;
			}

		}
	}

	void parse_EList(ast_node& node) {
		switch(it->v) {
			case RPAREN: {
				// EList -> ε
				break;
			}
			case LPAREN:
			case NUMBER:
			case STRING:
			case IDENTIFIER: 
			case KEYWORD: {
				// EList -> E EList
				parse_E(node.add_child());
				parse_EList(node);				
				break;
			}
			default:
				error_handler("at parse_EList: unexpected token: ", node);
				break;
		}
	}

	void parse_Name(ast_node& node) {
		switch(it->v) {
			case IDENTIFIER:
			case KEYWORD:
				node.add_child(*it);
				++it;
				break;
			default:
				error_handler("at parse_Name: unexpected token: ", node);
				break;
		}
	}

	void error_handler(const char* emsg, const ast_node& err_node) {
		std::cerr << "error at parser: " << emsg << "iterator at: \'" << lex->token_to_string(*it) << "\', "
			<< (err_node.is_terminal ? lex->token_to_string(*err_node.attr.tok) : std::string("non-terminal node")) 
			<< "\n";
		std::exit(-1);
	}

public:

	std::string tree_to_string() const{
		return root.to_string(*lex, 0);
	}


} pas; //class parser

	lisp_interpreter() {

	}

	void evaluate(const char* target) {
		lex.lexing(target);
		std::cout << lex.token_list_to_string() << "\n";
		pas.parsing(lex);
		std::cout << pas.tree_to_string();

	}

}; // class lisp_interpreter

} // namespace rais	
} // namespace list_interpreter_detail


int main(int argc, const char* argv[]) {
	rais::lisp_interpreter_detail::lisp_interpreter li;
	std::cout << "interpreting...\n";
	li.evaluate(
		R"lisp(
		
		; a comment
		(abc 123 "heeloo" (if (= 1 2) t (>= 4 nil)) (foo "hello world\\\\")) ; this is another comment!


		)lisp"
	);
	std::cout << "finished evaluating\n";
	return 0;
}