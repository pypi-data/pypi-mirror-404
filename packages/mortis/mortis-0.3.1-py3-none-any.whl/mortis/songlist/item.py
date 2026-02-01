from __future__ import annotations

import json
from io import TextIOWrapper
from typing import Literal, Self

from pydantic import Field, NonNegativeInt as uint, PositiveFloat as posfloat, PositiveInt as posint, PrivateAttr, field_serializer, model_validator

from mortis.songlist.base import SonglistPartModel
from mortis.songlist.diffs import Difficulties
from mortis.songlist.types import Backgrounds, LowerAsciiId, BackgroundStr, SideEnum, SingleLineStr, StrLocalizedSLRE
from mortis.utils import UnreachableBranch


__all__ = ['SonglistItem']

class SonglistItem(SonglistPartModel):

	# idx: uint
	id: LowerAsciiId
	title_localized: StrLocalizedSLRE

	## mutex: artist & artist_localized
	artist: SingleLineStr | None = None
	artist_localized: StrLocalizedSLRE | None = None

	bpm: str
	bpm_base: posint | posfloat
	pack: LowerAsciiId = Field(alias='set')
	purchase: LowerAsciiId | Literal[""]

	side: SideEnum
	@field_serializer('side', when_used='json')
	def _serialize_side(self, v: SideEnum) -> int:
		return v.value
	
	bg: BackgroundStr
	date: uint
	version: SingleLineStr
	audio_preview: uint = Field(alias='audioPreview')
	audio_preview_end: uint = Field(alias='audioPreviewEnd')

	difficulties: Difficulties


	_relcheck: bool = PrivateAttr(default=True)
	def _enable_relcheck(self) -> None:
		self._relcheck = True
	def _disable_relcheck(self) -> None:
		self._relcheck = False


	@model_validator(mode='after')
	def _after_validation(self) -> Self:
		if not self._relcheck:
			return self
		
		if self.audio_preview > self.audio_preview_end:
			raise ValueError(f'\'audioPreviewEnd\' must be no earlier than \'audioPreview\'')
		
		if (
			Backgrounds.is_official_bg(self.bg)
			and not Backgrounds.matches(self.side, self.bg)
		):
			raise ValueError(f'\'bg\' ({self.bg}) does not match the \'side\' ({self.side})')

		
		if self.artist is None and self.artist_localized is None:
			raise ValueError(f'At least one of \'artist\' and \'artist_localized\' should be provided')
		if self.artist is not None and self.artist_localized is not None:
			raise ValueError(f'At most one of \'artist\' and \'artist_localized\' should be provided')

		return self
	
	def __enter__(self) -> Self:
		self._disable_relcheck()
		return self
	
	def __exit__(self, exc_type, exc, tb):
		self._enable_relcheck()
		self._after_validation # trigger model after validator
	
	def use_localized_artist(self) -> None:
		if self.artist_localized is not None:
			return
		with self as ctx:
			assert ctx.artist is not None, UnreachableBranch()
			ctx.artist_localized = StrLocalizedSLRE(en=ctx.artist)
			ctx.artist = None
	
	def use_simple_artist(self) -> None:
		if self.artist is not None:
			return
		with self as ctx:
			assert ctx.artist_localized is not None, UnreachableBranch()
			ctx.artist = ctx.artist_localized.en
			ctx.artist_localized = None
	
	
	@classmethod
	def load_from_path(cls, path, /) -> Self:
		with open(path, 'r', encoding='utf-8') as f:
			return cls.load(f)

	@classmethod
	def load(cls, file: TextIOWrapper, /) -> Self:
		lines = file.read()
		return cls.loads(lines)

	@classmethod
	def loads(cls, lines: str, /) -> Self:
		return cls.model_validate_json(lines)

	def dumps(self, /, *, indent: int | None=None) -> str:
		return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

	def dump(self, file: TextIOWrapper, /, *, indent: int | None=None) -> None:
		file.write(self.dumps(indent=indent))
	
	def dump_to_path(self, path, /, *, indent: int | None=None) -> None:
		with open(path, 'w', encoding='utf-8') as f:
			self.dump(f, indent=indent)