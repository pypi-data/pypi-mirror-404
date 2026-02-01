from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any, Self

from pydantic import BaseModel, BeforeValidator, NonNegativeInt as uint, PrivateAttr, ValidationError, model_validator

from mortis.aff.events.arc import Arc, ScaledArctap
from mortis.aff.events.camera import Camera
from mortis.aff.events.hold import Hold, HoldFloat
from mortis.aff.events.scenecontrol import SceneControl
from mortis.aff.events.tap import Tap, TapFloat
from mortis.aff.events.timing import Timing
from mortis.aff.types.hitsound_str import HitsoundStr
from mortis.aff.types.models import AFFEvent
from mortis.aff.lexer.analyse import analyse_command, analyse_timinggroup_footer, analyse_timinggroup_header
from mortis.aff.lexer.token import tokenize
from mortis.globcfg import GlobalConfig
from mortis.utils import get_default_model_cfg, Predicate


__all__ = ['parse_event', 'TimingGroup']

__registered_aff_events__: list[type[AFFEvent]] = []

def get_registered_aff_events():
	global __registered_aff_events__
	if not __registered_aff_events__:
		__registered_aff_events__ = [Timing, Arc, Tap, TapFloat, Hold, HoldFloat, SceneControl, Camera]
		if GlobalConfig.uses_scaled_arctap:
			__registered_aff_events__.insert(1, ScaledArctap)
	
	return __registered_aff_events__


def parse_event(
	command: str,
	args: tuple,
	extras: tuple | None = None,
) -> AFFEvent:
	
	errors: dict[str, Exception] = {}
	registered = get_registered_aff_events()
	for eventcls in registered:
		if command in eventcls.commands:
			try:
				return eventcls.from_args(args, extras)
			except Exception as e:
				errors[eventcls.__name__] = e
	
	input = {'command': command, 'args': args, 'extras': extras}
	raise ValidationError.from_exception_data(
		title = f'parsing AFF event from {input}',
		line_errors = [{
			'type': 'value_error',
			'loc': ('parse_aff_event', ),
			'input': input,
			'ctx': {'error': errors},
		}]
	)


def ensure_angle(ui: uint) -> uint:
	return ui % 3600
type AngleInt = Annotated[uint, BeforeValidator(ensure_angle)]

__timing_group_attrs__ = ('noinput', 'fadingholds', 'anglex', 'angley')
class TimingGroup(BaseModel):

	model_config = get_default_model_cfg()

	noinput: bool | None = None
	fadingholds: bool | None = None
	anglex: AngleInt | None = None
	angley: AngleInt | None = None

	_events: list[AFFEvent] = PrivateAttr(default_factory=list)


	@property
	def args(self) -> dict[str, bool | uint | None]:
		return {
			name: current
			for name in __timing_group_attrs__
			if (current := getattr(self, name)) is not None
		}
	
	@args.setter
	def args(self, args: Any) -> None:
		if isinstance(args, dict):
			valid_args = self.load_args_from_dict(args)
		elif isinstance(args, str):
			valid_args = self.load_args_from_str(args)
		elif args is None:
			del self.args
			return
		else:
			raise TypeError(f'Invalid type for TimingGroup args: {type(args).__name__!r}')
		
		for name, value in valid_args.items():
			setattr(self, name, value)

	@args.deleter
	def args(self) -> None:
		for name in __timing_group_attrs__:
			setattr(self, name, None)
	

	@classmethod
	def load_args_from_dict(cls, args: dict[str, Any]) -> dict[str, bool | uint | None]:
		valid_args = {}
		for name in args:
			if name in __timing_group_attrs__:
				valid_args[name] = args[name]
			else:
				raise ValueError(f'Unknown TimingGroup argument: {name!r}')
		
		return valid_args
	
	@classmethod
	def load_args_from_str(cls, args_str: str) -> dict[str, bool | uint | None]:
		args: dict[str, bool | uint | None] = {}
		segments: list[str] = [s.strip() for s in args_str.split('_')]

		for seg in segments:
			if seg == 'noinput':
				args['noinput'] = True

			elif seg == 'fadingholds':
				args['fadingholds'] = True

			elif seg.startswith('anglex'):
				value_str = seg[len('anglex'):].strip()
				args['anglex'] = int(value_str)

			elif seg.startswith('angley'):
				value_str = seg[len('angley'):].strip()
				args['angley'] = int(value_str)
			
			else:
				raise ValueError(f'Unknown TimingGroup argument: {seg!r}')
		
		return args
	

	def dump_args_to_dict(self) -> dict:
		return {
			attr: current
			for attr in __timing_group_attrs__
			if (current := getattr(self, attr)) is not None
		}

	def dump_args_to_str(self) -> str:		
		segments = []
		for attr, current in self.dump_args_to_dict().items():
			if current is True:
				segments.append(attr)
			else:
				segments.append(f'{attr}{current}')
		return '_'.join(segments)

	
	def iter_events(self) -> Iterator[AFFEvent]:
		yield from self._events

	@property
	def events(self) -> tuple[AFFEvent, ...]:
		return tuple(self._events)

	def find_event(self, event: AFFEvent) -> int:
		for i, ev in enumerate(self._events):
			if ev is event:
				return i
		return -1

	def __contains__(self, event: AFFEvent) -> bool:
		return self.find_event(event) != -1

	def add_event(self, event: AFFEvent) -> None:
		if not isinstance(event, AFFEvent):
			raise TypeError(f'Event must be of type {AFFEvent.__name__}')
		
		if event in self:
			raise ValueError('Event is already in this group')
		self._events.append(event)
	
	def remove_event(self, event: AFFEvent) -> None:
		idx = self.find_event(event)
		if idx == -1:
			raise ValueError('Event is not found in this group')
		del self._events[idx]
	
	def clear_events(self) -> None:
		self._events = []


	@property
	def required_hitsounds(self) -> set[HitsoundStr]:
		hitsounds: set[HitsoundStr] = set()
		for event in self.iter_events():
			if not isinstance(event, Arc):
				continue
			if not event.hitsound.is_none():
				hitsounds.add(event.hitsound)
		return hitsounds
	

	@classmethod
	def from_str(cls, contents: str, *, events_only: bool=False) -> Self:
		instance = cls()

		lines = contents.split('\n')
		tokens_list = list(map(tokenize, lines))
		if events_only:
			evtoks_list = tokens_list

		else:
			header_toks = tokens_list[0]
			evtoks_list = tokens_list[1:-1]
			footer_toks = tokens_list[-1]

			header_args = analyse_timinggroup_header(header_toks)
			analyse_timinggroup_footer(footer_toks)
			cls.args = header_args
		
		for evtoks in evtoks_list:
			command, args, extras = analyse_command(evtoks)
			event = parse_event(command, args, extras, )
			instance.add_event(event)
		
		return instance

	def to_str(self, *, events_only: bool=False) -> str:
		event_lines = list(map(str, self._events))
		if events_only:
			result = event_lines

		else:
			result = [
				f'timinggroup({self.dump_args_to_str()})' + '{'
			]
			result.extend(f'  {x}' for x in event_lines)
			result.append('};')
		
		return '\n'.join(result)

	def __str__(self) -> str:
		return self.to_str()

	def filter(self, predicate: Predicate) -> tuple[AFFEvent, ...]:
		return tuple(event for event in self.iter_events()if predicate(event))

	@model_validator(mode='after')
	def _after_validation(self) -> Self:
		if self.noinput is False:
			self.noinput = None

		if self.fadingholds is False:
			self.fadingholds = None
		return self