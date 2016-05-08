from pycparser import parse_file, c_ast, c_generator
from cffi import *

def cEvalExpression(header_file, cpp_args = []):

    ignores = ['__attribute__(x)', '__extension__', '__inline', '__restrict']
    
    ast = parse_file(header_file, use_cpp = True, cpp_args = cpp_args+['-D'+i+'=' for i in ignores])
    generator = c_generator.CGenerator()

    ffi = FFI()
    lib = ffi.dlopen(None)

    unary_ops = {'+':lambda x:+x, '-':lambda x:-x}
    bin_ops = {'+':lambda x, y:x+y, '-':lambda x, y:x-y, '*':lambda x, y:x*y, '/':lambda x, y:x/y, '%':lambda x, y:x%y}

    def evalConst(exp):
        if exp.type=='int':
            return int(exp.value, 0)
        elif exp.type=='float':
            return float(exp.value)
        raise NotImplementedError()

    def makeConst(v):
        if isinstance(v, int):
            return c_ast.Constant('int', str(v))
        elif isinstance(v, float):
            return c_ast.Constant('float', str(v))
        raise NotImplementedError()

    def evalExpression(exp, enum_dict = {}):
        def _(exp):
            if isinstance(exp, c_ast.ID):
                if exp.name in enum_dict:
                    v = int(_(enum_dict[exp.name]).value)
                else:
                    v = getattr(lib, exp.name)
                    assert v
            elif isinstance(exp, c_ast.UnaryOp):
                if exp.op=='sizeof':
                    v = ffi.sizeof(generator.visit(exp.expr))
                else:
                    if not exp.op in unary_ops:
                        raise NotImplementedError()
                    v = unary_ops[exp.op](evalConst(_(exp.expr)))
            elif isinstance(exp, c_ast.BinaryOp):
                left, right = (evalConst(_(i)) for i in (exp.left, exp.right))
                if not exp.op in bin_ops:
                    raise NotImplementedError()
                v = bin_ops[exp.op](left, right)
            elif isinstance(exp, c_ast.Cast):
                #FIXME
                to_type = generator.visit(exp.to_type)
                if to_type!='int':
                    raise NotImplementedError()
                value = ffi.cast(to_type, evalConst(_(exp.expr)))
                v = int(value)
            else:
                return exp
            
            return makeConst(v)

        return _(exp)


    generator = c_generator.CGenerator()

    class Visitor(c_ast.NodeVisitor):
        def visit_ArrayDecl(self, node):
            for i, v in node.children():
                self.visit(v)

            if not isinstance(node.dim, c_ast.Constant):
                node.dim = evalExpression(node.dim)

        def visit_Enum(self, node):
            for i, v in node.children():
                self.visit(v)


            enums = node.values.enumerators

            enum_dict = {i.name:i.value for i in enums}
            for i in enums:
                if i.value:
                    if not isinstance(i.value, c_ast.Constant) and not isinstance(i.value, c_ast.ID):
                        i.value = evalExpression(i.value, enum_dict)

        def visit_Typedef(self, node):
            for i, v in node.children():
                self.visit(v)

        def visit_FileAST(self, node):
            new_ext = []
            for i in node.ext:
                self.visit(i)
                if not isinstance(i, c_ast.FuncDef):
                    if 'extern' in i.storage:
                        continue
                    ffi.cdef(generator.visit(i)+';')
                    new_ext += [i]
            node.ext = new_ext

    Visitor().visit(ast)

    return generator.visit(ast)

if __name__=='__main__':
    from sys import *

    if len(argv)<2:
        stderr.write("Usage: python %s header_file [cpp_args]..."%argv[0])
        exit(1)
    elif len(argv)==2:
        print (cEvalExpression(argv[1]))
        exit(0)
    else:
        print (cEvalExpression(argv[1], argv[2:]))
        exit(0)
    
    #processHeader()
