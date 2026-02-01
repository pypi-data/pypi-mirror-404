from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import IntEnum, StrEnum
from typing import Any, ClassVar, Self

from pydantic import NonNegativeInt as uint, PrivateAttr

from mortis.aff.types.hitsound_str import HitsoundStr
from mortis.aff.types.models import AFFEventConfig, LongNoteEvent, SkyEvent, TapLikeEvent
from mortis.aff.types.coord import ArcCoord, Coordinate
from mortis.aff.types.easings import ArcEasing, BaseEasing, get_easing_x, get_easing_y
from mortis.aff.types.dffloat import dffloat2


__all__ = ['ArcType', 'ArcColor', 'Arctap', 'Arc', 'ScaledArctap']

class ArcType(StrEnum):

	Solid = Snake = False_ = 'false'
	Void = Trace = True_ = 'true'
	Designant = 'designant'


class ArcColor(IntEnum):

	Blue = 0
	Red = 1
	Green = 2
	Gray = Grey = 3


class Arctap(SkyEvent, TapLikeEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		trailing='',
		commands=('arctap', 'at'),
		argument_order=('time',)
	)
	__converters__: ClassVar[tuple[str, ...]] = 'from_int', 'from_str'

	time: uint

	_parent: Arc | None = PrivateAttr(default=None)

	@property
	def parent(self) -> Arc | None:
		return self._parent
	
	@parent.setter
	def parent(self, value: Arc | None) -> None:
		if value is None:
			del self.parent
		else:
			self.bind_to(value)
	
	@parent.deleter
	def parent(self) -> None:
		self.unbind()	

	def bind_to(self, arc: Arc) -> None:
		if not isinstance(arc, Arc):
			raise TypeError('arc must be an instance of Arc')
		
		if self._parent is arc:
			return

		if self._parent is not None:
			self.unbind()

		if self.time > arc.end_time or self.time < arc.begin_time:
			raise ValueError(f'Arctap time {self.time} is not within the range of arc: {arc.time_range}')

		arc._arctaps.append(self)
		arc._arctaps.sort(key=lambda at: at.time)
		self._parent = arc

	def unbind(self) -> None:
		if self._parent is None:
			return
		
		idx = self._parent.find_arctap(self)
		del self._parent._arctaps[idx]
		self._parent = None

	def position(self) -> tuple[float, float]:
		if self._parent is None:
			raise ValueError('Arctap is not bound to any arc')
		return self._parent.position_at(self.time)
	
	@classmethod
	def from_int(cls, value: int) -> Self:
		try:
			return cls(time=int(value))
		except (ValueError, TypeError) as e:
			raise ValueError(e)
	
	def copy(self) -> Self:
		return self.__copy__()
	
	def deepcopy(self) -> Self:
		return self.__deepcopy__()
	
	def __copy__(self) -> Self:
		return self.__class__(time=self.time)
	
	def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
		instance = self.__class__(time=self.time)
		instance.parent = self.parent
		return instance


