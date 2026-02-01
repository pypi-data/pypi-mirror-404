from __future__ import annotations

from collections.abc import Iterable, Iterator
from io import TextIOWrapper
from typing import Any, Literal, Self

from pydantic import BaseModel, model_validator

from mortis.aff.lexer.analyse import analyse_annotation, analyse_command, analyse_part_separation, analyse_timinggroup_footer, analyse_timinggroup_header
from mortis.aff.lexer.token import tokenize
from mortis.aff.types.hitsound_str import HitsoundStr
from mortis.aff.types.models import AFFEvent
from mortis.aff.timinggroup import TimingGroup, parse_event
from mortis.utils import get_default_model_cfg


__all__ = ['AFF']

AudioOffset = 'AudioOffset'
TPDF = 'TimingPointDensityFactor'
class AFF(BaseModel):

	model_config = get_default_model_cfg()

	attrs: dict[str, Any] = {AudioOffset: 0}
	base_group: TimingGroup
	other_groups: list[TimingGroup] = []

	@property
	def offset(self) -> int:
		return self.attrs[AudioOffset]
	
	@offset.setter
	def offset(self, value: int) -> None:
		try:
			self.attrs[AudioOffset]  = int(value)
		except (ValueError, TypeError) as e:
			raise ValueError(e)
	
	@offset.deleter
	def offset(self) -> None:
		self.attrs[AudioOffset] = 0


	def iter_groups(self) -> Iterator[TimingGroup]:
		yield self.base_group
		yield from self.other_groups

	@property
	def groups(self) -> tuple[TimingGroup, ...]:
		return tuple(self.iter_groups())


	def iter_events(self) -> Iterator[AFFEvent]:
		for group in self.iter_groups():
			yield from group.iter_events()
	
	@property
	def events(self) -> tuple[AFFEvent, ...]:
		return tuple(self.iter_events())


	@property
	def tpdf(self) -> float | None:
		return self.attrs.get(TPDF)
	
	@tpdf.setter
	def tpdf(self, value: float) -> None:
		try:
			self.attrs[TPDF] = float(value)
		except (ValueError, TypeError) as e:
			raise ValueError(e)
	
	@tpdf.deleter
	def tpdf(self) -> None:
		if TPDF not in self.attrs:
			return
		del self.attrs[TPDF]

	def unwrap_tpdf(self) -> float:
		return 1.0 if self.tpdf is None else self.tpdf
	

	@classmethod
	def load_from_path(cls, path) -> Self:
		with open(path, 'r', encoding='utf-8') as f:
			return cls.load(f)

	@classmethod
	def load(cls, file: TextIOWrapper) -> Self:
		lines = file.readlines()
		return cls.load_lines(lines)
	
	@classmethod
	def loads(cls, line: str) -> Self:
		return cls.load_lines(line.split('\n'))

	@classmethod
	def load_lines(cls, lines: Iterable[str]) -> Self:
		attrs: dict[str, Any] = {}
		errors: dict[int, Exception] = {}

		base_group: TimingGroup = TimingGroup()
		other_groups: list[TimingGroup] = []
		current_group: TimingGroup = TimingGroup()

		status: Literal['anno', 'normal', 'ingroup'] = 'anno'
		for i, line in enumerate(lines):
			tokens = tokenize(line)

			if status == 'anno':
				try:
					analyse_part_separation(tokens)
					status = 'normal'
					continue
				except ValueError:
					pass

				try:
					anno_name, anno_val = analyse_annotation(tokens)
					attrs[anno_name] = anno_val
				except ValueError as e:
					errors[i] = e

			elif status == 'normal':
				try:
					header_args = analyse_timinggroup_header(tokens)
					current_group = TimingGroup()
					current_group.args = header_args
					status = 'ingroup'
					continue
				except ValueError:
					pass

				try:
					command, args, extras = analyse_command(tokens)
					event = parse_event(command, args, extras)
					base_group.add_event(event)
				except ValueError as e:
					errors[i] = e

			elif status == 'ingroup':
				try:
					analyse_timinggroup_footer(tokens)
					other_groups.append(current_group)
					status = 'normal'
					continue
				except ValueError:
					pass

				try:
					command, args, extras = analyse_command(tokens)
					event = parse_event(command, args, extras)
					current_group.add_event(event)
				except ValueError as e:
					errors[i] = e
		
		if errors:
			raise ValueError(f'Errors occurred during parsing. Details are: \n{errors!r}')
		
		return cls(
			attrs = attrs,
			base_group = base_group,
			other_groups = other_groups,
		)
	
	def dump_lines(self) -> list[str]:
		lines = [f'{attr}:{value}' for attr, value in self.attrs.items()]
		lines.append('-')
		lines.append(self.base_group.to_str(events_only=True))
		lines.extend(list(map(str, self.other_groups)))
		return lines
	
	def dumps(self) -> str:
		return '\n'.join(self.dump_lines())

	def dump(self, file: TextIOWrapper) -> None:
		file.write(self.dumps())
	
	def dump_to_path(self, path) -> None:
		with open(path, 'w', encoding='utf-8') as f:
			self.dump(f)
	
	def __str__(self) -> str:
		return self.dumps()
	

	@property
	def required_hitsounds(self) -> set[HitsoundStr]:
		hitsounds: set[HitsoundStr] = set()
		for group in self.iter_groups():
			hitsounds |= group.required_hitsounds
		return hitsounds


	@model_validator(mode='after')
	def _after_validation(self) -> Self:
		self.offset = self.attrs.get(AudioOffset, 0)
		
		tpdf = self.attrs.get('TimingPointDensityFactor')
		if tpdf is None:
			del self.tpdf
		else:
			self.tpdf = tpdf
		
		return self
	
	