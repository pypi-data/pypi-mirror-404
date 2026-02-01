from __future__ import annotations

from enum import IntEnum
from typing import Annotated, Any, Generic, TypeVar, final
from typing_extensions import Self

import annotated_types
from pydantic import AfterValidator, Field, model_validator

from mortis.globcfg import GlobalConfig
from mortis.songlist.base import SonglistPartModel
from mortis.utils import classproperty


__all__ = [
	'LowerAsciiId', 'BackgroundStr', 'SingleLineStr',
	'GuardinaError',
	'Localized', 'LocalizedReqEn', 'StrLocalizedSLRE',
	'SideEnum', 'RatingClassEnum',
	'RTCLS_STR_MAP', 'RatingInt',
	'Backgrounds', 'BACKGROUNDS',
]


def ensure_lower_ascii_id(s: str) -> str:
	if s.isidentifier() and s.isascii() and s.lower() == s:
		return s
	raise ValueError(f'{s!r} is not a lowercase ASCII identifier')
LowerAsciiId = Annotated[str, AfterValidator(ensure_lower_ascii_id)]


def ensure_bg(s: str) -> str:
	for ch in s:
		if ch in 'qwertyuiopasdfghjklzxcvbnm0123456789-_':
			continue
		raise ValueError(f'{s!r} is not a valid background str')
	return s
BackgroundStr = Annotated[str, AfterValidator(ensure_bg)]


def ensure_single_line(s: str) -> str:
	if '\n' not in s:
		return s
	raise ValueError(f'{s!r} is not in one line (contain no \'\\n\')')
SingleLineStr = Annotated[str, AfterValidator(ensure_single_line)]


@final
class GuardinaError(ValueError, KeyError):
	__instance__ = None
	def __new__(cls) -> Self:
		if cls.__instance__ is None:
			cls.__instance__ = super().__new__(cls)
		return cls.__instance__
	
	def __init__(self) -> None:
		pass

	def __str__(self) -> str:
		return f'\'kr\' is not a valid language code; do you mean \'ko\'?'
	
	def __repr__(self) -> str:
		return f'{self.__class__.__name__}()'

T = TypeVar('T')
class Localized(SonglistPartModel, Generic[T]):
	en: T | None = None
	ja: T | None = None
	ko: T | None = None
	zh_Hans: T | None = Field(default=None, alias='zh-Hans')
	zh_Hant: T | None = Field(default=None, alias='zh-Hant')

	@model_validator(mode='before')
	def _before_validation(cls, data: Any) -> Any:
		if not isinstance(data, dict):
			return data
		if 'kr' in data:
			if GlobalConfig.allows_kr_langcode:
				if 'ko' not in data:
					data['ko'] = data['kr']
				del data['kr']
			else:
				raise GuardinaError
		return data

	def __bool__(self) -> bool:
		return bool(self.nondefault_fields)

class LocalizedReqEn(Localized[T]):
	en: T  # pyright: ignore[reportGeneralTypeIssues, reportIncompatibleVariableOverride] | intended behaviour

	def __bool__(self) -> bool:
		return True

StrLocalizedSLRE = LocalizedReqEn[SingleLineStr]


class SideEnum(IntEnum):
	Light = 0
	Conflict = 1
	Achromatic = 2
	Lephon = 3

class RatingClassEnum(IntEnum):
	Past = 0
	Present = 1
	Future = 2
	Beyond = 3
	Eternal = 4
RTCLS_STR_MAP = {e: e.name.lower() for e in RatingClassEnum}


RatingInt = Annotated[int, annotated_types.Ge(-1)]


