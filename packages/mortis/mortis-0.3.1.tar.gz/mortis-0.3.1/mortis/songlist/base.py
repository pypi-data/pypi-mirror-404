from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = []

class SonglistPartModel(BaseModel):
	model_config = ConfigDict(
		extra='ignore',
		allow_inf_nan=False,
		validate_by_alias=True,
		serialize_by_alias=True,
		validate_default=True,
		validate_assignment=True,
		json_encoders={Enum: lambda e: e.value}
	)

	def to_dict(self) -> dict:
		return self.model_dump(exclude_defaults=True, by_alias=True, mode='json')
	
	@property
	def nondefault_fields(self) -> dict[str, Any]:
		result = {}
		for name, info in self.__class__.model_fields.items():
			attr = getattr(self, name)
			if info.is_required() or attr != info.default:
				result[name] = attr
		return result