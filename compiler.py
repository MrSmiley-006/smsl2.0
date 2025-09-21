from parser import *
from error import SmSLError
from collections import OrderedDict, namedtuple
import re
import sys

class Function:
    def __init__(self, name, params, code):
        self.params = params
        self.code = code
        self.name = name

    def __repr__(self):
        return f"Function(\n{self.name= }\n{self.params= }\n{self.code= })"

class OrderedDict(OrderedDict):
    def index(self, item):
        return list(self).index(item)

Func = namedtuple("Func", "consts vars funcs code")
    
class Compiler:
    def __init__(self, ast, func_=False):
        self.ast = ast
        self.cur_node = self.ast[0]
        self.out = ""
        self.line = 1
        self.instr = 0
        self.func_count = 0
        self.regs = []
        self.consts = ["0"]
        self.return_stack = []
        self.vars = {}
        self.funcs = OrderedDict()
        self.lists = []
        self.func_ = func_
    
    def compile(self):
        for i in self.ast:
            if not self.func_:
                self.out += f"{self.line}.\n"
            self.cur_node = self.ast[self.line-1]
            self._compile()
            self.line += 1

        if self.vars == {}:
            self.vars = {"a" : "1"}

        print(self.vars.items())
        if not self.func_:
            funcs = ""
            for i in self.funcs:
                funcs += f"{i}: {','.join(self.funcs[i].params)}\n{self.funcs[i].code}\nFUNC_END\n"
                funcs = funcs.replace("-1", str(len(self.consts)-1))
            self.out = ",".join([str(x) for x in self.consts]) + "\n" \
                + funcs + self.out
            if "-d" in sys.argv: breakpoint()
            return self.out
        else:
            return Func([str(x) for x in self.consts], self.vars, self.funcs, self.out)

    def _compile(self):
        #print(self.cur_node)
        if self.cur_node == None:
            return None
        
        if isinstance(self.cur_node, IdentNode):
            self.load_var()
        elif isinstance(self.cur_node, NumberNode):
            self.load_const()
        elif isinstance(self.cur_node, OpNode):
            self.op_node()
        elif isinstance(self.cur_node, Newline):
            self.cur_node = self.cur_node.next
            self._compile()

        elif isinstance(self.cur_node, CallNode):
            self.call()
        else: self.statement()

    def op_node(self):
        instr = "None"
        match self.cur_node.type:
            case "+":
                instr = "ADD"
            case "-":
                instr = "SUB"
            case "*":
                instr = "MUL"
            case "/":
                instr = "DIV"
            case "=":
                instr = "STORE"
                self.vars[self.cur_node.left.value] = "0"
            case ">":
                instr = "GT"
            case "<":
                instr = "LT"
            case "<=":
                instr = "LTEQ"
            case ">=":
                instr = "GTEQ"
            case "==":
                instr = "EQ"
            case "!=":
                instr = "NOTEQ"
        #self.free_reg += 1
        prev_node = self.cur_node
        if isinstance(self.cur_node.left, IdentNode) and instr == "STORE":
            regs = self.cur_node.left.value
        else:
            self.cur_node = prev_node.left
            self.expr()
        self.cur_node = prev_node.right
        self.expr()
        regs = ""
        if instr == "STORE":
            regs = f" {prev_node.left.value} {self.regs[-1]}"
            print("STORE")
        else:
            allocated_regs = self.reg_alloc(1)
            for i in range(2, -1, -1):
                regs += " " + str(allocated_regs[0] - i)
                
        self.out += instr + regs + "\n"
        self.instr += 1
        """match self.prev_node.type:
                case "+":
                self.out += "ADD\n"
        """

    def unary_op_node(self):
        #if "-d" in sys.argv: breakpoint()
        cur_node = self.cur_node
        self.cur_node = self.cur_node.value
        self.expr()
        match cur_node.type:
            case "-":
                allocated_reg = self.reg_alloc(1)[0]
                self.out += f"LOAD_CONST 0 {allocated_reg}\n"
                self.out += f"SUB {allocated_reg} {self.get_out_reg()} {allocated_reg}\n"
        
    def expr(self):
        """
        číslo, mat. výraz, volání funkce, (text)
        """
        if isinstance(self.cur_node, OpNode):
            self.op_node()
        elif isinstance(self.cur_node, UnaryOpNode):
            self.unary_op_node()
        elif isinstance(self.cur_node, NumberNode) or isinstance(self.cur_node, StringNode):
            self.load_const()
        elif isinstance(self.cur_node, IdentNode):
            self.load_var()
        elif isinstance(self.cur_node, CallNode):
            self.call()
        elif isinstance(self.cur_node, ListNode):
            self.list()
        elif isinstance(self.cur_node, IndexNode):
            self.index()

    def statement(self):
        if isinstance(self.cur_node, IfNode):
            self.cond()
        elif isinstance(self.cur_node, FuncNode):
            self.func()
        elif isinstance(self.cur_node, Newline):
            self.cur_node = self.cur_node.next
        elif isinstance(self.cur_node, ForNode | WhileNode):
            self.loop()
        elif isinstance(self.cur_node, ReturnNode):
            self.return_val()
        else:
            self.expr()

    def cond(self):
        if_node = self.cur_node
        self.cur_node = self.cur_node.expr
        self.expr()
        out = self.out
        self.out = ""
        if isinstance(if_node.block, ListNode):
            for self.cur_node in if_node.block:
                print(if_node.block, self.cur_node)
                self.statement()
        else:
            self.cur_node = if_node.block
            self.expr()
        #allocated_reg = self.reg_alloc(1)[0]
        lines = 0
        for i in out.split("\n"):
            if i[:-1].isnumeric():
                continue
            lines += 1
        self.out = f"{out}\nJUMP_IF_NOT {out[-2]} {len(self.out.split(chr(10))) + lines}\n{self.out}"
        self.cond_reg = out[-2]

    def loop(self):
        out = self.out
        lines = 0
        if isinstance(self.cur_node, ForNode):
            if self.cur_node.type == "for":
                for_node = self.cur_node
                self.cur_node = for_node.var
                self.op_node()
                self.cur_node = WhileNode(for_node.expr, for_node.block)
                self.cur_node.block.args.append(for_node.update)
                self.loop()
            else: # foreach
                pass
        elif isinstance(self.cur_node, WhileNode):
            for i in self.out.split("\n"):
                if i[:-1].isnumeric():
                    continue
                lines += 1
            self.cond()
            self.out += f"JUMP_IF {self.cond_reg} {lines - 1}\n"

    def list(self):
        list_node = self.cur_node
        size = len(list_node.args)
        start_addr = self.lowest_free_reg()
        self.out += f"MAKE_ARRAY {start_addr} {size}\n"
        self.lists.append(self.cur_node)
        for i in list_node.args:
            self.cur_node = i
            self.expr()

    def index(self):
        if "-d" in sys.argv: breakpoint()
        allocated_reg = self.reg_alloc(1)[0]
        cur_node = self.cur_node
        self.cur_node = self.cur_node.list
        self.expr()
        self.cur_node = cur_node.index
        self.expr()
        index = self.out.split("\n")[-2].split(" ")[-1]
        #if isinstance(self.cur_node, IdentNode):
            #index = self.vars[self.cur_node.value]
        self.out += f"GET_ELEMENT {self.vars[cur_node.list.value]} {index} {allocated_reg}\n"
        
    def load_const(self):
        allocated_reg = self.reg_alloc(1)[0]
        if not self.cur_node.value in self.consts:
            self.consts.append(self.cur_node.value)
            
        self.out += "LOAD_CONST " + str(self.consts.index(self.cur_node.value)) + " " + str(allocated_reg) + "\n"
        self.instr += 1

    def load_var(self):
        allocated_reg = self.reg_alloc(1)[0]
        if self.cur_node.value not in self.vars:
            raise SmSLError(f"{self.cur_node.value} is not defined.", self.line)
        
        self.out += "LOAD_VAR " + self.cur_node.value + " " + str(allocated_reg) + "\n"
        self.instr += 1

    def block(self, node):
        if "-d" in sys.argv: breakpoint()
        compiler = self.__class__(node.block.args, True)
        compiler.funcs = self.funcs
        compiler.vars = self.vars
        if isinstance(node, FuncNode):
            compiler.vars.update(dict.fromkeys(node.args.args, "0"))
        #if "-d" in sys.argv: breakpoint()
        code = compiler.compile()
        return code
        
    def call(self):
        print(self.funcs)
        call_node = self.cur_node
        regs = []
        allocated_reg = ""
        for i in self.cur_node.args.args:
            print(f"{self.cur_node = }")
            if i == None:
                continue
            self.cur_node = i
            self.expr()
            regs.append(self.out.split(' ')[-1].replace(chr(10), ''))
            print(f"{call_node.args.args=}, {i=}")
        allocated_reg = self.reg_alloc(1)[0]

        print(f"{self.out.split(' ')[-1]= }")
        if not regs:
            regs.append("198")
        self.out += f"CALL {self.funcs.index(call_node.func_name)} {allocated_reg} {' '.join(regs)}\n"

    def func(self):
        if "-d" in sys.argv: breakpoint()
        print("func")
        func_returns = False
        try:
            params = self.reg_alloc(len(self.cur_node.args.args))[0]
        except IndexError:
            params = None
        self.newline()
        print(f"{self.cur_node=} :)")
        func_node = self.cur_node
        self.cur_node = self.cur_node.block.args[0]
        self.newline()
        if isinstance(self.cur_node, StringNode) and self.cur_node.value.startswith("COMPILETO:\n"):
            code = self.cur_node.value.replace("COMPILETO:\n", "")
        else:
            code = self.block(func_node)
            self.consts.extend(code.consts)
            code = code.code
            print(f"{self.cur_node=}")

        code = code.split("\n")
        regs = len(code)
        for i in code:
            if i.startswith("consts:") or i.startswith("vars:"):
               regs -= 1
            if re.match(r"\s*RETURN", i):
                func_returns = True

        if not func_returns:
            code.append(f"LOAD_CONST 0 {regs+1}")
            code.append(f"RETURN {regs+1}")

        """memory = self.reg_alloc(regs)
        print(self.regs, memory)
        for i_ in range(len(code)):
            i = code[i_]
            if "consts:" in i or "vars:" in i:
                continue
            if i.endswith("."):
                continue
            i = i.split(" ")
            #if "-d" in sys.argv: breakpoint()
            for j in i:
                if j.isnumeric():
                    #if "-d" in sys.argv: breakpoint()
                    k = int(j) + memory[0]
                    i[i.index(j)] = str(k)
            code[i_] = " ".join(i)"""
        code = "\n".join(code) + "\n"
                    
        print("code:\n" + code)
        func = Function(func_node.name.value, func_node.args.args, code)
        self.funcs[func_node.name.value] = func
        #if "-d" in sys.argv: breakpoint()

    def return_val(self):
        self.cur_node = self.cur_node.expr
        self.expr()
        return_reg = self.get_out_reg()
        self.out += f"RETURN {return_reg}\n"


    def build_call(self, code, params):
        pass
    
    def newline(self):
        while isinstance(self.cur_node, Newline):
            self.cur_node = self.cur_node.next
        
    def assign(self):
        pass

    def get_out_reg(self):
        out = self.out.split("\n")
        out_reg = int(out[-2].split(" ")[-1])
        return out_reg
    
    def lowest_free_reg(self):
        for i in range(200):
            if i not in self.regs:
                return i
    
    def reg_alloc(self, regs):
        allocated_regs = []
        # free_reg = self.free_reg
        # for i in range(11):
        #     if i not in self.regs:
        #         free_reg = i
        #         break

        i = 0
        j = 0
        while i <= 200:
            if i not in self.regs:
                allocated_regs.append(i)
            i += 1
            if len(allocated_regs) == regs:
                break

        if not allocated_regs and regs != 0:
            raise ValueError("Out of memory!")

        self.regs += allocated_regs
        return allocated_regs
