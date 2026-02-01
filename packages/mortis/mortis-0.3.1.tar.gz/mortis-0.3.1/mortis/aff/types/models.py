from __future__ import annotations

from typing import Any, ClassVar, Self, final

from pydantic import BaseModel, ValidationError, model_validator
from pydantic.fields import FieldInfo
# from pydantic_core.core_schema import CoreSchema, union_schema, no_info_plain_validator_function

from mortis.aff.lexer.analyse import analyse_command
from mortis.aff.lexer.token import tokenize
from mortis.utils import get_default_model_cfg, classproperty, UnreachableBranch


__all__ = [
	'AFFEventConfig',
	'AFFEvent',
	'GameObjectEvent', 'TechnicalEvent',
	'FloorEvent', 'SkyEvent', 'LongNoteEvent', 'TapLikeEvent'
]

class AFFEventConfig:
	def __init__(
		self,
		*,
		is_event: bool = False,
		commands: tuple[str, ...] | None = None,
		trailing: str = ';',
		uses_extra_args: bool = False,
		argument_order: tuple[str, ...] | None = None
	) -> None:
		
		self.is_event = is_event
		self.commands = commands if commands is not None else ()
		self.trailing = trailing
		self.uses_extra = uses_extra_args
		self.fields_order = argument_order if argument_order is not None else ()