BACKGROUNDS = {
    SideEnum.Light: ('aegleseeker', 'aethercrest', 'alice_light', 'anima_light', 'arcahv', 'auxesia', 'azalea', 'base_light', 'chuni-worldvanquisher', 'chunithmnew_light', 'cytus_light', 'djmax_light', 'dynamix_light', 'eclipse_light', 'eden_append_light', 'eden_boss', 'eden_light', 'etherstrike', 'felis', 'finale_light', 'fractureray', 'gc_lance', 'gc_light', 'gou', 'hime_light', 'lanota-light', 'magnolia', 'maimai_light', 'meta_mysteria', 'mirai_light', 'modelista', 'musedash_light', 'nextstage_light', 'nijuusei-light-b', 'nijuusei2_light', 'nirvluce', 'observer_light', 'omatsuri_light', 'omegafour', 'ongeki_light', 'pragmatism', 'prelude_light', 'quon', 'rei', 'ringedgenesis', 'rotaeno_light', 'shiawase', 'shiawase2', 'single2_light', 'single_light', 'solitarydream', 'tanoc_light', 'tanoc_red', 'temptation', 'tonesphere-solarsphere', 'touhou_light', 'undertale_light', 'virtus', 'vs_light', 'vulcanus', 'wacca_light', 'zettai_light', 'megarex_light'),
    SideEnum.Conflict: ('alexandrite', 'alice_conflict', 'alterego', 'altergate', 'anima_conflict', 'apophenia', 'arcanaeden', 'arghena', 'axiumcrisis', 'base_conflict', 'chuni-garakuta', 'chuni-ikazuchi', 'chunithmnew_conflict', 'chunithmthird_conflict', 'codeoblivion', 'cyaegha', 'cytus_boss', 'cytus_conflict', 'djmax_conflict', 'djmax_nightmare', 'djmax_wagd', 'dynamix_conflict', 'eclipse_conflict', 'eden_append_conflict', 'eden_conflict', 'extradimensional', 'finale_conflict', 'gc_buchigire', 'gc_conflict', 'gc_ouroboros', 'grievouslady', 'hime_conflict', 'lamia', 'lanota-conflict', 'lethaeus', 'macula_conflict_a', 'maimai_boss', 'maimai_conflict', 'megalovaniarmx', 'mirai_awakened', 'mirai_conflict', 'musedash_conflict', 'nextstage_conflict', 'nihil', 'nijuusei-conflict-b', 'nijuusei2_conflict', 'observer_conflict', 'omatsuri_conflict', 'ongeki_conflict', 'pentiment', 'prelude_conflict', 'rotaeno_conflict', 'saikyostronger', 'sheriruth', 'single2_conflict', 'single_conflict', 'spidersthread', 'tanoc_conflict', 'tempestissimo', 'tiferet', 'tonesphere-darksphere', 'touhou_conflict', 'undertale_conflict', 'vs_conflict', 'wacca_boss', 'wacca_conflict', 'xterfusion', 'yugamu', 'zettai', 'tempestissimo_red', 'megarex_conflict', 'megarex_signal'),
    SideEnum.Achromatic: ('epilogue', 'testify'),
    SideEnum.Lephon: ('designant', 'lamentrain', 'lephon'),
}

class Backgrounds:
	@classmethod
	def is_official_bg(cls, bg: str) -> bool:
		return any(bg in bgs for bgs in BACKGROUNDS.values())

	@classmethod
	def matches(cls, side: SideEnum, bg: str) -> bool:
		return bg in BACKGROUNDS.get(side, ())
	
	@classproperty
	@classmethod
	def light_bgs(cls) -> tuple[str, ...]:
		return BACKGROUNDS[SideEnum.Light]
	
	@classproperty
	@classmethod
	def conflict_bgs(cls) -> tuple[str, ...]:
		return BACKGROUNDS[SideEnum.Conflict]
	
	@classproperty
	@classmethod
	def achromatic_bgs(cls) -> tuple[str, ...]:
		return BACKGROUNDS[SideEnum.Achromatic]
	
	@classproperty
	@classmethod
	def lephon_bgs(cls) -> tuple[str, ...]:
		return BACKGROUNDS[SideEnum.Lephon]