from ops import *
from interpreter import Interpreter

class TestOperators:
	proc0 = Proc(lambda x: 2 * x)
	proc1 = Proc(lambda x: x + 5)
	seq0 = WfSeq((proc0, proc1))
	par0 = WfPar((proc0, proc1))
	seq1 = WfSeq((proc1, proc0))
	par1 = WfPar((proc1, proc0))


	def test_seq_procs(self):
		ops = self.proc0 >> self.proc1
		v = Interpreter().interpret(ops, 5)
		assert v == 15

	def test_seq_wfs(self):
		ops = self.seq0 >> self.seq1
		v = Interpreter().interpret(ops, 5)
		assert v == 40

	def test_seq_wfs_procs(self):
		ops = self.seq0 >> self.proc0
		v = Interpreter().interpret(ops, 5)
		assert v == 30

	def test_seq_proc_wfs(self):
		ops = self.proc0 >> self.seq0
		v = Interpreter().interpret(ops, 5)
		assert v == 25

	def test_seq_chained(self):
		ops = self.proc0 >> self.proc1 >> self.proc0
		v = Interpreter().interpret(ops, 5)
		assert v == 30


	def test_par_procs(self):
		ops = self.proc0 / self.proc1
		v = Interpreter().interpret(ops, 7)
		assert v == (14, 12)

	def test_par_wfs(self):
		ops = self.seq0 / self.seq1
		v = Interpreter().interpret(ops, 7)
		assert v == (19, 24)

	def test_par_mixed(self):
		ops = self.seq0 / self.proc0
		v = Interpreter().interpret(ops, 7)
		assert v == (19, 14)
