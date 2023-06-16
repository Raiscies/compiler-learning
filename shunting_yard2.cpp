
#include <algorithm>
#include <iostream>
#include <cstdlib>
#include <utility>
#include <ranges>
#include <string>
#include <vector>

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

std::string eval_binop(operator_category oper, std::vector<token>& opnd_s) {
	if(opnd_s.size() < 2) return "too few operands"s; //error
	
	long long res = opnd_s.back().value; opnd_s.pop_back();

	switch(oper) {
		case ADD:
			res = opnd_s.back().value + res;
			break;
		case MNS:
			res = opnd_s.back().value - res;
			break;
		case MUL:
			res = opnd_s.back().value * res;
			break;
		case DIV:
			res = opnd_s.back().value / res;
			break;
		case MOD:
			res = opnd_s.back().value % res;
			break;
		default: return "unknown operator: "s + oper_table[oper];
	}
	opnd_s.pop_back();
	opnd_s.emplace_back(res);
	return "";
}

std::pair<long long, std::string> eval(const std::vector<token>& tokens) {
	if(tokens.empty()) return {0, "empty token sequence"};

	//                +  -  *  /  %
	int priority[] = {1, 1, 2, 2, 2};

	std::vector<token> out, opers;

	for(const auto& tok: tokens) {
		if(tok.oper == NOT_A_OPER) {
			//push_back number
			out.push_back(tok);
		}else if(opers.empty()) {
			//push_back if stack is empty
			opers.push_back(tok);
		}else if(tok.oper == LP) {
			// (
			opers.push_back(tok);
		}else if(tok.oper == RP) {
			// )
			while(!opers.empty() && opers.back().oper != LP) {
				out.push_back(opers.back());
				opers.pop_back();
			}
			if(!opers.empty()) opers.pop_back();
			else return {0, "missing left paren"};
		}else {
			//other ops
			if(priority[opers.back().oper] >= priority[tok.oper]) {
				//output operator at stack
				//reduce
				out.push_back(opers.back());
				opers.pop_back();
			}else {
				//shift in
				opers.push_back(tok);
			}
		}
	}

	// while(!out.empty()) {
	// 	std::cout << std::string(out.back()) << ", ";
	// 	out.pop_back();
	// }

	//evaluate RPE
	std::vector<token> evals;
	int top_opnd_count = 0;
	while(!out.empty()) {
		if(out.back().oper != NOT_A_OPER) {
			//is a operator
			evals.push_back(out.back());
		}else {
			if(top_opnd_count < 2) {
				evals.push_back(out.back());
				++top_opnd_count;
			}else {
				//top_opnd_count == 2
				long long res = 0;
				switch(evals[evals.size() - 3].oper) {
					case ADD:
						res = evals[evals.size() - 1].value + evals[evals.size() - 2].value;
						break;
					case MNS:
						res = evals[evals.size() - 1].value - evals[evals.size() - 2].value;
						break;
					case MUL:
						res = evals[evals.size() - 1].value * evals[evals.size() - 2].value;
						break;
					case DIV:
						res = evals[evals.size() - 1].value / evals[evals.size() - 2].value;
						break;
					case MOD:
						res = evals[evals.size() - 1].value % evals[evals.size() - 2].value;
						break;
					default:
						return {0, "bad operator at evaluating: "s + oper_table[evals[evals.size() - 3].oper]};
				}
				evals.pop_back();
				evals.pop_back();
				evals.pop_back();
				evals.emplace_back(res);
				top_opnd_count = 1;
			}
		}
		out.pop_back();
	}

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