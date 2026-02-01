from __future__ import annotations

from enum import StrEnum
from typing import ClassVar, Self

from pydantic import NonNegativeInt as uint

from mortis.aff.types.models import AFFEventConfig, TechnicalEvent
from mortis.aff.types.dffloat import dffloat2


__all__ = ['SceneControlType', 'SceneControl']

class SceneControlType(StrEnum):

	TrackHide = trackhide = 'trackhide'
	TrackShow = trackshow = 'trackshow'
	
	TrackDisplay = trackdisplay = 'trackdisplay'
	RedLine = redline = 'redline'
	ArcahvDistort = arcahvdistort = 'arcahvdistort'
	ArcahvDebris = arcahvdebris = 'arcahvdebris'
	HideGroup = hidegroup = 'hidegroup'
	EnwidenCamera = enwidencamera = 'enwidencamera'
	EnwidenLanes = enwidenlanes = 'enwidenlanes'


class SceneControl(TechnicalEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		commands=('scenecontrol', ),
		argument_order=('time', 'type_', 'duration', 'target_state')
	)
	
	time: uint
	type_: SceneControlType
	duration: dffloat2 | None = None
	target_state: uint | None = None

	def _after_validation(self) -> Self:
		super()._after_validation()

		# scenecontrol(t, type);
		if self.type_ in [SceneControlType.TrackHide, SceneControlType.TrackShow]:
			if self.duration is not None or self.target_state is not None:
				raise ValueError(f'{self.type_} does not accept any extra parameter')
			
			return self
			
		# scenecontrol(t, type, duration, target_state);
		if self.type_ == SceneControlType.HideGroup:
			# unused, but need a non-None value
			if self.duration is None:
				self.duration = dffloat2(1.00)
		else:
			if self.duration is None:
				raise ValueError(f'duration of {self.type_} is necessary')
		
		if self.duration < 0:
			raise ValueError(f'duration must be non-negative, got {self.duration}')
		
		if self.type_ == SceneControlType.RedLine:
			# unused, but need a non-None value.
			if self.target_state is None:
				self.target_state = 0
		else:
			if self.target_state is None:
				raise ValueError(f'target_state of {self.type_} is necessary')
			
			if self.type_ in {
				SceneControlType.EnwidenCamera,
				SceneControlType.EnwidenLanes,
				SceneControlType.HideGroup,
			} and self.target_state not in {0, 1}:
				raise ValueError(
					f'target_state of {self.type_} is a switch value that only accepts 0 or 1, got {self.target_state}'
				)
		
		return self