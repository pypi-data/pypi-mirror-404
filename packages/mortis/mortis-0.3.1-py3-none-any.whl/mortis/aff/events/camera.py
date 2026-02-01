from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import NonNegativeInt as uint

from mortis.aff.types.models import AFFEventConfig, TechnicalEvent
from mortis.aff.types.dffloat import dffloat2


__all__ = ['CameraEasing', 'Camera']

class CameraEasing(StrEnum):

	Linear = s = 's'
	CubicIn = qi = 'qi'
	CubicOut = qo = 'qo'
	Reset = reset = 'reset'


class Camera(TechnicalEvent):

	__aff_config__: ClassVar[AFFEventConfig] = AFFEventConfig(
		is_event=True,
		commands=('camera', ),
		argument_order=(
			'time',
			'truck', 'pedestral', 'dolly',
			'pan', 'tilt', 'roll',
			'easing', 'duration'
		)
	)
	
	time: uint
	truck: dffloat2
	"""Movement along the X-axis"""
	pedestral: dffloat2
	"""Movement along the Y-axis"""
	dolly: dffloat2
	"""Movement along the Z-axis"""
	pan: dffloat2
	"""Rotation around the Y-axis"""
	tilt: dffloat2
	"""Rotation around the X-axis"""
	roll: dffloat2
	"""Rotation around the Z-axis"""
	easing: CameraEasing
	duration: uint