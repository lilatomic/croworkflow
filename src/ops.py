from __future__ import annotations

from collections import defaultdict
from enum import Enum

from typing import *
import abc

from _types import I, O, T


class Op(abc.ABC):
	def __rshift__(self, o: "Wf"):
		"""Run this operation and then that operation"""
		ops = []
		for i in [self, o]:
			if isinstance(i, WfSeq):
				ops.extend(i.ops)
			else:
				ops.append(i)
		return WfSeq(ops)

	def __floordiv__(self, o: "Wf"):
		"""Run this and that in parallel"""
		return WfPar((self, o,))


class Proc(Op):
	"""An operation"""

	def __init__(self, c: Callable, label: Optional[str]=None):
		self.c = c
		self.label = label

	def __call__(self, *args: Any, **kwds: Any) -> O:
		return self.c(*args, **kwds)

	def __str__(self):
		if self.label:
			return f"{self.label}<{id(self)}>"
		else:
			return f"proc<{id(self)}>"


class NOOP(Op):
	"""A no-operation"""
	...


class Const(Op):
	def __init__(self, value: O):
		self.value = value

	def __str__(self):
		return str(self.value)


class Wf(Op, abc.ABC):
	def __init__(self, label: Optional[str] = None):
		self.label = label

	def __str__(self):
		if self.label:
			return f"{self.label}<{id(self)}>"
		else:
			return f"{self.__class__.__name__}<{id(self)}>"


class WfSeq(Wf):
	"""Workflow which chains operations"""
	def __init__(self, ops: List["Op"], label = None):
		self.ops = ops
		super().__init__(label)


class WfPar(Wf):
	"""Workflow which runs multiple operations on the same value in parallel"""
	def __init__(self, ops: List["Op"], label = None):
		self.ops = ops
		super().__init__(label)


class WfFor(Wf):
	"""Workflow which runs the same operation on each item in the value in parallel"""
	def __init__(self, op: Op, label: Optional[str] = None):
		self.op = op
		super().__init__(label)


class WfConditional(Wf):
	"""Workflow which executed conditionally"""

	def __init__(self, cond: Op, if_true: Op = NOOP, if_false: Op = NOOP, label = None):
		self.cond = cond
		self.if_true = if_true
		self.if_false = if_false
		super().__init__(label)


class WfBound(Wf):
	"""
	Internal container for a workflow with a bound value
	Useful for generating workflows
	"""

	def __init__(self, op: Op, value: I, label = None):
		self.op = op
		self.value = value
		super().__init__(label)

	def __str__(self):
		return str(self.value)


class OpGen(Op):
	"""Operation that generates Operations"""

	@abc.abstractmethod
	def gen(self, value: I) -> Op:
		...


class GroupBy(OpGen):
	def __init__(self, partitioner):
		self.partitioner = partitioner

	@staticmethod
	def aggregate(kv_pairs: List[T, I]) -> Dict[T, List[I]]:
		out = defaultdict(list)
		for k,v in kv_pairs:
			out[k].append(v)
		return out

	def gen(self, value):
		keying_wf = WfFor(
			self.partitioner // NOOP(), label="GroupBy"
		)

		return keying_wf >> Proc(self.aggregate, "GroupBy.aggregate")


class Filter(OpGen):
	class FilterMode(Enum):
		Include = "include"
		Exclude = "exclude"

	def __init__(self, predicate, mode: FilterMode = FilterMode.Include):
		self.predicate = predicate
		self.mode = mode
		super().__init__()

	@staticmethod
	def filter_include(elems_pairs):
		return tuple((elem for elem, res in elems_pairs if res))

	@staticmethod
	def filter_exclude(elems_pairs):
		return tuple((elem for elem, res in elems_pairs if not res))

	def gen(self, value):
		if self.mode == Filter.FilterMode.Include:
			filter = Filter.filter_include
		else:
			filter = Filter.filter_exclude

		return WfFor(
			NOOP() // self.predicate, label="Filter"
		) >> Proc(filter)
