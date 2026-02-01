from __future__ import annotations

from enum import StrEnum
from re import compile as compile_regex
from typing import Any


__all__ = [
	'TokenType', 'Token', 'Tokens',
	'ARG_TOKEN_TYPES', 'COMMAND_TOKEN_TYPES', 'TOKEN_TYPES_PATTERNS',
	'tokenize'
]

class TokenType(StrEnum):
	# Grammatical symbols
	LeftParenthesis = r'\('
	RightParenthesis = r'\)'
	LeftBracket = r'\['
	RightBracket = r'\]'
	LeftBrace = r'\{'
	RightBrace = r'\}'
	Comma = r','
	Colon = r':'
	Semicolon = r';'

	# Keywords
	Arctap = r'arctap'
	Arc = r'arc'
	At = r'at'
	Camera = r'camera'
	Hold = r'hold'
	SceneControl = r'scenecontrol'
	TimingGroup = r'timinggroup'
	Timing = r'timing'

	# Types
	Float = r'[+-]?(\d+\.\d*|\.\d+)'
	Integer = r'[+-]?[0-9]+'
	Identifier = r'[a-zA-Z_][a-zA-Z0-9_]*'

	# Special
	PartSeparator = r'-'
	Whitespace = r'\s+'

ARG_TOKEN_TYPES = (TokenType.Integer, TokenType.Float, TokenType.Identifier)
COMMAND_TOKEN_TYPES = (
	TokenType.Arc,
	TokenType.Camera,
	TokenType.Hold,
	TokenType.SceneControl,
	TokenType.Timing,
)

TOKEN_TYPES_PATTERNS = [
	(token_type, compile_regex(regex)) 
	for token_type, regex
	in TokenType.__members__.items()
]

class Token:
	def __init__(self, type_: TokenType, value: Any | None = None) -> None:
		self.type_ = type_
		self.value = value
	
	def __repr__(self) -> str:
		value_str = '' if self.value is None else f', {self.value!r}'
		return f'Token({self.type_.name}{value_str})'
	
	def __eq__(self, other) -> bool:
		return type(other) is type(self) and self.type_ == other.type_ and self.value == other.value

Tokens = tuple[Token, ...]

def tokenize(line: str) -> tuple[Token, ...]:
	if not isinstance(line, str):
		raise ValueError(f'Value must be of type str, got value {line!r} of type {type(line)!r}')
	tokens = []
	pos = 0
	line_len = len(line)

	
	while pos < line_len:
		matched = None
		token_type = None
		
		for name, pattern in TOKEN_TYPES_PATTERNS:
			matched = pattern.match(line, pos)
			if matched:
				token_type = TokenType[name]
				break
		else:
			raise ValueError(f"Failed to tokenize at position {pos} (at char {line[pos]!r}): {line!r}")
		
		matched_text = matched.group(0)
		
		if token_type == TokenType.Whitespace:
			pos = matched.end()
			continue
		
		value = None
		if token_type == TokenType.Float:
			value = float(matched_text)

		elif token_type == TokenType.Integer:
			value = int(matched_text)
		
		elif token_type == TokenType.Identifier:
			value = str(matched_text)
		
		else:
			value = matched_text
		
		tokens.append(Token(token_type, value))
		pos = matched.end()
	
	return tuple(tokens)