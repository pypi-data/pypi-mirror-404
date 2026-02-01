from __future__ import annotations

from enum import IntEnum

from mortis.aff.types.dffloat import dffloat2, dffloat3


__all__ = ['FixedLane', 'FloatLane', 'ArcCoord', 'Coordinate']

class FixedLane(IntEnum):
	
	Leftmost = Leftmost6k = Lane0 = 0
	Leftmost4k = Lane1 = 1
	Lane2 = 2
	Lane3 = 3
	Rightmost4k = Lane4 = 4
	Rightmost = Rightmost6k = Lane5 = 5

ArcCoord = dffloat2
FloatLane = dffloat3

class Coordinate:
	@staticmethod
	def arc_to_fixed(value: ArcCoord) -> FixedLane:
		arc = ArcCoord(value)
		return (
			FixedLane.Leftmost
			if (raw := round(ArcCoord(arc) * 2 + 1.5)) < FixedLane.Leftmost
			else (
				FixedLane.Rightmost
				if raw > FixedLane.Rightmost
				else FixedLane(raw)
			)
		)
	
	@staticmethod
	def arc_to_float(value: ArcCoord) -> FloatLane:
		arc = ArcCoord(value)
		return FloatLane(arc / 2 + 0.25)

	@staticmethod
	def fixed_to_arc(value: FixedLane) -> ArcCoord:
		fixed_lane = FixedLane(value)
		return ArcCoord(fixed_lane.value / 2 - 0.75)

	@staticmethod
	def fixed_to_float(value: FixedLane) -> FloatLane:
		fixed_lane = FixedLane(value)
		return FloatLane(fixed_lane.value / 4 - 0.125)
	
	@staticmethod
	def float_to_arc(value: FloatLane) -> ArcCoord:
		float_lane = FloatLane(value)
		return ArcCoord(float_lane * 2 - 0.5)
	
	@staticmethod
	def float_to_fixed(value: FloatLane) -> FixedLane:
		float_lane = FloatLane(value)
		return (
			FixedLane.Leftmost
			if (raw := round(float_lane * 4 + 0.5)) < FixedLane.Leftmost
			else (
				FixedLane.Rightmost
				if raw > FixedLane.Rightmost
				else FixedLane(raw)
			)
		)
	
	@staticmethod
	def mirror_arc(value: ArcCoord) -> ArcCoord:
		return ArcCoord(1.0 - ArcCoord(value))
	
	@staticmethod
	def mirror_float(value: FloatLane) -> FloatLane:
		return FloatLane(1.0 - FloatLane(value))
	
	@staticmethod
	def mirror_fixed(value: FixedLane) -> FixedLane:
		return FixedLane(5 - value.value)