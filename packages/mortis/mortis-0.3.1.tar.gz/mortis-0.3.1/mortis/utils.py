from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, Literal, Self, TypeVar, final

from pydantic import ConfigDict


__all__ = ['classproperty', 'get_default_model_cfg', 'UnreachableBranch', 'Predicate']

MT = TypeVar('MT', bound=Any)
RT = TypeVar('RT')
class classproperty(Generic[MT, RT]):
	"""
	Class property attribute. 
	"""

	def __init__(self, fget: Callable[[type[MT]], RT], /) -> None:
		self.fget = classmethod(fget)

	def __get__(self, instance: MT | None, objtype: type[MT], /) -> RT:
		return self.fget.__get__(instance, objtype)()


def get_default_model_cfg(
	extra: Literal['allow', 'ignore', 'forbid'] = 'forbid',
	ignored_types: Any = None
) -> ConfigDict:
	
	if ignored_types is None:
		ignored_types = ()

	return ConfigDict(
		extra=extra,
		validate_assignment=True,
		validate_default=True,
		ignored_types=ignored_types + (classproperty, ),
		allow_inf_nan=False,
	)


@final
class UnreachableBranch(Exception):
	__instance__ = None
	
	def __new__(cls) -> Self:
		if cls.__instance__ is None:
			cls.__instance__ = super().__new__(cls)
		return cls.__instance__
	
	def __init__(self) -> None:
		pass

	def __str__(self) -> str:
		return 'Current code branch is expected to be unreachable'
	
	def __repr__(self) -> str:
		return '<UnreachableBranch>'
UnreachableBranch() # create singleton

type Predicate = Callable[[Any], bool]