class AFFEvent(BaseModel):

	model_config = get_default_model_cfg(ignored_types=(AFFEventConfig, ))

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig()
	__converters__: ClassVar[tuple[str, ...]] = 'from_str',
	
	########################################################################################

	@classmethod
	def is_event_class(cls) -> bool:
		return cls.__aff_config__.is_event
	
	@classproperty
	def commands(cls) -> tuple[str, ...]:
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not an event class')
		
		return cls.__aff_config__.commands
	
	@classproperty
	def main_command(cls) -> str:
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not an event class')
		
		assert cls.__aff_config__.commands, f'{cls.__name__} should have at least one command name'
		return cls.__aff_config__.commands[0]
	
	@classproperty
	def command_trailing(cls) -> str:
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not an event class')
		
		return cls.__aff_config__.trailing
	
	@classmethod
	def allows_extra(cls) -> bool:
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not an event class')
		
		return cls.__aff_config__.uses_extra
	
	@classproperty
	def fields_order(cls) -> tuple[str, ...]:
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not an event class')
		
		return cls.__aff_config__.fields_order
	
	########################################################################################

	@classproperty
	def model_ordered_fields(cls) -> dict[str, FieldInfo]:
		return {
			name: cls.model_fields[name]
			for name in cls.fields_order
		}

	@classproperty
	def model_required_fields(cls) -> dict[str, FieldInfo]:
		return {
			name: info
			for name, info in cls.model_ordered_fields.items()
			if info.is_required()
		}

	@classproperty
	def model_optional_fields(cls) -> dict[str, FieldInfo]:
		return {
			name: info
			for name, info in cls.model_ordered_fields.items()
			if not info.is_required()
		}
	
	@property
	def ordered_fields(self) -> dict[str, Any]:
		return {
			name: getattr(self, name)
			for name in self.__class__.model_ordered_fields
		}
	
	@property
	def required_fields(self) -> dict[str, Any]:
		return {
			name: getattr(self, name)
			for name in self.__class__.model_required_fields
		}
	
	@property
	def optional_fields(self) -> dict[str, Any]:
		return {
			name: getattr(self, name)
			for name in self.__class__.model_optional_fields
		}

	@property
	def nondefault_fields(self) -> dict[str, Any]:
		result = self.required_fields
		result.update({
			name: current
			for name, info in self.__class__.model_ordered_fields.items()
			if (current := getattr(self, name)) != info.default
		})
		return result
	
	@classproperty
	def min_fields_count(cls) -> int:
		return len(cls.model_required_fields)
	
	@classproperty
	def max_fields_count(cls) -> int:
		return len(cls.model_ordered_fields)
	
	########################################################################################
	
	def __eq__(self, another: Any) -> bool:
		return type(another) is type(self) and self.to_dict() == another.to_dict()
	
	def __ne__(self, another: Any) -> bool:
		return not (self == another)
	
	########################################################################################

	def copy(self) -> Self: # type: ignore
		return self.model_copy()
	
	def deepcopy(self) -> Self:
		return self.model_copy(deep=True)
	
	########################################################################################

	def _set_extras(self, extras: Any) -> None:
		pass

	def _get_extras(self) -> Any:
		return None
	
	########################################################################################

	@final
	@model_validator(mode='before')
	@classmethod
	def __model_validator_before__(cls, data: Any) -> Any:
		return cls._before_validation(data)
	
	@final
	@model_validator(mode='after')
	def __model_validator_after__(self) -> Self:
		return self._after_validation()
	
	@classmethod
	def _before_validation(cls, data: Any) -> Any:
		if isinstance(data, str):
			return cls.from_str(data)
		return data
	
	def _after_validation(self) -> Self:
		return self
	
	########################################################################################

	@classmethod
	def from_dict(cls, data: dict) -> Self:
		extras = {}
		if 'extras' in data:
			extras = data.pop('extras')

		instance = cls.model_validate(data)
		if extras and cls.allows_extra():
			instance._set_extras(extras)

		return instance
	
	def to_dict(self) -> dict:
		data = self.nondefault_fields.copy()
		if self.allows_extra():
			extras = self._get_extras()
			if extras:
				data['extras'] = extras
		return data

	@classmethod
	def from_str(cls, line: str) -> Self:
		if not cls.is_event_class():
			raise ValueError(f'{cls.__name__} is not a event class')
		
		tokens = tokenize(line)
		command, args, extras = analyse_command(tokens)
		return cls.from_analysed(command, args, extras)

	def to_str(self) -> str:
		cls = self.__class__
		if not cls.is_event_class():
			raise TypeError(f'{cls.__name__} is not a event class')
		
		main_command = cls.main_command
		args = []
		for arg in cls.fields_order:
			info = cls.model_ordered_fields[arg]
			current = getattr(self, arg)
			if not info.is_required() and current == info.default:
				break
			args.append(current)
		
		args_str = '(' + ','.join(list(map(str, args))) + ')'

		extras_str = ''		
		if cls.allows_extra():
			extras = self._get_extras()
			if extras:
				extras_str = '[' + ','.join(list(map(str, extras))) + ']'

		
		return main_command + args_str + extras_str + cls.command_trailing
	
	def __str__(self) -> str:
		return self.to_str()
	
	########################################################################################

	@classmethod
	def from_analysed(cls, command: str, args: tuple, extras: tuple | None = None) -> Self:
		if not cls.is_event_class():
			raise ValueError(f'{cls.__name__} is not a event class')
		
		if command not in cls.commands:
			raise ValueError(f'Command name does not match; expected any of {cls.commands!r}, got {command}')
		
		return cls.from_args(args, extras)
	
	@classmethod
	def from_args(cls, args: tuple, extras: tuple | None = None) -> Self:
		if not cls.is_event_class():
			raise ValueError(f'{cls.__name__} is not a event class')
		
		argc = len(args)
		maxc = cls.max_fields_count
		minc = cls.min_fields_count
		if argc > maxc or argc < minc:
			argc_str = (
				str(maxc) if maxc == minc
				else f'{minc} to {maxc}'
			)
			raise ValueError(f'invalid format; expected {argc_str} arguments, got {argc}')
		
		data: dict = {name: arg for name, arg in zip(cls.fields_order, args)}
		instance = cls.model_validate(data)

		if extras:
			instance._set_extras(extras)

		return instance
	
	########################################################################################

	@final
	@classmethod
	def from_any(cls, data: Any) -> Self:
		errors: list = []

		for name in cls.__converters__:
			func = getattr(cls, name)
			try:
				return func(data)
		
			except ValidationError as e:
				for error in e.errors():
					if 'ctx' not in error:
						error['ctx'] = {}
					
					error['ctx']['converter'] = name
					error['ctx']['error'] = e
					errors.append(error) # type: ignore

			except (ValueError, TypeError) as e:
				errors.append({
					'type': 'value_error',
					'input': data,
					'ctx': {'converter': name, 'error': e}
				})
		
		if errors:
			raise ValidationError.from_exception_data(
				title = f"instantiating {cls.__name__} from {data}",
				line_errors = errors
			)
		
		raise UnreachableBranch


class GameObjectEvent(AFFEvent):
	def mirror(self) -> None:
		pass

class TechnicalEvent(AFFEvent):
	pass


class FloorEvent(GameObjectEvent):
	pass

class SkyEvent(GameObjectEvent):
	pass


class LongNoteEvent(GameObjectEvent):
	@property
	def time_range(self) -> tuple[int, int]:
		return (self.begin_time, self.end_time)
	
	@time_range.setter
	def time_range(self, value: tuple[int, int]) -> None:
		begin, end = value
		if begin > end:
			raise ValueError(f'Invalid time range; begin should not be greater than end')
		
		if begin <= self.end_time:
			self.begin_time, self.end_time = begin, end
		else:
			self.end_time, self.begin_time = end, begin

	@property
	def duration(self) -> int:
		return self.end_time - self.begin_time
	
	def __len__(self) -> int:
		return self.duration
	
	def _after_validation(self) -> Self:
		super()._after_validation()
		if self.end_time < self.begin_time:
			raise ValueError('end_time must be greater than or equal to begin_time')
		return self

class TapLikeEvent(GameObjectEvent):
	pass