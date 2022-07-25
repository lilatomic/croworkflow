from ops import *
from interpreter import Interpreter


class TestBasic:
	proc0 = Proc(lambda x: 2 * x)
	proc1 = Proc(lambda x: x + 5)
	seq = WfSeq((proc0, proc1))
	par = WfPar((proc0, proc1))
	predicate = Proc(lambda x: x % 2 == 0)

	def test_runs_op(self):
		v = Interpreter().interpret(self.proc0, 2)
		assert v == 4

	def test_runs_seq(self):
		v = Interpreter().interpret(self.seq, 3)
		assert v == 11

	def test_runs_par(self):
		v = Interpreter().interpret(self.par, 3)
		assert v == (6, 8)

	def test_runs_cond_true(self):
		ops = WfConditional(self.predicate, if_true=self.proc0)
		v = Interpreter().interpret(ops, 6)
		assert v == 12

	def test_runs_cond_false(self):
		ops = WfConditional(self.predicate, if_false=self.proc0)
		v = Interpreter().interpret(ops, 5)
		assert v == 10


class TestGenerators:
	predicate = Proc(lambda x: x % 3)

	def test_evaluates_generator(self):
		ops = GroupBy(self.predicate)
		# v = Interpreter().begin_interpret(ops, range(0, 3))
		v = Interpreter().begin_interpret(ops, range(0, 12))
		assert v == {0: [0, 3, 6, 9], 1: [1, 4, 7, 10], 2: [2, 5, 8, 11]}

class TestGraph:

	def test_generate_sample(self):
	# 	ops = Proc(lambda x: list(range(0, x)), "range") >> \
	# 		WfFor(Proc(lambda x: x*2)) >> \
	# 		GroupBy(Proc(lambda x: x % 3, "mod3"))
	# 	print(ops.ops)

	# 	Interpreter().begin_interpret(ops, 12)

	# def o(self):
		ops = Proc(lambda x: list(range(0, x)), "range") >> \
			WfFor(
				WfConditional(Proc(lambda x: x < 5, "is smol"), Proc(lambda x: x * 2, "double"), Proc(lambda x: x - 5, "make smaller"))
			) >> \
			GroupBy(Proc(lambda x: x % 3, "mod3")) >> \
			Proc(lambda x: x.items(), "items") >> \
			WfFor(Proc(lambda kv: print(f"<{kv[0]}:{kv[1]}>"), "print"))
		print(ops.ops)

		Interpreter().begin_interpret(ops, 12)
