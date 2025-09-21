import sys

class NumberNode:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return f"NumberNode({self.value})"

class IdentNode:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"IdentNode({self.value})"

class OpNode:
    def __init__(self, left, type, right):
        self.left = left
        self.type = type
        self.right = right

    def __repr__(self):
        return f"OpNode({self.left}, {self.type}, {self.right})"

class UnaryOpNode:
    def __init__(self, type, value):
        self.value = value
        self.type = type

    def __repr__(self):
        return f"UnaryOpNode({self.type}, {self.value})"
    
class CallNode:
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args
        
    def __repr__(self):
        return f"CallNode({self.func_name}, {self.args})"

class ListNode:
    def __init__(self, *args):
        self.args = [*args]

    def __repr__(self):
        return f"ListNode({self.args})"

    def __iter__(self):
        return iter(self.args)

class IndexNode:
    def __init__(self, list, index):
        self.list = list
        self.index = index

    def __repr__(self):
        return f"IndexNode({self.list}, {self.index})"

class StringNode:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"StringNode({self.value})"

class IfNode:
    def __init__(self, expr, block):
        self.expr = expr
        self.block = block

    def __repr__(self):
        return f"IfNode({self.expr}, {self.block})"

class ElseNode:
    def __init__(self, block):
        self.block = block

    def __repr__(self):
        return f"ElseNode({self.block})"

class ForNode:
    def __init__(self, var, expr, update, type, block):
        self.var = var
        self.expr = expr
        self.type = type
        self.block = block
        self.update = update

    def __repr__(self):
        return f"ForNode({self.var}, {self.expr}, {self.type}, {self.update}, {self.block})"

class WhileNode:
    def __init__(self, expr, block):
        self.expr = expr
        self.block = block

    def __repr__(self):
        return f"WhileNode({self.expr}, {self.block})"

class UntilNode:
    def __init__(self, expr, block):
        self.expr = expr
        self.block = block

    def __repr__(self):
        return f"UntilNode({self.expr}, {self.block})"

class FuncNode:
    def __init__(self, name, args, block):
        self.name = name
        self.args = args
        self.block = block

    def __repr__(self):
        return f"FuncNode({self.name}, {self.args}, {self.block})"

class EllipsisNode:
    def __repr__(self):
        return "EllipsisNode()"

class ClassNode:
    def __init__(self, name, extends, block):
        self.name = name
        self.extends = extends
        self.block = block

    def __repr__(self):
        return f"ClassNode({self.name}, {self.extends}, {self.block})"

class AttrNode:
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

    def __repr__(self):
        return f"AttrNode({self.obj}, {self.attr})"

class ReturnNode:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"ReturnNode({self.expr})"
        
