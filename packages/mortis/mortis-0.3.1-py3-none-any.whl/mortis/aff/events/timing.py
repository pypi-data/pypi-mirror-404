from __future__ import annotations

from math import isclose
from typing import ClassVar, Self

from pydantic import NonNegativeInt as uint

from mortis.aff.types.models import AFFEventConfig, TechnicalEvent
from mortis.aff.types.dffloat import dffloat2


__all__ = ['Timing']

class Timing(TechnicalEvent):
	
	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		commands=('timing', ),
		argument_order=('time', 'bpm', 'beat')
	)

	time: uint
	bpm: dffloat2
	beat: dffloat2

	def _after_validation(self) -> Self:
		super()._after_validation()
		
		if self.beat < 0:
			raise ValueError(f'beat must be non-negative')
		
		TOLERANCE = 0.009
		if not isclose(self.bpm, 0, abs_tol=TOLERANCE) and isclose(self.beat, 0, abs_tol=TOLERANCE):
			raise ValueError(f'beat cannot be zero if bpm is non-zero')
		
		if self.time == 0:
			if self.bpm < 0:
				raise ValueError(f'bpm of initial timing (time == 0) must be non-negative')
			if self.beat < 0:
				raise ValueError(f'beat of initial timing (time == 0) must be non-negative')
		
		return self
	
	@property
	def beat_duration_ms(self) -> float:
		return 6e4 / self.bpm
	
	@property
	def measure_duration_ms(self) -> float:
		return self.beat_duration_ms * self.beat