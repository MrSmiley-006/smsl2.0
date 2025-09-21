import re
import sys

def assemble(asm, func=False, args=None):
    asm = asm.split("\nFUNC_END")
    asm[0] = asm[0].split("\n")
    if not func:
        consts = asm[0][0]
        del asm[0][0]
        print(f"{consts = }")
    asm[0] = "\n".join(asm[0])
    funcs = asm[:-1]
    asm = asm[-1]
    print(f"{funcs = }")
    bytecode = b""
    line = 0
    if not func:
        consts = consts.split(",")
        for i in consts:
            bytecode += i.encode()
            bytecode += b"\0" if i == consts[-1] else b"\1"
            print(i, i == consts[-1], consts[-1])
    if func:
        for i in args.split(","):
            print(i)
            if ":" in i:
                i = i.split(":")
                print(i)
                bytecode += i[0] + b"\2" + i[1]
                bytecode += b"\0" if ":".join(i) == args.split(",")[-1] else b"\1"
            else:
                bytecode += i.encode() + b"\0"
    for i in funcs:
        i_ = i
        if "-d" in sys.argv: breakpoint()
        match = re.match(r"\w+:\s?(\w+,?\s?)+\n", i)
        if match != None:
            i = i.replace(match.group(), "")
            args = match.group(1)
        func_bytecode = assemble(i, True, args) + b"\xFD"
        func_bytecode += b"\xFE" if i_ == funcs[-1] else b""
        print(f"{func_bytecode = }")
        """if "consts:" in i:
            for j in range(len(func_bytecode)):
                if func_bytecode[j] == b"\0":
                    func_bytecode = bytes(func_bytecode)
                    break
                del func_bytecode[j]"""
        if "-d" in sys.argv: breakpoint()
        bytecode += func_bytecode
    #if funcs:
    #    bytecode += b"\xFE"
    for i in asm.split("\n"):
        invalid_instruction = False
        """if re.match(r"\d+\.", i):
            line += 1
            bytecode += b"\3" + str(line)"""
        i = re.sub(r"^( + )|\t+", "", i)
        i = i.split(" ")
        #if not func: if "-d" in sys.argv: breakpoint()
        match i[0]:
            case "LOAD_CONST":
                bytecode += b"\4"
            case "LOAD_VAR":
                bytecode += b"\5"
            case "ADD":
                bytecode += b"\6"
            case "WRITE":
                bytecode += b"\x10"
            case "SUB":
                bytecode += b"\x11"
            case "READ":
                bytecode += b"\x12"
            case "CAST":
                bytecode += b"\x13"
            case "STORE":
                bytecode += b"\x14"
            case "JUMP":
                bytecode += b"\x15"
            case "GT":
                bytecode += b"\x16"
            case "GTEQ":
                bytecode += b"\x17"
            case "LT":
                bytecode += b"\x18"
            case "LTEQ":
                bytecode += b"\x19"
            case "EQ":
                bytecode += b"\x1A"
            case "NOTEQ":
                bytecode += b"\x1B"
            case "AND":
                bytecode += b"\x1C"
            case "NOT":
                bytecode += b"\x1D"
            case "JUMP_IF":
                bytecode += b"\x1E"
            case "LOG_NOT":
                bytecode += b"\x1F"
            case "JUMP_IF_NOT":
                bytecode += b"\x20"
            case "CALL":
                bytecode += b"\x21"
            case "RETURN":
                bytecode += b"\x22"
            case "JUMP":
                bytecode += b"\x23"
            case "MAKE_ARRAY":
                bytecode += b"\x24"
            case "GET_ELEMENT":
                bytecode += b"\x25"
            case "SET_ELEMENT":
                bytecode += b"\x26"
            case "GET_ARRAY_LENGTH":
                bytecode += b"\x27"
            case "FIND_ELEMENT":
                bytecode += b"\x28"
            case "SORT_ARRAY":
                bytecode += b"\x29"
            case "JOIN_STRING":
                bytecode += b"\x2A"
            case "INDEX_STRING":
                bytecode += b"\x2B"
            case _:
                invalid_instruction = True
        for j in i:
            if not invalid_instruction:
                if j == i[0]: continue
                bytecode += j.encode()
                bytecode += b"\1"
        if bytecode[-1] != 254:
            bytecode = bytecode[:-1] +  b"\0" # nahrazení znaku \1 na konci znakem \0

    #if "-d" in sys.argv: breakpoint()
    return bytecode

if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        code = f.read().replace("\x7f\x01", "")

    with open(sys.argv[1].replace(".smslasm", ".csmsl"), "wb") as f:
        f.write(assemble(code))