class Newline:
    def __init__(self, next):
        self.next = next

    def __repr__(self):
        return f"Newline, {self.next}"
        
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.counter = 0
        self.cur_tok = {}

    def statement(self):
        result = self.logic_expr()
        if self.counter < len(self.tokens):
            if self.tokens[self.counter]["value"] in ("if", "while", "until"):
                if "-d" in sys.argv: breakpoint()
                tok = self.tokens[self.counter]
                self.counter += 1
                expr = self.logic_expr()
                print(self.tokens[self.counter])
                if self.tokens[self.counter]["value"] == "(":
                    self.counter += 1
                    if self.tokens[self.counter]["type"] != "newline":
                        block = self.statement()
                    else:
                        block = self.block()
                    if tok["value"] == "if":
                        result = IfNode(expr, block)
                    elif tok["value"] == "while":
                        result = WhileNode(expr, block)
                    elif tok["value"] == "until":
                        result = UntilNode(expr, block)
                else:
                    raise SyntaxError("Příkaz if musí následovat výraz a blok kódu.")
            elif self.tokens[self.counter]["value"] == "else":
                self.counter += 1
                if self.tokens[self.counter]["value"] == "if":
                    self.counter += 1
                    expr = self.expr()
                    if self.tokens[self.counter]["value"] == "(":
                        self.counter += 1
                        if self.tokens[self.counter]["type"] != "newline":
                            block = self.statement()
                        else:
                            block = self.block()
                        result = ElseNode(IfNode(expr, block))
                    else:
                        raise SyntaxError("Příkaz if musí následovat výraz a blok kódu.")
                elif self.tokens[self.counter]["value"] == "(":
                    self.counter += 1
                    if self.tokens[self.counter]["type"] != "newline":
                        block = self.statement()
                    else:
                        block = self.block()
                    result = ElseNode(block)
                        
            elif self.tokens[self.counter]["value"] == "for":
                if "-d" in sys.argv: breakpoint()
                self.counter += 1
                var = IdentNode(self.tokens[self.counter]["value"])
                self.counter += 2
                var = OpNode(var, "=", self.logic_expr())
                if self.tokens[self.counter]["value"] == ",":
                    self.counter += 1
                    expr = self.logic_expr()
                    type = "for"
                elif self.tokens[self.counter]["value"] == "in":
                    self.counter += 1
                    expr = self.expr()
                    if isinstance(expr, IdentNode) or isinstance(expr, CallNode) \
                       or isinstance(expr, ListNode):
                        type = "foreach"
                    else:
                        raise SyntaxError("Za klíčovým slovem in musí být iterovatelný výraz.")
                if type == "for":
                    if self.tokens[self.counter]["value"] == ",":
                        self.counter += 1
                        update = IdentNode(self.tokens[self.counter]["value"])
                        self.counter += 2
                        update = OpNode(update, "=", self.logic_expr())
                if self.tokens[self.counter]["value"] == "(":
                    self.counter += 1
                    if self.tokens[self.counter]["type"] != "newline":
                        block = self.statement()
                    else:
                        block = self.block()
                    result = ForNode(var, expr, update, type, block)
            
            elif self.tokens[self.counter]["value"] == "func":
                result = self.func()
            elif self.tokens[self.counter]["value"] == "class":
                self.counter += 1
                name = IdentNode(self.tokens[self.counter]["value"])
                self.counter += 1
                extends = None
                if self.tokens[self.counter]["value"] == "extends":
                    self.counter += 1
                    extends = self.tokens[self.counter]["value"]
                    self.counter += 1
                if self.tokens[self.counter]["value"] == "(":
                    self.counter += 1
                    if self.tokens[self.counter]["type"] == "newline":
                        block = ListNode()
                        while self.counter < len(self.tokens):
                            if self.tokens[self.counter]["value"] == "func":
                                block.args.append(self.func())
                            elif self.tokens[self.counter]["type"] == "newline":
                                self.counter += 1
                            else:
                                break
                    else:
                        block = self.statement()
                result = ClassNode(name, extends, block)
            #elif self.tokens[self.counter]["type"] == "ident" and self.tokens[self.counter+1]["value"] == "=":
                #self.counter += 2
                
        return result
    
    def block(self):
        self.counter += 1
        result = ListNode()
        while self.counter < len(self.tokens):
            if self.cur_tok["value"] == "return":
                result.args.append(self.func_return())
            else:
                result.args.append(self.statement())
            if self.counter >= len(self.tokens):
                break
            if self.tokens[self.counter]["value"] == ";":
                self.counter += 1
            if self.tokens[self.counter]["value"] == ")":
                break
        print(f"result:{result}")
        return result

    def list(self):
        self.counter += 1
        result = ListNode()
        while self.counter < len(self.tokens):
            result.args.append(self.expr())
            if self.tokens[self.counter]["value"] == "}":
                return result
            if self.tokens[self.counter]["value"] == ",":
                self.counter += 1
            else:
                raise SyntaxError("Prvky seznamu musí být odděleny čárkami.")

    def func(self):
       self.counter += 1
       print(self.counter, len(self.tokens))
       name = IdentNode(self.tokens[self.counter]["value"])
       print(name)
       self.counter += 1
       args = ListNode()
       print(f"token:{self.tokens[self.counter]}")
       if self.tokens[self.counter]["value"] == "[":
           self.counter += 1
           while self.counter < len(self.tokens):
               if self.tokens[self.counter]["value"] == ",":
                   self.counter += 1
               elif self.tokens[self.counter]["value"] == "]":
                   self.counter += 1
                   
               else:
                   args.args.append(self.tokens[self.counter]["value"])
                   self.counter += 1
       if self.counter < len(self.tokens):
           while self.tokens[self.counter]["type"] == "newline":
               self.counter += 1
           print(f"token:{self.tokens[self.counter]}")
           if self.tokens[self.counter]["value"] == "(":
               block = self.block()
               if self.counter < len(self.tokens) and self.tokens[self.counter]["value"] == ")":
                   self.counter += 1
           result = FuncNode(name, args, block)
           return result

    def func_return(self):
        if self.tokens[self.counter]["value"] == "return":
            self.counter += 1

        result = ReturnNode(self.logic_expr())
        
        return result

    def logic_expr(self):
        result = self.rel_expr()
        while self.counter < len(self.tokens):
            if self.tokens[self.counter]["value"] in ("and", "or", "not", "xor"):
                self.counter += 1
                result = OpNode(result, self.tokens[self.counter-1]["value"], self.rel_expr())
            else:
                break
        return result

    def rel_expr(self):
        result = self.expr()
        #self.counter += 1 #
        while self.counter < len(self.tokens):
            self.cur_tok = self.tokens[self.counter]
            if self.cur_tok["value"] in (">", "<", ">=", "<=", "==", "!="):
                self.counter += 1
                result = OpNode(result, self.cur_tok["value"], self.logic_expr())
            else:
                break

        return result
    
    def expr(self):
        result = self.mul_div()
        while self.counter < len(self.tokens):
            self.cur_tok = self.tokens[self.counter]
            if self.cur_tok["value"] in ("+", "-"):
               self.counter += 1
               result = OpNode(result, self.cur_tok["value"], self.mul_div())
            elif self.cur_tok["value"] == "{":
                result = self.list()
                if  self.tokens[self.counter]["value"] != "}":
                    raise SyntaxError("Neukončený seznam")
            else:
                break#raise SyntaxError(f"factor, {self.cur_tok['value']} {self.tokens[self.counter+1]['value']}")
        
        return result

    def mul_div(self):
        result = self.factor()
        while self.counter < len(self.tokens):
            self.cur_tok = self.tokens[self.counter]
            if self.cur_tok["value"] in ("*", "/"):
                self.counter += 1
                result = OpNode(result, self.cur_tok["value"], self.factor())
            else:
                break#raise SyntaxError(f"term, {self.cur_tok['value']} {self.tokens[self.counter+1]['value']}")
        return result

    def factor(self):
        if self.counter >= len(self.tokens):
            return None
        tok = self.tokens[self.counter]
        if self.counter < len(self.tokens)-1:
            if self.tokens[self.counter+1]["value"] == "@":
                self.counter += 1
                return self.index()
        #print(f"tok: {tok}")
        if tok["type"] == "newline":
            self.counter += 1
            return Newline(self.statement())
        if tok["value"] == "-":
            self.counter += 1
            if self.tokens[self.counter]["value"] == "-":
                self.counter += 1
                return UnaryOpNode("--", self.factor())
            return UnaryOpNode("-", self.factor())
        if tok["value"] == "+":
            self.counter += 1
            if self.tokens[self.counter]["value"] == "+":
                self.counter += 1
                return UnaryOpNode("++", self.factor())
        if tok["type"] in ("number", "ident"):
            #if "-d" in sys.argv: breakpoint()
            result = self.ident()
            self.counter += 1
            if self.tokens[self.counter]["value"] == "->":
                self.counter += 1
                result = AttrNode(IdentNode(tok["value"]), IdentNode(self.tokens[self.counter]["value"]))
            if tok["type"] == "ident":
                ident = tok
                if self.tokens[self.counter]["value"] == "=":
                    self.counter += 1
                    result = self.assign()
                elif self.tokens[self.counter]["value"] == "[":
                    self.counter += 1
                    result = self.call()
            return result
        elif tok["value"] == "(":
            self.counter += 1
            result = self.tokens[self.counter]["value"]
            return self.logic_expr()
            """while self.counter < len(self.tokens):
                if self.tokens[self.counter] != ")":
                    result = OpNode(result, "expr", self.plus_minus())
                    self.counter += 1
                else:
                    break
            return result"""
        elif tok["type"] == "string":
            self.counter += 1
            return StringNode(tok["value"])

    def index(self):
        self.counter -= 1
        list = IdentNode(self.tokens[self.counter]["value"])
        self.counter += 2
        if "-d" in sys.argv: breakpoint()
        return IndexNode(list, self.expr())

    def ident(self):
        #if "-d" in sys.argv: breakpoint()
        if self.counter < len(self.tokens):
            result = NumberNode(self.tokens[self.counter]["value"]) if self.tokens[self.counter]["type"] == "number" else IdentNode(self.tokens[self.counter]["value"])
            return result
    
    def assign(self):
        if self.tokens[self.counter-3]["value"] == "private":
            type = "p="
        else:
            type = "="
        result = OpNode(IdentNode(self.tokens[self.counter-2]["value"]), type, self.logic_expr())
        if self.tokens[self.counter-3]["value"] == "->":
            result.left = AttrNode(self.tokens[self.counter-4]["value"], result.left)
        return result

    def _assign(self):
        if self.counter < len(self.tokens):
            ident = IdentNode(self.tokens[self.counter]["value"])
            self.counter += 1
            if self.tokens[self.counter]["value"] == "->":
                self.counter += 1
                ident = AttrNode(ident, self.tokens[self.counter])
                self.counter += 1
            if self.tokens[self.counter]["value"] == "=":
                result = OpNode(ident, "=", self.logic_expr())
            else:
                result = ident
        return result

    def call(self):
        func = self.tokens[self.counter-2]["value"]
        #self.counter += 1
        args = ListNode()#self.tokens[self.counter]["value"])
        while self.counter < len(self.tokens):
            if self.tokens[self.counter]["value"] not in ("]", "\n", ";"):
                print(f"call:{self.tokens[self.counter]}")
                args.args.append(self.expr())
                self.counter += 1
            else:
                break
       
        return CallNode(func, args)

    def parse(self):
        return self.statement()
