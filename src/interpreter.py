from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum
from dataclasses import dataclass, field
from typing import *
from uuid import UUID, uuid4

import pydot

import ops
from ops import Const, Labelled, Op, Proc, Wf, WfBound, WfConditional, NOOP, OpGen, WfFor, WfPar, WfSeq
from _types import I, O


class VirtualNode():
	def __init__(self, label: str):
		self.label = label
		self.uuid = str(uuid4())

	def __str__(self):
		return str(self.label)


class Interpreter:
	def __init__(self, graph=None, graph_root=None, head=None):
		if not graph:
			graph = pydot.Dot()
		self.graph = graph
		if not graph_root:
			graph_root = self.graph
		self.graph_root = graph_root
		if not head:
			head = str(uuid4())
		self.head = head
	siblings = defaultdict(list)


	@contextmanager
	def frame(self, op: Op, name: str) -> Interpreter:
		un = self._node_id(op)
		if hasattr(op, "label"):
			subgraph = pydot.Subgraph(f"cluster_{un}", label=name)
			self.graph.add_subgraph(subgraph)
		else:
			subgraph = self.graph
		yield Interpreter(graph=subgraph, graph_root=self.graph_root, head=self.head)


	def begin_interpret(self, op, value: I) -> O:
		try:
			v = self.interpret(op, value)
		finally:
			self.showplot()
		return v

	def showplot(self):
		self.graph.write('file.dot', format="raw", encoding="utf-8")

	def interpret(self, op: Op, value: I) -> O:
		self._graph_node(op, value)
		if isinstance(op, ops.Proc):
			value = op(value)
		elif isinstance(op, Const):
			value = op.value
		elif isinstance(op, Labelled):
			value = (value, self.interpret(op.op, value))
		elif isinstance(op, NOOP):
			...
		elif isinstance(op, WfSeq):
			with self.frame(op, str(op)) as frame:
				for op in op.ops:
					value = frame.interpret(op, value)
				self.head = frame.head
		elif isinstance(op, WfBound):
			value = self.interpret(op.op, op.value)
		elif isinstance(op, WfPar):
			value = self._interpret_in_parallel(op, value, self.ParallelMode.WfPar)

		elif isinstance(op, WfFor):
			with self.frame(op, str(op)) as frame:
				value = self._interpret_in_parallel(op, value, self.ParallelMode.WfFor)
		elif isinstance(op, WfConditional):
			cond_result = self.interpret(op.cond, value)
			if cond_result:
				value = self.interpret(op.if_true, value)
			else:
				value = self.interpret(op.if_false, value)
		elif isinstance(op, OpGen):
			generated_ops = op.gen(value)
			value = self.interpret(generated_ops, value)
		else:
			raise TypeError("op of incorrect type", ("expected",Op,), ("actual",type(op),))
		return value

	class ParallelMode(Enum):
		WfPar = "WfPar"
		WfFor = "WfFor"

	def _interpret_in_parallel(self, op, value, mode):
		frames = []
		if mode == self.ParallelMode.WfPar:
			for proc in op.ops:
				with self.frame(proc, str(proc)) as frame:
					ret = frame.interpret(proc, value)
					frames.append((frame, ret))
		elif mode == self.ParallelMode.WfFor:
			for v in value:
				sub_op = deepcopy(op.op)
				with self.frame(sub_op, str(sub_op)) as frame:
					ret = frame.interpret(sub_op, v)
					frames.append((frame, ret))
		else:
			raise TypeError("invalid parallel processing mode")
		traces = []
		values = []
		for frame, ret in frames:
			traces.append(frame)
			values.append(ret)
		merge_node = VirtualNode("gather")
		self._graph_fan_in(frames, merge_node)
		self.head = merge_node.uuid
		return tuple(values)

	@staticmethod
	def _node_id(n: Op):
		return str(uuid4())

	def _graph_node(self, n, value):
		this_id = str(uuid4())
		if isinstance(n, NOOP):
			return
		if isinstance(n, Labelled):
			return
		else:
			self.graph.add_node(pydot.Node(this_id, label = str(n)))
			self.graph_root.add_edge(pydot.Edge(self.head, this_id, label=str(value)))

			self.head = this_id

	def _graph_fan_in(self, frames, n):
		id_n  = n.uuid
		self.graph.add_node(pydot.Node(id_n, label = str(n)))
		for frame in frames:
			self.graph_root.add_edge(pydot.Edge(frame[0].head, id_n, label=str(frame[1])))
