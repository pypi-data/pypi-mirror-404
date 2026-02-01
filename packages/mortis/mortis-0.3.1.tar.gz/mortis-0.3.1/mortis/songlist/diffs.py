from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, Self

from pydantic import Field, NonNegativeInt as uint, PositiveInt as posint, PositiveFloat as posfloat, model_serializer, model_validator

from mortis.songlist.base import SonglistPartModel
from mortis.songlist.types import RTCLS_STR_MAP, BackgroundStr, RatingClassEnum, RatingInt, SingleLineStr, StrLocalizedSLRE


__all__ = ['Difficulty', 'Difficulties']

class Difficulty(SonglistPartModel):
	rating_class: RatingClassEnum = Field(alias='ratingClass')
	chart_designer: str = Field(alias='chartDesigner')
	jacket_designer: str = Field(alias='jacketDesigner')
	rating: RatingInt
	rating_plus: bool = Field(default=False, alias='ratingPlus')


	title_localized: StrLocalizedSLRE | None = None
	artist: SingleLineStr | None = None

	bpm: str | None = None
	bpm_base: posint | posfloat | None = None

	audio_override: bool = Field(default=False, alias='audioOverride')
	jacket_override: bool = Field(default=False, alias='jacketOverride')
	bg: BackgroundStr | None = None
	date: uint | None = None
	version: SingleLineStr | None = None

	audio_preview: uint | None = Field(default=None, alias='audioPreview')
	audio_preview_end: uint | None = Field(default=None, alias='audioPreviewEnd')

	def is_activated(self) -> bool:
		return self.rating != -1
	
	def __bool__(self) -> bool:
		return self.is_activated()

	@property
	def rating_str(self) -> str:
		return f'{self.rating}+' if self.rating_plus else str(self.rating)
	
	@model_validator(mode='after')
	def _after_validation(self) -> Self:
		if self.audio_preview is not None:
			if self.audio_preview_end is not None and self.audio_preview > self.audio_preview_end:
				raise ValueError(f'\'audioPreviewEnd\' must be no earlier than \'audioPreview\'')
			raise ValueError(f'\'audioPreview\' and \'audioPreviewEnd\' should be provided at the same time')
		elif self.audio_preview_end is not None:
			raise ValueError(f'\'audioPreview\' and \'audioPreviewEnd\' should be provided at the same time')

		return self


class _DifficultyList(SonglistPartModel):
	data: list[Difficulty]

	@model_validator(mode='before')
	@classmethod
	def _before_validation(cls, value: Any) -> Any:
		if isinstance(value, cls):
			return value
		elif isinstance(value, Iterable) and not isinstance(value, dict):
			return {'data': value}
		return value
	
	@model_validator(mode='after')
	def _after_validation(self) -> Self:
		found = set()
		duplicated: list[RatingClassEnum] = []

		for diff in self.data:
			rtcls = diff.rating_class
			if rtcls in found:
				duplicated.append(rtcls)
			else:
				found.add(rtcls)
		
		if duplicated:
			duplicated_str = ', '.join(e.name for e in duplicated)
			raise ValueError(f'Duplicated difficulties: {duplicated_str}')
		
		return self

	def to_dict(self) -> dict[str, Difficulty]:
		return {RTCLS_STR_MAP[item.rating_class]: item for item in self.data}


class Difficulties(SonglistPartModel):
	past: Difficulty
	present: Difficulty
	future: Difficulty
	beyond: Difficulty | None = None
	eternal: Difficulty | None = None

	@model_validator(mode='before')
	@classmethod
	def _before_validation(cls, value: Any) -> Any:
		if isinstance(value, cls):
			return value
		elif isinstance(value, Iterable) and not isinstance(value, dict):
			diff_list = _DifficultyList.model_validate(value)
			return diff_list.to_dict()
		elif isinstance(value, _DifficultyList):
			return value.to_dict()
		return value

	@property
	def all_declared(self) -> tuple[Difficulty, ...]:
		return tuple(self.nondefault_fields.values())
	
	def __len__(self) -> int:
		return len(self.all_declared)

	@property
	def all_activated(self) -> tuple[Difficulty, ...]:
		return tuple(
			diff for name in self.__class__.model_fields
			if (diff := getattr(self, name)) is not None and diff.is_activated()
		)

	@model_serializer
	def serialize(self) -> list[Difficulty]:
		return list(self.all_declared)

	def __getitem__(self, index: RatingClassEnum) -> Difficulty | None:
		index = RatingClassEnum(index)
		name = RTCLS_STR_MAP[index]
		diff = getattr(self, name)
		if diff is None:
			raise IndexError(f'No such difficulty: {index}')
		return diff
	
	def __setitem__(self, index: RatingClassEnum, value: Difficulty) -> None:
		index = RatingClassEnum(index)
		name = RTCLS_STR_MAP[index]
		value = Difficulty.model_validate(value)
		setattr(self, name, value)
	
	def __delitem__(self, index: RatingClassEnum) -> None:
		index = RatingClassEnum(index)
		if index in {RatingClassEnum.Past, RatingClassEnum.Present, RatingClassEnum.Future}:
			raise IndexError(f'Failed to delete difficulty {index.name}: required and undeletable')
		name = RTCLS_STR_MAP[index]
		setattr(self, name, None)
	
	def iter_difficulty(self) -> Iterator[Difficulty]:
		yield from self.all_declared

	def __contains__(self, rtcls: RatingClassEnum) -> bool:
		try:
			self[rtcls]
			return True
		except IndexError:
			return False