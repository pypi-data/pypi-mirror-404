from __future__ import annotations

from typing import ClassVar

from pydantic import NonNegativeInt as uint

from mortis.aff.types.models import AFFEventConfig, FloorEvent, TapLikeEvent
from mortis.aff.types.coord import Coordinate, FixedLane, FloatLane


__all__ = ['Tap', 'TapFloat']

class Tap(FloorEvent, TapLikeEvent):
	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		commands=('', ),
		argument_order=('time', 'lane')
	)

	time: uint
	lane: FixedLane

	def to_fixed_lane(self) -> Tap:
		return self

	def to_float_lane(self) -> TapFloat:
		return TapFloat(
			time = self.time,
			lane = Coordinate.fixed_to_float(self.lane),
		)
	
	def mirror(self) -> None:
		self.lane = Coordinate.mirror_fixed(self.lane)


class TapFloat(Tap):

	lane: FloatLane

	def to_float_lane(self) -> TapFloat:
		return self

	def to_fixed_lane(self) -> Tap:
		return Tap(
			time = self.time,
			lane = Coordinate.float_to_fixed(self.lane)
		)
	
	def mirror(self) -> None:
		self.lane = Coordinate.mirror_float(self.lane) # type: ignore