class Arc(SkyEvent, LongNoteEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		uses_extra_args=True,
		commands=('arc', ),
		argument_order=(
			'begin_time', 'end_time',
			'begin_x', 'end_x',
			'easing',
			'begin_y', 'end_y',
			'color', 'hitsound', 'type_',
			'smoothness'
		)
	)
	
	begin_time: uint
	end_time: uint
	begin_x: ArcCoord
	end_x: ArcCoord
	easing: ArcEasing
	begin_y: ArcCoord
	end_y: ArcCoord
	color: ArcColor
	hitsound: HitsoundStr
	type_: ArcType
	smoothness: dffloat2 | None = None

	_arctaps: list[Arctap] = []
	
	@property
	def easing_x(self) -> BaseEasing:
		return get_easing_x(self.easing)(self.begin_time, self.end_time, self.begin_x, self.end_x)
	
	@property
	def easing_y(self) -> BaseEasing:
		return get_easing_y(self.easing)(self.begin_time, self.end_time, self.begin_y, self.end_y)
	

	def iter_arctaps(self) -> Iterator[Arctap]:
		yield from self._arctaps
	
	@property
	def arctaps(self) -> tuple[Arctap, ...]:
		return tuple(self._arctaps)
	
	def find_arctap(self, arctap: Arctap) -> int:
		for i, at in enumerate(self._arctaps):
			if at is arctap: # check identity (`is`) because we are maintaining refs
				return i
		return -1
	
	def add_arctap(self, arctap: Arctap) -> None:
		if arctap in self:
			raise ValueError('Arctap is already added to this arc')
		arctap.bind_to(self)
	
	def remove_arctap(self, arctap: Arctap) -> None:
		if arctap not in self:
			raise ValueError('Arctap is not found in this arc')
		arctap.unbind()
	
	def clear_arctaps(self) -> None:
		for at in self._arctaps:
			at.unbind()
	
	def extend_arctaps(self, arctaps: Iterable[Arctap]) -> None:
		for at in arctaps:
			self.add_arctap(at)

	def _get_extras(self) -> Any:
		return self._arctaps
	
	def _set_extras(self, extras: Any) -> None:
		try:
			arctaps = list(map(Arctap.from_any, list(extras)))
			for arctap in arctaps:
				arctap.bind_to(self)
		except (ValueError, TypeError) as e:
			raise ValueError(e)
	
	def position_at(self, time: int) -> tuple[float, float]:
		x = self.easing_x.at(time)
		y = self.easing_y.at(time)
		return (x, y)

	def __contains__(self, arctap: Arctap) -> bool:
		return self.find_arctap(arctap) != -1
	
	@classmethod
	def from_scaled_arctap(cls, sat: ScaledArctap) -> Self:
		return cls(
			begin_time = sat.time,
			end_time = sat.time,
			begin_x = sat.begin_x,
			end_x = sat.end_x,
			easing = ArcEasing.S,
			begin_y = sat.y,
			end_y = sat.y,
			color = ArcColor.Grey,
			hitsound = sat.hitsound,
			type_ = ArcType.Solid,
		)
	
	def to_scaled_arctap(self) -> ScaledArctap:
		return ScaledArctap.from_arc(self)
	
	def is_scaled_arctap(self) -> bool:
		try:
			self.to_scaled_arctap()
			return True
		except ValueError:
			return False

	def _after_validation(self) -> Self:
		super()._after_validation()

		if all([
			self.begin_time == self.end_time,
			self.begin_x == self.end_x,
			self.begin_y == self.end_y
		]):
			raise ValueError(f'The start and end points of arc cannot be the same')

		return self
	
	def clip(
		self,
		begin: uint,
		end: uint,
		/, *, 
		preserve_arctaps: bool = True
	) -> Arc:
		
		begin = int(begin)
		end = int(end)
		
		arc = self.model_copy()
		arc.time_range = begin, end

		if any([
			begin < self.begin_time,
			end > self.end_time
		]):
			raise ValueError(f'Clip is out of the range of the arc')
		
		begin_x, begin_y = self.position_at(begin)
		end_x, end_y = self.position_at(end)

		arc.clear_arctaps()
		arc.begin_x, arc.begin_y = ArcCoord(begin_x), ArcCoord(begin_y)
		arc.end_x, arc.end_y = ArcCoord(end_x), ArcCoord(end_y)

		if preserve_arctaps:
			arc.extend_arctaps(
				at for at in self._arctaps
				if at.time >= begin and at.time <= end
			)

		return arc
	
	def copy(self) -> Self:
		return self.__copy__()
	
	def deepcopy(self) -> Self:
		return self.__deepcopy__()
	
	def __copy__(self) -> Self:
		cls = self.__class__
		data = {
			name: getattr(self, name)
			for name in cls.fields_order
		}
		return cls(**data)
	
	def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
		instance = self.__copy__()
		for at in self.arctaps:
			copied_at = at.__deepcopy__()
			copied_at.bind_to(instance)

		return instance
	
	def mirror(self) -> None:
		self.begin_x = ArcCoord(1.0 - self.begin_x)
		self.end_x = ArcCoord(1.0 - self.end_x)


class ScaledArctap(SkyEvent, TapLikeEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		uses_extra_args=True,
		commands=('arc', ),
		argument_order=('time', 'begin_x', 'end_x', 'y', 'hitsound')
	)
	
	time: uint
	begin_x: ArcCoord
	end_x: ArcCoord
	y: ArcCoord
	hitsound: HitsoundStr

	@classmethod
	def from_arc(cls, arc: Arc) -> Self:
		if not all([
			arc.begin_time == arc.end_time,
			arc.begin_y == arc.end_y,
			arc.color == ArcColor.Grey,
			arc.type_ == ArcType.Solid,
			len(arc.arctaps) == 0
		]):
			raise ValueError(f'Failed to convert this arc to a scaled arctap')
		
		return cls(
			time = arc.begin_time,
			begin_x = arc.begin_x,
			end_x = arc.end_x,
			y = arc.begin_y,
			hitsound = arc.hitsound
		)

	def to_arc(self) -> Arc:
		return Arc.from_scaled_arctap(self)
	
	@classmethod
	def from_str(cls, line: str) -> Self:
		arc = Arc.from_str(line)
		return cls.from_arc(arc)

	def to_str(self) -> str:
		return self.to_arc().to_str()
	

	@classmethod
	def from_dict(cls, data: dict) -> Self:
		arc = Arc.from_dict(data)
		return cls.from_arc(arc)
	
	@classmethod
	def from_analysed(cls, command: str, args: tuple, extras: tuple | None = None) -> Self:
		arc = Arc.from_analysed(command, args, extras)
		return cls.from_arc(arc)
	
	@classmethod
	def from_args(cls, args: tuple, extras: tuple | None = None) -> Self:
		arc = Arc.from_args(args, extras)
		return cls.from_arc(arc)
	
	def mirror(self) -> None:
		self.begin_x = Coordinate.mirror_arc(self.begin_x)
		self.end_x = Coordinate.mirror_arc(self.end_x)
