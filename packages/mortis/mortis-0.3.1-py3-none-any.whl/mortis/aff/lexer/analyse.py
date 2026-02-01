from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

from mortis.aff.lexer.token import ARG_TOKEN_TYPES, COMMAND_TOKEN_TYPES, Token, Tokens, TokenType


__all__ = [
	'analyse_annotation',
	'analyse_part_separation',
	'analyse_timinggroup_header',
	'analyse_timinggroup_footer',
	'analyse_command'
]

def analyse_annotation(tokens: Tokens) -> tuple[str, Any]:
	if any([
		len(tokens) != 3,
		tokens[0].type_ != TokenType.Identifier,
		tokens[1].type_ != TokenType.Colon,
		tokens[2].type_ not in ARG_TOKEN_TYPES
	]):
		raise ValueError('Invalid annotation format')
	return tokens[0].value, tokens[2].value # type: ignore


def analyse_part_separation(tokens: Tokens) -> None:
	if len(tokens) != 1 or tokens[0].type_ != TokenType.PartSeparator:
		raise ValueError('Invalid part separation format')


def analyse_timinggroup_header(tokens: Tokens) -> str | None:
	exc = ValueError('Invalid timing group header format')
	tokenc = len(tokens)

	if tokenc == 4:
		tg, lparen, rparen, lbrace = tokens
	elif tokenc == 5:
		tg, lparen, params, rparen, lbrace = tokens
	else:
		raise exc
	
	if any([
		tg.type_ != TokenType.TimingGroup,
		lparen.type_ != TokenType.LeftParenthesis,
		(tokenc == 5 and params.type_ != TokenType.Identifier), # type: ignore
		rparen.type_ != TokenType.RightParenthesis,
		lbrace.type_ != TokenType.LeftBrace,
	]):
		raise exc
	
	return params.value if tokenc == 5 else None # type: ignore


def analyse_timinggroup_footer(tokens: Tokens) -> None:
	if any([
		len(tokens) != 2,
		tokens[0].type_ != TokenType.RightBrace,
		tokens[1].type_ != TokenType.Semicolon,
	]):
		raise ValueError('Invalid timing group footer format')


def find_token_of_type(
	tokens: Iterable[Token],
	type_: TokenType,
	start: int = 0
) -> int | None:
	
	tokens = list(tokens)
	for i in range(start, len(tokens)):
		if tokens[i].type_ == type_:
			return i
	return None


def analyse_command(tokens: Tokens) -> tuple[str, tuple, tuple | None]:
	exc = ValueError('Invalid command format')
	if not tokens:
		raise exc
	
	lpidx = find_token_of_type(tokens, TokenType.LeftParenthesis)
	if lpidx is None:
		raise exc
	
	if lpidx == 0:
		command_name = ''
		_, *rest = tokens
	else:
		command, _, *rest = tokens
		if command.type_ not in COMMAND_TOKEN_TYPES:
			raise exc
		command_name = command.value
	
	rpidx = find_token_of_type(rest, TokenType.RightParenthesis)
	if rpidx is None:
		raise exc
	
	argtoks = rest[:rpidx]
	after_rparen_tokens = rest[rpidx + 1:] # type: ignore
	
	if not argtoks:
		raise exc
	
	args = []
	arg_status: Literal['arg', 'comma']	= 'arg'
	while argtoks:
		tok = argtoks.pop(0)
		if arg_status == 'arg' and tok.type_ in ARG_TOKEN_TYPES:
			args.append(tok.value)
			arg_status = 'comma'
		elif arg_status == 'comma' and tok.type_ == TokenType.Comma:
			arg_status = 'arg'
		else:
			raise exc
	
	*rest, trailing = after_rparen_tokens
	if trailing.type_ != TokenType.Semicolon:
		raise exc
	
	if not rest:
		return command_name, tuple(args), None # type: ignore

	restc = len(rest)
	if restc < 3:
		raise exc
	
	lbracket, *extoks, rbracket = rest
	if any([
		lbracket.type_ != TokenType.LeftBracket,
		rbracket.type_ != TokenType.RightBracket,
		len(extoks) % 5 != 4,
	]):
		raise exc
	
	extra_args: list = []
	ex_status = 0
	ex_status_types = {
		0: {TokenType.At, TokenType.Arctap},
		1: {TokenType.LeftParenthesis},
		2: {TokenType.Integer},
		3: {TokenType.RightParenthesis},
		4: {TokenType.Comma},
	}
	while extoks:
		tok = extoks.pop(0)
		if tok.type_ not in ex_status_types[ex_status]:
			raise exc
		
		if ex_status == 2:
			extra_args.append(tok.value)
		
		ex_status = (ex_status + 1) % 5
	
	return command.value, tuple(args), tuple(extra_args) # type: ignore
		