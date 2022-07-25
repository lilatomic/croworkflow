from ops import Filter, Labelled, Proc, WfFor
from interpreter import Interpreter

def multiple_of(k: int):
    return Proc(lambda x: x % k == 0, f"Mutiple of {k}")

do_things = (
    Proc(lambda x: list(range(0, x)), "fetch parameters")
    >> WfFor(Labelled(multiple_of(2) // multiple_of(3)))
    >> Filter(Proc(lambda x: x[1][0] and x[1][1]))
    >> WfFor(Proc(lambda x: x[0]))
    >> WfFor(Proc(str, "str"), "str")
    >> Proc(lambda l: ", ".join(l), "format")
)

if __name__ == "__main__":
    n = 12
    print(Interpreter().begin_interpret(do_things, n))
