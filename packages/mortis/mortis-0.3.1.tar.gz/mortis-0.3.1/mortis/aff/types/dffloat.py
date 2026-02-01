from __future__ import annotations

from math import isfinite
from re import fullmatch
from typing import Any, Self, final

from pydantic_core.core_schema import CoreSchema, float_schema, no_info_plain_validator_function, plain_serializer_function_ser_schema

from mortis.utils import classproperty



__all__ = ['dffloat', 'dffloat2', 'dffloat3']

class _dffloat_base(float):
	"""
	Inner type implementing `dffloat`.
	"""

	__pattern__ = r'^[+-]?(?:\d+\.\d*|\.\d+)$'
	__slots__ = ()

	@classproperty
	def precision(cls) -> int | None:
		raise NotImplementedError
	
	@final
	@classproperty
	def pattern(cls) -> str:
		return cls.__pattern__

	def __new__(cls, value: Any) -> Self:
		if isinstance(value, str):
			value = value.strip()
			if not fullmatch(cls.pattern, value):
				raise ValueError(f'Value {value!r} does not match with the required pattern {cls.pattern!r}')
		
		vf = float(value)
		if not isfinite(vf):
			raise ValueError(f'Value must be finite, got {vf}')
		
		if cls.precision is not None: # default behaviour: no rounding
			vf = round(vf, cls.precision)

		instance = super().__new__(cls, vf)
		return instance
		
	def __str__(self) -> str:
		vf = float(self)

		if self.precision is not None:
			value_str = f'{vf:.{self.precision}f}'
		else:
			value_str = str(vf)
		
		if '.' not in value_str:
			return value_str + '.0'
		
		return value_str
	
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({str(self)})'
	
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
			serialization=plain_serializer_function_ser_schema(
				lambda v: float(v),
				return_schema=float_schema()
			)
		)


__mortis_dffloats__: dict[int, type[_dffloat_base]] = {}
class dffloat(_dffloat_base):
	"""
	Subclass of `float` for ensuring format requirement of AFF file. 

		value_2 = dffloat(3.0)
		# Both declarations are equivalent to each other.

	This class behaves like normal `float` in most cases, but:
	- Arithmetics, etc. applied on instances, would returns a result in `float`, not `dffloat`.
	  - This is because `dffloat` failed to maintain (mathematical) closure from `float`.
	    - Or simpler, no way to ensure results of `dffloat` operations is still a valid `dffloat`.
	  - This always happens, **even both operands are `dffloat`.**:

		value_3 = value_1 + value_2

		print(type(value_3))
		>>> <class 'float'>
		print(value_3)
		>>> 6.0

	- This rejects nonfinite values e.g. `inf` and `nan`.:

		# dffloat('nan')
		# This would result in a ValueError

	- When parsing from a `str`, a `[+/-][aaa].[bbb]` format `str` is required, where
	  - `[...]` indicates that `...` is optional, and
	  - at least one of `[aaa]` and `[bbb]` should be provided.:

		print(dffloat('1.0'))
		>>> 1.0

		print(dffloat('+7.'))
		>>> 7.0

		print(dffloat('-.8'))
		>>> -0.8

		# dffloat('1')
		# ValueError, since '1' does not match the pattern. There is no decimal point in '1'.
	
	- You can limit the float precision (see below).

	These requirements sounds totally weird and counter-intuitive, but AFF file format **does need such behaviours**.
	
	Using `dffloat[x]` can create a **new type** which limits the maximum float precision to posint `x`.:

		value_5 = dffloat[3](1.0)

		print(value_5)
		>>> 1.000

		type(value_5)
		# dffloat[3]

	- Any of `dffloat[x]` is **not** a subclass of `dffloat`.:

		print(issubclass(dffloat[3], dffloat))
		>>> False

	- Using `dffloat` without specifying `[x]` is ok as well.
	  - In this case, there is no float precision limitations.:
	
		print(dffloat(1.24))
		>>> 1.24
		print(dffloat(1.24444))
		>>> 1.24444
	
	- Use `cls.precision` to check its float precision.:

		print(dffloat.precision)
		>>> None
		print(dffloat[3].precision)
		>>> 3

	"""
	@classproperty
	def precision(cls) -> int | None:
		return None

	def __class_getitem__(cls, prec: int) -> type[_dffloat_base]:
		"""
		Syntactic sugar for creating `dffloat[x]` classes with precision limitations.
		"""
		if not isinstance(prec, int):
			raise TypeError(f'Precision must be of type int, got value {prec!r} of type {type(prec)!r}')
		
		if prec <= 0:
			raise TypeError(f'Precision must be a positive int, got {prec}')
		
		if prec not in __mortis_dffloats__:
			class Subclass(_dffloat_base):
				@classproperty
				def precision(cls) -> int | None:
					return prec
				
			Subclass.__name__ = f'{dffloat.__name__}[{prec}]'
			Subclass.__qualname__ = f'{dffloat.__qualname__}[{prec}]'
			
			__mortis_dffloats__[prec] = Subclass
		
		return __mortis_dffloats__[prec]
	
dffloat2 = dffloat[2]
dffloat3 = dffloat[3]