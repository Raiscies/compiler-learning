#include <algorithm>
#include <iostream>
#include <cstdlib>
#include <utility>
#include <ranges>
#include <string>
#include <vector>
#include <stack>
/*
	supports integer number
	operator: +, -, *, /, %, (, )
*/
using namespace std::literals;

enum operator_category {
	ADD = 0, MNS, MUL, DIV, MOD, LP, RP, 
	NOT_A_OPER = -1,
	UNKNOWN = -2
};

static constexpr char oper_table[] = {
	'+', '-', '*', '/', '%', '(', ')'
};

struct token {
	long long value = 0;
	operator_category oper;

	token(long long value_) noexcept: value{value_}, oper{NOT_A_OPER} {}
	token(operator_category oper_) noexcept: oper{oper} {}
	token(char c) noexcept{
		switch(c) {
			case '+': oper = ADD; break;
			case '-': oper = MNS; break;
			case '*': oper = MUL; break;
			case '/': oper = DIV; break;
			case '%': oper = MOD; break;
			case '(': oper = LP;  break;
			case ')': oper = RP;  break;
			default:  oper = UNKNOWN;
		}
	}

	explicit operator std::string() noexcept{
		if(oper == UNKNOWN)         return {'?'};
		else if(oper == NOT_A_OPER) return std::to_string(value);
		else                        return {oper_table[oper]};
	}
};

std::pair<std::vector<token>, const char*> lex(const char* s) {
	if(!s) return {{}, s};
	auto res = std::pair<std::vector<token>, const char*>{{}, s};
	const char* pos = s;
	while(*pos != '\0') {
		switch(*pos) {
			case '\x9' ... '\xd': [[fallthrough]]; // '\t' '\n' '\v' '\f' '\r' 
			case ' ': 
				//spaces
				++pos; //skip white spaces
				break;
			case '0' ... '9':
				//number
				res.first.emplace_back(std::strtoll(pos, const_cast<char**>(&pos), 0));
				break;
			case '+':[[fallthrough]];
			case '-':[[fallthrough]];
			case '*':[[fallthrough]];
			case '/':[[fallthrough]];
			case '%':[[fallthrough]];
			case '(':[[fallthrough]];
			case ')':
				res.first.emplace_back(*pos);
				++pos;
				break;
			default:
				res.second = pos;
				return res;
		}
	}
	res.second = pos;
	return res;
}

std::string eval_binop(operator_category oper, std::stack<token>& opnd_s) {
	if(opnd_s.size() < 2) return "too few operands"s; //error
	
	long long res = opnd_s.top().value; opnd_s.pop();

	switch(oper) {
		case ADD:
			res = opnd_s.top().value + res;
			break;
		case MNS:
			res = opnd_s.top().value - res;
			break;
		case MUL:
			res = opnd_s.top().value * res;
			break;
		case DIV:
			res = opnd_s.top().value / res;
			break;
		case MOD:
			res = opnd_s.top().value % res;
			break;
		default: return "unknown operator: "s + oper_table[oper];
	}
	opnd_s.pop();
	opnd_s.emplace(res);
	return "";
}

std::pair<long long, std::string> eval(const std::vector<token>& tokens) {
	enum action_flag{ R = 1, S = 2, X = 3 };
	static constexpr action_flag action_table[7][7] = {
		// R means reduce
		// S means shift-in
		// X means meaningless or error
		// action_table[pos][stack.top]
		// stack   +  -  *  /  %  (  )   
		/*pos*/
		/* + */    S, S, R, R, R, S, X,   
		/* - */    S, S, R, R, R, S, X,
		/* * */    S, S, R, R, R, S, X,
		/* / */    S, S, R, R, R, S, X,
		/* % */    S, S, R, R, R, S, X,
		/* ( */    S, S, S, S, S, S, X,
		/* ) */    R, R, R, R, R, R, X
	};


	std::stack<token> oper_s, opnd_s;
	for(const auto& tok: tokens) {
		if(tok.oper == NOT_A_OPER) {
			opnd_s.push(tok);
			continue;
		}
		if(tok.oper == UNKNOWN) {
			// error at evaluating
			return {0, "unknown operator"s};
		}
		if(oper_s.empty()) {
			oper_s.push(tok);
			continue;
		}

		//main logics
		if(action_table[tok.oper][oper_s.top().oper] == S) {
			//shift-in
			oper_s.push(tok);
		}else {
			//reduce
			if(tok.oper == RP) {
				// )
				if(oper_s.empty()) return {0, "missing left paren"s}; // error: missing left paren
				if(oper_s.top().oper == LP) {
					if(opnd_s.empty()) return {0, "empty paren pair"s}; // error: ( empty )
					oper_s.pop();
					continue;
				}
				auto res = eval_binop(oper_s.top().oper, opnd_s);
				if(!res.empty()) return {0, res}; //error: too few operands
				oper_s.pop(); //pop binop
				oper_s.pop(); //pop (
			}else {
				// + - * / %
				auto res = eval_binop(oper_s.top().oper, opnd_s);
				if(!res.empty()) return {0, res};
				oper_s.pop();
				oper_s.push(tok);
			}
		}
	}
	if(!oper_s.empty()) {
		auto res = eval_binop(oper_s.top().oper, opnd_s);
		if(!res.empty()) return {0, res};
	}
	auto res = opnd_s.top(); opnd_s.pop();
	return {res.value, {}};
}



int main(int argc, char const *argv[]) {
	using std::cout;
	using std::endl;
	using namespace std::ranges;
	auto tokens = lex("(1 + 3 / 98)").first;
	for_each(tokens, [](auto i){cout << std::string(i) << " ";});
	cout << '\n';
	auto res = eval(tokens);
	if(!res.second.empty()) {
		cout << "error: wrong expression:" << res.second;
	}else cout << "result: " << res.first;

	return 0;
}