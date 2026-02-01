from __future__ import annotations

from typing import ClassVar

from pydantic import NonNegativeInt as uint

from mortis.aff.types.models import AFFEventConfig, FloorEvent, LongNoteEvent
from mortis.aff.types.coord import Coordinate, FixedLane, FloatLane


__all__ = ['Hold', 'HoldFloat']

class Hold(FloorEvent, LongNoteEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		commands=('hold', ),
		argument_order=('begin_time', 'end_time', 'lane')
	)

	begin_time: uint
	end_time: uint
	lane: FixedLane

	def to_fixed_lane(self) -> Hold:
		return self

	def to_float_lane(self) -> HoldFloat:
		return HoldFloat(
			begin_time = self.begin_time,
			end_time = self.end_time,
			lane = Coordinate.fixed_to_float(self.lane),
		)
	
	def mirror(self) -> None:
		self.lane = Coordinate.mirror_fixed(self.lane)


class HoldFloat(Hold):

	lane: FloatLane

	def to_float_lane(self) -> HoldFloat:
		return self

	def to_fixed_lane(self) -> Hold:
		return Hold(
			begin_time = self.begin_time,
			end_time = self.end_time,
			lane = Coordinate.float_to_fixed(self.lane),
		)
	
	def mirror(self) -> None:
		self.lane = Coordinate.mirror_float(self.lane) # type: ignore