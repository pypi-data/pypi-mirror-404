from typing import Self, final

from pydantic_core.core_schema import CoreSchema, str_schema, no_info_plain_validator_function, plain_serializer_function_ser_schema


__all__ = ['HitsoundStr']

@final
class HitsoundStr(str):
	def __new__(cls, obj: object="") -> Self:
		content = 'none' if obj is None else str(obj).replace('.', '_')
		return super().__new__(cls, content)

	def is_none(self) -> bool:
		return self == 'none'
	
	def unwrap(self) -> str | None:
		return None if self.is_none() else self.replace('_', '.')
	
	@final
	@classmethod
	def __get_pydantic_core_schema__(cls, source_type, handler) -> CoreSchema:

		def validate(value):
			if isinstance(value, cls):
				return value
			try:
				return cls(value)
			except TypeError as e:
				raise ValueError(e) from e

		return no_info_plain_validator_function(
			validate,
			serialization=plain_serializer_function_ser_schema(str, return_schema=str_schema())
		)
	
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({str(self)!r})'