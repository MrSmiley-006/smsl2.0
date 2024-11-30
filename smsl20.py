import re, sys
import os
from parser import Parser
from compiler import Compiler
from assemble import assemble

def process_defines(code):
    replaces = {}
    for i in code.split("\n"):
        i = i.split(" ")
        if len(i) < 3: continue
        if i[0] == "#define":
            replaces[i[1]] = " " + i[2] + " "
        elif i[0] == "#undef":
            del replaces[i[1]]

    return replaces

def remove_strings(code):
    strings = re.findall(r"\"[^\"]+\"", code)
    i_ = 0
    for i in strings:
        code = code.replace(i, f"|{i_}|")
        i_ += 1

    return code, strings

def restore_strings(code, strings):
    for i in range(len(strings)):
        code = code.replace(f"|{i}|", strings[i])

    return code

def preprocess(code):
    code_ = code
    code = code.split("\n")
    replaces = {}
    for i in code:
        i = i.split(" ")
        if len(i) <= 1: continue
        if i[0] == "#include":
            #print(i)
            i[1] = i[1].replace('"', "")
            i[1] = re.sub(r":.*", "", i[1])
            if not i[1] in os.listdir():
                i[1] = os.path.join(os.environ["SMSL_STDLIB"], i[1])
            with open(i[1]) as f:
                file_contents = f.read()
            """if ":" in i[1]:
                namespace = re.sub(r".*:", "", i[1])
                regex = f"namespace {namespace} (.*)"
                nmspc = re.search(regex, file_contents)
                if nmspc != None: print("nmspc:" + nmspc.match())"""
            #print(file_contents)
            code_ = file_contents + code_

    code_, strings = remove_strings(code_)
    print(f"strings:{str(strings)}\n code:{code_}")
    replaces = process_defines(code_)
    for i, j in replaces.items():
        #print(i, j)
        code_ = re.sub(i, j, code_, 0)
            
    code_ = re.sub(r"#(define|undef|include).*\n", "", code_, 0)
    #print(replaces)
    return restore_strings(code_, strings), replaces

def isalpha(char):
    if char.isalpha() or char == "_":
        return True
    return False

def isalnum(char):
    if char.isalnum() or char == "_":
        return True
    return False

def isnumeric(char):
    if char.isnumeric() or char == ".":
        return True
    return False

def lex(code, replaces):
    i = 0
    string_mode = False
    ident_mode = False
    comment_mode = False
    number_mode = False
    cur_tok = {}
    tokens = []
    line = 1
    while i < len(code):
        #print(code[i])
        if code[i] == '"':
            cur_tok["type"] = "string"
            if string_mode:
                string_mode = False
                #cur_tok["value"] += code[i]
            else:
                string_mode = True
        elif isalpha(code[i]) and not ident_mode:
            cur_tok["type"] = "ident"
            ident_mode = True
            cur_tok["value"] = ""
        elif code[i].startswith("#"):
            comment_mode = True
            print("COMMENT")
        elif code[i].isnumeric() and not number_mode and not ident_mode:
            cur_tok["type"] = "number"
            number_mode = True
            cur_tok["value"] = ""
        elif code[i] in ["+", "-", "*", "/"]:
            cur_tok["type"] = "op"
            cur_tok["value"] = code[i]
            if code[i] == "*" and code[i+1] == "*" or code[i] == "/" and code[i+1] == "/" \
               or code[i] == "-" and code[i+1] == ">":
                cur_tok["value"] += code[i+1]
        elif code[i] == "\n" and not string_mode and not number_mode:
            cur_tok["type"] = "newline"
            cur_tok["value"] = code[i]
            line += 1
                
        if string_mode:
            try:
                cur_tok["value"] += code[i]
            except KeyError:
                cur_tok["value"] = code[i]
            i += 1
            continue
        elif comment_mode:
            if code[i] == "\n":
                comment_mode = False
            i += 1
            continue
        elif ident_mode:
            if isalnum(code[i]):
                cur_tok["value"] += code[i]
                i += 1
                continue
            else:
                ident_mode = False
                if cur_tok["value"] in ["if", "else", "for", "until", "while", "try", "using", "catch", "private", "func", "class", "extends", "return"]:
                    cur_tok["type"] = "keyword"
                elif " " + cur_tok["value"] + " " in replaces.values():
                    cur_tok["type"] = "special"
        elif number_mode:
            if isnumeric(code[i]):
                cur_tok["value"] += code[i]
                i += 1
                continue
            else:
                number_mode = False
        
        if cur_tok != {}:
            cur_tok["line"] = line
            tokens.append(cur_tok)
        cur_tok = {}
        i += 1

    for i in range(len(tokens)):
        if tokens[i]["type"] == "special":
            tokens[i]["value"] = {val:key for (key, val) in zip(replaces.keys(), replaces.values())}[" " + tokens[i]["value"] + " "] \
                .replace("\\", "")

    tokens.append({"type" : "EOF", "value" : "EOF"})

    return tokens

def xor(a, b):
    return (a and not b) or (not a and b)

def run():
    with open(sys.argv[1]) as f:
        code, replaces = preprocess(f.read())
    #print(code)
    print({val:key for (key, val) in zip(replaces.keys(), replaces.values())})
    tokens = lex(code, replaces)
    blocks = 0
    for i in range(len(tokens)):
        if tokens[i]["value"] == "(":
            blocks += 1
        elif tokens[i]["value"] == ")":
            blocks -= 1
        if tokens[i]["value"] == "\n" and blocks > 0:
            tokens[i] = {"type" : "newline", "value" : ";"}
    lines = []
    line = []
    for i in tokens:
        print(i)
        line.append(i)
        if i["value"] in ("\n", "EOF"):
            lines.append(line)
            line = []
    print(lines)
    parsed = []
    parser = Parser(lines[0])
    for i in lines:
        parser.tokens = i
        parser.counter = 0
        parsed.append(parser.parse())
    print("--------------\nParsed")
    indent_count = 0
    for i in str(parsed):
        if i == "(":
            indent_count += 1
            print(i + "\n" + ("    " * indent_count), end="")
        elif i == ")":
            indent_count -= 1
            print(i + "\n" + ("    " * indent_count), end="")
        else:
            print(i, end="")
    print("")
    asm = Compiler(parsed).compile()
    print(asm)
    if "-a" in sys.argv:
        out = asm
        ext = ".smslasm"
    else:
        out = assemble(asm)
        ext = ".csmsl"
    filename = sys.argv[1].split(".")
    with open(".".join(
            [x for x in filename if not (x == "smsl" and x == filename[-1])])
              + ext,
              "w" if "-a" in sys.argv else "wb") as f:
        f.write(out)

if __name__ == "__main__":
    run()
