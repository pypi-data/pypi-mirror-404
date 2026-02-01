import ast
import operator
import inspect
from typing import Dict, List, Tuple, Optional, Any, Set


class LazyASTParser:
    def __init__(self):
        self.hot_nodes = []  # 格式：[(节点类型, 节点名称/标识), ...]
        self.current_func = None  # 记录当前解析的函数名
        self.import_records = {}  # key=模块名，value=别名（无别名则为模块名）
        self.optimizer = ASTOptimizer(self)  # 内置O3级优化器实例

    def _visit_loop(self, node):
        """识别循环节点，标记为hot_nodes"""
        loop_id = f"loop_line_{node.lineno}"
        self.hot_nodes.append(('loop', loop_id))
        self.visit(node.body)

    def _visit_func_def(self, node):
        """识别函数节点，标记为hot_nodes"""
        self.current_func = node.name
        self.hot_nodes.append(('func', self.current_func))
        self.visit(node.body)
        self.current_func = None

    def _visit_import(self, node):
        """识别import语句，记录模块名+别名（字典形式）"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            alias_name = alias.asname if alias.asname else module_name
            self.import_records[module_name] = alias_name

    def _visit_import_from(self, node):
        """识别from ... import ...语句，记录模块名"""
        if node.module:
            module_name = node.module.split('.')[0]
            self.import_records[module_name] = module_name

    def visit(self, node):
        """递归遍历AST节点（鲁棒版）"""
        if isinstance(node, (str, int, float, bool, bytes, type(None))):
            return
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return
        if not hasattr(node, '_fields'):
            return

        # 核心节点识别
        if isinstance(node, ast.FunctionDef):
            self._visit_func_def(node)
        elif isinstance(node, (ast.For, ast.While)):
            self._visit_loop(node)
        elif isinstance(node, ast.Import):
            self._visit_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._visit_import_from(node)
        # 递归处理其他节点字段
        else:
            for field, value in ast.iter_fields(node):
                self.visit(value)

    def parse(self, source, filename="unknown.py", optimize: bool = True,
              optimize_level: str = "O3", optimize_strategies: List[str] = None) -> ast.AST:
        """
        解析源码（默认O3级全作弊优化），完全兼容原API
        Args:
            source: 源代码字符串
            filename: 文件名
            optimize: 是否启用优化（默认True）
            optimize_level: 优化级别（O0/O1/O2/O3），优先级高于custom_strategies
                            O0: 无优化 | O1: 仅常量折叠
                            O2: 常量+位运算+循环展开+尾递归 | O3: O2+类型推断+静态分析+死代码消除
            optimize_strategies: 自定义优化策略列表（仅optimize_level=None时生效）
        Returns:
            优化后的AST树（默认O3）/原始AST树
        """
        # 清空历史数据，保持原逻辑
        self.hot_nodes = []
        self.import_records = {}
        # 原始AST解析
        ast_tree = ast.parse(source, filename=filename)
        self.visit(ast_tree)
        
        # 【核心】默认O3级全作弊优化
        if optimize:
            ast_tree = self.optimizer.optimize(ast_tree, optimize_level, optimize_strategies)
        
        return ast_tree


class TypeInfo:
    """类型信息记录：用于静态分析的变量类型/取值范围"""
    def __init__(self):
        self.type: Optional[type] = None  # 推断的类型（int/float/str等）
        self.min_val: Optional[Any] = None  # 最小值
        self.max_val: Optional[Any] = None  # 最大值
        self.is_const: bool = False  # 是否为常量
        self.value: Optional[Any] = None  # 常量值

    def __repr__(self):
        return f"TypeInfo(type={self.type.__name__ if self.type else 'None'}, min={self.min_val}, max={self.max_val}, const={self.is_const}, value={self.value})"


class ASTOptimizer:
    """O3级终极作弊优化器：O2 + 类型推断 + 静态分析 + 死代码消除"""
    def __init__(self, parser: LazyASTParser):
        self.parser = parser
        # 运算符映射（常量折叠用）
        self.bin_op_map = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.BitAnd: operator.and_,
            ast.BitOr: operator.or_,
            ast.LShift: operator.lshift,
            ast.RShift: operator.rshift
        }
        self.unary_op_map = {
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Not: operator.not_,
            ast.Invert: operator.invert
        }
        # 优化配置
        self.processed_funcs = set()  # 避免递归函数重复处理
        self.DEFAULT_UNROLL_COUNT = 2  # 默认循环展开次数
        self.MAX_UNROLL_COUNT = 10      # 最大展开次数
        # 类型分析上下文
        self.type_context: Dict[str, TypeInfo] = {}  # 变量名 -> 类型信息

    def optimize(self, ast_tree: ast.AST, optimize_level: str = "O3", custom_strategies: List[str] = None) -> ast.AST:
        """
        执行指定级别优化
        O0: []
        O1: ['constant_folding']
        O2: ['constant_folding', 'arithmetic_to_bitwise', 'loop_unrolling', 'recursion_to_iteration']
        O3: O2 + ['type_inference', 'dead_code_elimination', 'range_optimization', 'short_circuit_optimization']
        """
        # 定义各级别策略
        level_strategies = {
            "O0": [],
            "O1": ['constant_folding'],
            "O2": ['constant_folding', 'arithmetic_to_bitwise', 'loop_unrolling', 'recursion_to_iteration'],
            "O3": ['constant_folding', 'arithmetic_to_bitwise', 'loop_unrolling', 'recursion_to_iteration',
                   'type_inference', 'dead_code_elimination', 'range_optimization', 'short_circuit_optimization']
        }
        # 确定最终策略
        if optimize_level in level_strategies:
            strategies = level_strategies[optimize_level]
        else:
            strategies = custom_strategies or level_strategies["O3"]

        # 按依赖顺序执行优化
        # 1. 先做类型推断（为后续优化提供基础）
        if 'type_inference' in strategies:
            self.type_context.clear()
            ast_tree = self._type_inference(ast_tree)
        # 2. 常量折叠（基础）
        if 'constant_folding' in strategies:
            ast_tree = self._constant_folding(ast_tree)
        # 3. 四则运算变位运算
        if 'arithmetic_to_bitwise' in strategies:
            ast_tree = self._arithmetic_to_bitwise(ast_tree)
        # 4. 取值范围优化
        if 'range_optimization' in strategies:
            ast_tree = self._range_optimization(ast_tree)
        # 5. 循环展开
        if 'loop_unrolling' in strategies:
            ast_tree = self._loop_unrolling(ast_tree)
        # 6. 尾递归转迭代
        if 'recursion_to_iteration' in strategies:
            self.processed_funcs.clear()
            ast_tree = self._recursion_to_iteration(ast_tree)
        # 7. 短路表达式优化
        if 'short_circuit_optimization' in strategies:
            ast_tree = self._short_circuit_optimization(ast_tree)
        # 8. 死代码消除（最后执行，依赖前面的分析）
        if 'dead_code_elimination' in strategies:
            ast_tree = self._dead_code_elimination(ast_tree)

        # 修复AST节点位置信息
        ast.fix_missing_locations(ast_tree)
        ast.increment_lineno(ast_tree, 0)
        return ast_tree

    # ====================== 原有O2级优化（略作适配） ======================
    def _constant_folding(self, node: ast.AST) -> ast.AST:
        """常量折叠（适配类型推断上下文）"""
        class ConstantFoldingVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
                node.left = self.visit(node.left)
                node.right = self.visit(node.right)
                # 原有常量折叠逻辑
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                    try:
                        op_func = self.parent.bin_op_map.get(type(node.op))
                        if op_func:
                            result = op_func(node.left.value, node.right.value)
                            return ast.Constant(value=result, lineno=node.lineno, col_offset=node.col_offset)
                    except (ZeroDivisionError, OverflowError, TypeError):
                        pass
                # 新增：基于类型推断的常量折叠（比如已知n是int且n=5，直接替换）
                elif isinstance(node.left, ast.Name) and node.left.id in self.parent.type_context:
                    left_info = self.parent.type_context[node.left.id]
                    if left_info.is_const and isinstance(node.right, ast.Constant):
                        try:
                            op_func = self.parent.bin_op_map.get(type(node.op))
                            if op_func:
                                result = op_func(left_info.value, node.right.value)
                                return ast.Constant(value=result, lineno=node.lineno, col_offset=node.col_offset)
                        except:
                            pass
                elif isinstance(node.right, ast.Name) and node.right.id in self.parent.type_context:
                    right_info = self.parent.type_context[node.right.id]
                    if right_info.is_const and isinstance(node.left, ast.Constant):
                        try:
                            op_func = self.parent.bin_op_map.get(type(node.op))
                            if op_func:
                                result = op_func(node.left.value, right_info.value)
                                return ast.Constant(value=result, lineno=node.lineno, col_offset=node.col_offset)
                        except:
                            pass
                return node

            def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
                node.operand = self.visit(node.operand)
                if isinstance(node.operand, ast.Constant):
                    try:
                        op_func = self.parent.unary_op_map.get(type(node.op))
                        if op_func:
                            result = op_func(node.operand.value)
                            return ast.Constant(value=result, lineno=node.lineno, col_offset=node.col_offset)
                    except TypeError:
                        pass
                return node

            def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
                values = [self.visit(v) for v in node.values]
                all_const = all(isinstance(v, ast.Constant) for v in values)
                if all_const:
                    try:
                        if isinstance(node.op, ast.And):
                            result = all(v.value for v in values)
                        elif isinstance(node.op, ast.Or):
                            result = any(v.value for v in values)
                        else:
                            return ast.BoolOp(op=node.op, values=values)
                        return ast.Constant(value=result, lineno=node.lineno, col_offset=node.col_offset)
                    except TypeError:
                        pass
                return ast.BoolOp(op=node.op, values=values)

        visitor = ConstantFoldingVisitor(self)
        return visitor.visit(node)

    def _arithmetic_to_bitwise(self, node: ast.AST) -> ast.AST:
        """四则运算变位运算（基于类型推断，只对int类型优化）"""
        class BitwiseOptimizer(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
                node = self.generic_visit(node)
                
                # 先判断类型是否为int（基于类型推断）
                left_is_int = False
                right_is_int = False
                if isinstance(node.left, ast.Name) and node.left.id in self.parent.type_context:
                    left_is_int = self.parent.type_context[node.left.id].type == int
                elif isinstance(node.left, ast.Constant):
                    left_is_int = isinstance(node.left.value, int)
                
                if isinstance(node.right, ast.Name) and node.right.id in self.parent.type_context:
                    right_is_int = self.parent.type_context[node.right.id].type == int
                elif isinstance(node.right, ast.Constant):
                    right_is_int = isinstance(node.right.value, int)
                
                # 仅对int类型做位运算优化
                if not (left_is_int and right_is_int):
                    return node

                # 1. 乘法 → 左移
                if (isinstance(node.op, ast.Mult) and
                    isinstance(node.right, ast.Constant) and
                    isinstance(node.right.value, int) and
                    node.right.value > 1 and
                    (node.right.value & (node.right.value - 1)) == 0):
                    shift = node.right.value.bit_length() - 1
                    return ast.BinOp(
                        left=node.left, op=ast.LShift(),
                        right=ast.Constant(value=shift),
                        lineno=node.lineno, col_offset=node.col_offset
                    )
                # 2. 整数地板除 → 右移
                if (isinstance(node.op, ast.FloorDiv) and
                    isinstance(node.right, ast.Constant) and
                    isinstance(node.right.value, int) and
                    node.right.value > 1 and
                    (node.right.value & (node.right.value - 1)) == 0):
                    shift = node.right.value.bit_length() - 1
                    return ast.BinOp(
                        left=node.left, op=ast.RShift(),
                        right=ast.Constant(value=shift),
                        lineno=node.lineno, col_offset=node.col_offset
                    )
                # 3. 取模2 → 按位与1
                if (isinstance(node.op, ast.Mod) and
                    isinstance(node.right, ast.Constant) and
                    node.right.value == 2):
                    return ast.BinOp(
                        left=node.left, op=ast.BitAnd(),
                        right=ast.Constant(value=1),
                        lineno=node.lineno, col_offset=node.col_offset
                    )
                # 4. 相同值相减 → 常量0
                if (isinstance(node.op, ast.Sub) and
                    ast.dump(node.left) == ast.dump(node.right)):
                    return ast.Constant(value=0, lineno=node.lineno, col_offset=node.col_offset)
                return node

        visitor = BitwiseOptimizer(self)
        return visitor.visit(node)

    def _loop_unrolling(self, node: ast.AST) -> ast.AST:
        """循环展开（基于类型推断优化展开逻辑）"""
        class LoopUnrollingVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def _get_fixed_loop_count(self, iter_node: ast.Call) -> Optional[int]:
                """解析range调用，返回固定循环次数"""
                if not (isinstance(iter_node, ast.Call) and
                        isinstance(iter_node.func, ast.Name) and
                        iter_node.func.id == 'range'):
                    return None
                args = iter_node.args
                # 处理基于类型推断的变量（比如已知n是int且n=5，range(n) → 5次）
                for i, arg in enumerate(args):
                    if isinstance(arg, ast.Name) and arg.id in self.parent.type_context:
                        arg_info = self.parent.type_context[arg.id]
                        if arg_info.is_const and isinstance(arg_info.value, int):
                            args[i] = ast.Constant(value=arg_info.value)
                
                # range(N)
                if len(args) == 1 and isinstance(args[0], ast.Constant) and isinstance(args[0].value, int):
                    return abs(args[0].value)
                # range(0, N)
                if len(args) == 2 and all(isinstance(a, ast.Constant) and isinstance(a.value, int) for a in args):
                    start, end = args[0].value, args[1].value
                    return abs(end - start) if (end - start) != 0 else None
                # range(N, 0, -1)
                if len(args) == 3 and all(isinstance(a, ast.Constant) and isinstance(a.value, int) for a in args):
                    start, end, step = args[0].value, args[1].value, args[2].value
                    if step == -1 and end == 0 and start > 0:
                        return start
                return None

            def _replace_loop_var(self, stmt: ast.AST, var_name: str, value: int) -> ast.AST:
                """替换循环体内的变量为常量值"""
                class VarReplacer(ast.NodeTransformer):
                    def visit_Name(self, node: ast.Name) -> ast.AST:
                        if node.id == var_name and node.ctx == ast.Load():
                            return ast.Constant(value=value, lineno=node.lineno, col_offset=node.col_offset)
                        return node
                return VarReplacer().visit(stmt)

            def visit_For(self, node: ast.For) -> ast.AST:
                if not isinstance(node.target, ast.Name):
                    return node
                loop_var = node.target.id
                loop_count = self._get_fixed_loop_count(node.iter)
                if loop_count is None or loop_count <= 1 or loop_count > self.parent.MAX_UNROLL_COUNT:
                    return node
                # 展开循环体
                unrolled_body = []
                for i in range(loop_count):
                    for stmt in node.body:
                        new_stmt = ast.copy_location(ast.parse(ast.unparse(stmt)).body[0], stmt)
                        new_stmt = self._replace_loop_var(new_stmt, loop_var, i)
                        unrolled_body.append(new_stmt)
                if node.orelse:
                    unrolled_body.extend(node.orelse)
                return unrolled_body

            def visit_While(self, node: ast.While) -> ast.AST:
                # 基于类型推断优化While循环展开
                if (isinstance(node.test, ast.Compare) and
                    isinstance(node.test.left, ast.Name) and
                    node.test.left.id in self.parent.type_context and
                    self.parent.type_context[node.test.left.id].type == int and
                    isinstance(node.test.ops[0], ast.Lt) and
                    isinstance(node.test.comparators[0], (ast.Constant, ast.Name))):
                    
                    loop_var = node.test.left.id
                    max_val_node = node.test.comparators[0]
                    max_val = None
                    
                    # 处理常量最大值
                    if isinstance(max_val_node, ast.Constant) and isinstance(max_val_node.value, int):
                        max_val = max_val_node.value
                    # 处理类型推断后的变量最大值
                    elif isinstance(max_val_node, ast.Name) and max_val_node.id in self.parent.type_context:
                        max_val_info = self.parent.type_context[max_val_node.id]
                        if max_val_info.is_const and isinstance(max_val_info.value, int):
                            max_val = max_val_info.value
                    
                    if max_val is not None:
                        # 检查循环体是否只有i+=1
                        has_inc = False
                        for stmt in node.body:
                            if (isinstance(stmt, ast.Assign) and
                                isinstance(stmt.targets[0], ast.Name) and
                                stmt.targets[0].id == loop_var and
                                isinstance(stmt.value, ast.BinOp) and
                                isinstance(stmt.value.left, ast.Name) and
                                stmt.value.left.id == loop_var and
                                isinstance(stmt.value.op, ast.Add) and
                                (isinstance(stmt.value.right, ast.Constant) and stmt.value.right.value == 1 or
                                 (isinstance(stmt.value.right, ast.Name) and 
                                  stmt.value.right.id in self.parent.type_context and
                                  self.parent.type_context[stmt.value.right.id].is_const and
                                  self.parent.type_context[stmt.value.right.id].value == 1))):
                                has_inc = True
                        
                        if has_inc and 1 < max_val <= self.parent.MAX_UNROLL_COUNT:
                            unrolled_body = []
                            for i in range(max_val):
                                for stmt in node.body:
                                    if not (isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == loop_var):
                                        new_stmt = ast.copy_location(ast.parse(ast.unparse(stmt)).body[0], stmt)
                                        new_stmt = self._replace_loop_var(new_stmt, loop_var, i)
                                        unrolled_body.append(new_stmt)
                            return unrolled_body
                return node

        visitor = LoopUnrollingVisitor(self)
        return visitor.visit(node)

    def _recursion_to_iteration(self, node: ast.AST) -> ast.AST:
        """尾递归转迭代（适配类型推断）"""
        class RecursionToIterationVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def _is_tail_recursion(self, return_node: ast.Return, func_name: str) -> Optional[ast.Call]:
                """判断是否是尾递归调用"""
                if not isinstance(return_node.value, ast.Call):
                    return None
                call_node = return_node.value
                if (isinstance(call_node.func, ast.Name) and
                    call_node.func.id == func_name and
                    len(call_node.args) > 0):
                    return call_node
                return None

            def _gen_param_assign(self, func_name: str, call_node: ast.Call, func_args: ast.arguments) -> List[ast.AST]:
                """生成尾递归调用的参数赋值语句"""
                assign_stmts = []
                for arg, call_arg in zip(func_args.args, call_node.args):
                    arg_name = arg.arg
                    # 基于类型推断优化赋值（常量直接替换）
                    if isinstance(call_arg, ast.Name) and call_arg.id in self.parent.type_context:
                        arg_info = self.parent.type_context[call_arg.id]
                        if arg_info.is_const:
                            call_arg = ast.Constant(value=arg_info.value, lineno=call_node.lineno)
                    
                    assign = ast.Assign(
                        targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                        value=call_arg,
                        lineno=call_node.lineno
                    )
                    assign_stmts.append(assign)
                return assign_stmts

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                if node.name in self.parent.processed_funcs:
                    return node
                self.parent.processed_funcs.add(node.name)
                node = self.generic_visit(node)

                # 查找尾递归返回节点
                tail_recur_call = None
                return_node_idx = -1
                for idx, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return):
                        tail_recur_call = self._is_tail_recursion(stmt, node.name)
                        if tail_recur_call:
                            return_node_idx = idx
                            break
                if tail_recur_call is None or return_node_idx == -1:
                    return node

                # 尾递归转While循环
                pre_body = node.body[:return_node_idx]
                loop_test = ast.Constant(value=True, lineno=node.lineno)
                if pre_body and isinstance(pre_body[-1], ast.If):
                    if_node = pre_body[-1]
                    loop_test = if_node.test
                    pre_body[-1] = ast.If(
                        test=if_node.test,
                        body=if_node.body,
                        orelse=[],
                        lineno=if_node.lineno
                    )
                param_assign = self._gen_param_assign(node.name, tail_recur_call, node.args)
                loop_body = pre_body + param_assign
                while_loop = ast.While(
                    test=loop_test,
                    body=loop_body,
                    orelse=[],
                    lineno=node.lineno
                )
                node.body = [while_loop]
                return node

        visitor = RecursionToIterationVisitor(self)
        return visitor.visit(node)

    # ====================== 新增O3级作弊优化 ======================
    def _type_inference(self, node: ast.AST) -> ast.AST:
        """
        终极作弊：类型推断（哪怕没有常量也能精准推断）
        支持：
        1. input类型推断：n = int(input()) → n的类型是int
        2. 赋值类型推断：s = "hello" → s的类型是str
        3. 运算类型推断：a = b + c（已知b=int,c=int → a=int）
        4. 条件类型推断：if n > 0 → n的min_val=1
        """
        class TypeInferenceVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent
                self.current_scope: Set[str] = set()  # 当前作用域的变量

            def _infer_call_type(self, node: ast.Call) -> Optional[type]:
                """推断函数调用的返回类型"""
                # 处理input相关调用
                if (isinstance(node.func, ast.Name) and node.func.id == 'input'):
                    return str
                # 处理int(input())/float(input())等
                elif (isinstance(node.func, ast.Name) and node.func.id in ['int', 'float', 'str', 'bool'] and
                      len(node.args) == 1 and isinstance(node.args[0], ast.Call) and
                      isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == 'input'):
                    return eval(node.func.id)  # 返回对应的类型（int/float等）
                # 可扩展：处理其他常见函数的返回类型
                return None

            def _update_var_type(self, var_name: str, type_info: TypeInfo):
                """更新变量的类型信息"""
                if var_name not in self.parent.type_context:
                    self.parent.type_context[var_name] = TypeInfo()
                ctx_info = self.parent.type_context[var_name]
                ctx_info.type = type_info.type or ctx_info.type
                ctx_info.min_val = type_info.min_val if type_info.min_val is not None else ctx_info.min_val
                ctx_info.max_val = type_info.max_val if type_info.max_val is not None else ctx_info.max_val
                ctx_info.is_const = type_info.is_const or ctx_info.is_const
                ctx_info.value = type_info.value if type_info.value is not None else ctx_info.value

            def visit_Assign(self, node: ast.Assign) -> ast.AST:
                """处理赋值语句的类型推断"""
                node = self.generic_visit(node)
                # 仅处理单变量赋值
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id
                    type_info = TypeInfo()
                    
                    # 1. 常量赋值：n = 5 → const=True, type=int, value=5
                    if isinstance(node.value, ast.Constant):
                        type_info.type = type(node.value.value)
                        type_info.is_const = True
                        type_info.value = node.value.value
                        type_info.min_val = node.value.value
                        type_info.max_val = node.value.value
                    
                    # 2. 函数调用赋值：n = int(input()) → type=int
                    elif isinstance(node.value, ast.Call):
                        call_type = self._infer_call_type(node.value)
                        if call_type:
                            type_info.type = call_type
                            # input返回值的范围：int是任意整数，str是任意字符串
                            if call_type == int:
                                type_info.min_val = -float('inf')
                                type_info.max_val = float('inf')
                            elif call_type == float:
                                type_info.min_val = -float('inf')
                                type_info.max_val = float('inf')
                    
                    # 3. 运算赋值：a = b + c（基于已有类型推断）
                    elif isinstance(node.value, ast.BinOp):
                        left_type = None
                        right_type = None
                        # 获取左操作数类型
                        if isinstance(node.value.left, ast.Name) and node.value.left.id in self.parent.type_context:
                            left_type = self.parent.type_context[node.value.left.id].type
                        elif isinstance(node.value.left, ast.Constant):
                            left_type = type(node.value.left.value)
                        # 获取右操作数类型
                        if isinstance(node.value.right, ast.Name) and node.value.right.id in self.parent.type_context:
                            right_type = self.parent.type_context[node.value.right.id].type
                        elif isinstance(node.value.right, ast.Constant):
                            right_type = type(node.value.right.value)
                        # 推断运算结果类型
                        if left_type and right_type and left_type == right_type:
                            if left_type in [int, float]:
                                type_info.type = left_type
                                # 推断取值范围（简单版）
                                left_min = self.parent.type_context.get(node.value.left.id, TypeInfo()).min_val
                                left_max = self.parent.type_context.get(node.value.left.id, TypeInfo()).max_val
                                right_min = self.parent.type_context.get(node.value.right.id, TypeInfo()).min_val
                                right_max = self.parent.type_context.get(node.value.right.id, TypeInfo()).max_val
                                
                                if isinstance(node.value.op, ast.Add):
                                    type_info.min_val = (left_min or 0) + (right_min or 0)
                                    type_info.max_val = (left_max or 0) + (right_max or 0)
                                elif isinstance(node.value.op, ast.Mult):
                                    type_info.min_val = (left_min or 0) * (right_min or 0)
                                    type_info.max_val = (left_max or 0) * (right_max or 0)
                    
                    # 更新类型上下文
                    self._update_var_type(var_name, type_info)
                    self.current_scope.add(var_name)
                return node

            def visit_Compare(self, node: ast.Compare) -> ast.AST:
                """处理条件判断的类型推断（更新变量取值范围）"""
                node = self.generic_visit(node)
                # 仅处理单变量比较
                if isinstance(node.left, ast.Name) and node.left.id in self.parent.type_context:
                    var_name = node.left.id
                    var_info = self.parent.type_context[var_name]
                    # 处理常量比较：n > 5 → min_val=6
                    if len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Constant):
                        comp_val = node.comparators[0].value
                        op = node.ops[0]
                        # 更新取值范围
                        if isinstance(op, ast.Gt):  # >
                            var_info.min_val = comp_val + 1 if var_info.type == int else comp_val
                        elif isinstance(op, ast.GtE):  # >=
                            var_info.min_val = comp_val
                        elif isinstance(op, ast.Lt):  # <
                            var_info.max_val = comp_val - 1 if var_info.type == int else comp_val
                        elif isinstance(op, ast.LtE):  # <=
                            var_info.max_val = comp_val
                        elif isinstance(op, ast.Eq):  # ==
                            var_info.is_const = True
                            var_info.value = comp_val
                            var_info.min_val = comp_val
                            var_info.max_val = comp_val
                return node

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                """处理函数参数的类型推断"""
                # 保存当前作用域
                old_scope = self.current_scope.copy()
                self.current_scope.clear()
                
                # 处理函数参数
                for arg in node.args.args:
                    var_info = TypeInfo()
                    # 处理有默认值的参数
                    if arg in node.args.defaults:
                        default_idx = node.args.defaults.index(arg)
                        default_val = node.args.defaults[default_idx]
                        if isinstance(default_val, ast.Constant):
                            var_info.type = type(default_val.value)
                            var_info.is_const = True
                            var_info.value = default_val.value
                            var_info.min_val = default_val.value
                            var_info.max_val = default_val.value
                    self._update_var_type(arg.arg, var_info)
                    self.current_scope.add(arg.arg)
                
                # 处理函数体
                node.body = [self.visit(stmt) for stmt in node.body]
                
                # 恢复作用域
                self.current_scope = old_scope
                return node

        visitor = TypeInferenceVisitor(self)
        return visitor.visit(node)

    def _range_optimization(self, node: ast.AST) -> ast.AST:
        """
        取值范围优化：基于类型推断的范围预判
        例：已知n>0且n是int，直接优化掉n<=0的分支
        """
        class RangeOptimizer(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def visit_If(self, node: ast.If) -> ast.AST:
                """优化不可能执行的条件分支"""
                node = self.generic_visit(node)
                # 判断条件是否恒真/恒假
                condition_result = self._eval_condition(node.test)
                if condition_result is True:
                    # 恒真：只保留if体，删除else
                    return node.body
                elif condition_result is False:
                    # 恒假：只保留else体（如果有）
                    return node.orelse if node.orelse else []
                return node

            def _eval_condition(self, node: ast.AST) -> Optional[bool]:
                """评估条件是否恒真/恒假（基于类型推断）"""
                # 处理比较表达式
                if isinstance(node, ast.Compare):
                    if isinstance(node.left, ast.Name) and node.left.id in self.parent.type_context:
                        var_info = self.parent.type_context[node.left.id]
                        if len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Constant):
                            comp_val = node.comparators[0].value
                            op = node.ops[0]
                            # 基于取值范围判断
                            if var_info.min_val is not None and var_info.max_val is not None:
                                if isinstance(op, ast.Gt):
                                    if var_info.min_val > comp_val:
                                        return True
                                    elif var_info.max_val <= comp_val:
                                        return False
                                elif isinstance(op, ast.Lt):
                                    if var_info.max_val < comp_val:
                                        return True
                                    elif var_info.min_val >= comp_val:
                                        return False
                                elif isinstance(op, ast.Eq):
                                    if var_info.min_val == var_info.max_val == comp_val:
                                        return True
                                    elif var_info.min_val > comp_val or var_info.max_val < comp_val:
                                        return False
                # 处理布尔运算
                elif isinstance(node, ast.BoolOp):
                    values = [self._eval_condition(v) for v in node.values]
                    if all(v is not None for v in values):
                        if isinstance(node.op, ast.And):
                            return all(values)
                        elif isinstance(node.op, ast.Or):
                            return any(values)
                # 处理常量布尔值
                elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
                    return node.value
                return None

        visitor = RangeOptimizer(self)
        return visitor.visit(node)

    def _short_circuit_optimization(self, node: ast.AST) -> ast.AST:
        """短路表达式优化：提前计算短路条件"""
        class ShortCircuitVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
                """优化and/or短路表达式"""
                node = self.generic_visit(node)
                # 处理and短路：False and xxx → False
                if isinstance(node.op, ast.And):
                    for i, value in enumerate(node.values):
                        eval_result = self._eval_const(value)
                        if eval_result is False:
                            # 短路：直接返回False
                            return ast.Constant(value=False, lineno=node.lineno, col_offset=node.col_offset)
                        elif eval_result is True and i == len(node.values) - 1:
                            # 最后一个为True → 返回True
                            return ast.Constant(value=True, lineno=node.lineno, col_offset=node.col_offset)
                # 处理or短路：True or xxx → True
                elif isinstance(node.op, ast.Or):
                    for value in node.values:
                        eval_result = self._eval_const(value)
                        if eval_result is True:
                            # 短路：直接返回True
                            return ast.Constant(value=True, lineno=node.lineno, col_offset=node.col_offset)
                    # 所有都为False → 返回False
                    return ast.Constant(value=False, lineno=node.lineno, col_offset=node.col_offset)
                return node

            def _eval_const(self, node: ast.AST) -> Optional[bool]:
                """评估节点是否为常量布尔值"""
                if isinstance(node, ast.Constant) and isinstance(node.value, bool):
                    return node.value
                # 基于类型推断的常量
                elif isinstance(node, ast.Name) and node.id in self.parent.type_context:
                    var_info = self.parent.type_context[node.id]
                    if var_info.is_const and isinstance(var_info.value, bool):
                        return var_info.value
                return None

        visitor = ShortCircuitVisitor(self)
        return visitor.visit(node)

    def _dead_code_elimination(self, node: ast.AST) -> ast.AST:
        """
        死代码消除：删除不可能执行的代码
        例：n = 5; if n > 10: xxx → 删除整个if分支
        """
        class DeadCodeVisitor(ast.NodeTransformer):
            def __init__(self, parent):
                self.parent = parent

            def visit_If(self, node: ast.If) -> ast.AST:
                """删除恒假的if分支"""
                node = self.generic_visit(node)
                # 评估条件
                condition_result = self._eval_condition(node.test)
                if condition_result is False:
                    # 恒假：返回else分支（如果有），否则删除整个if
                    return node.orelse if node.orelse else []
                elif condition_result is True:
                    # 恒真：返回if分支，删除else
                    return node.body
                return node

            def visit_Assign(self, node: ast.Assign) -> ast.AST:
                """删除未使用的变量赋值"""
                node = self.generic_visit(node)
                # 检查变量是否被使用（简单版：只检查是否在类型上下文中且非常量）
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id
                    # 如果变量未被使用且不是常量，删除赋值
                    if var_name not in self.parent.type_context or not self.parent.type_context[var_name].is_const:
                        # 简单检查：后续是否有使用（这里简化处理，实际需要数据流分析）
                        return []
                return node

            def _eval_condition(self, node: ast.AST) -> Optional[bool]:
                """评估条件是否恒真/恒假"""
                # 复用range_optimization中的评估逻辑
                if isinstance(node, ast.Compare):
                    if isinstance(node.left, ast.Name) and node.left.id in self.parent.type_context:
                        var_info = self.parent.type_context[node.left.id]
                        if len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Constant):
                            comp_val = node.comparators[0].value
                            op = node.ops[0]
                            if var_info.min_val is not None and var_info.max_val is not None:
                                if isinstance(op, ast.Gt):
                                    return var_info.min_val > comp_val
                                elif isinstance(op, ast.Lt):
                                    return var_info.max_val < comp_val
                                elif isinstance(op, ast.Eq):
                                    return var_info.min_val == var_info.max_val == comp_val
                elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
                    return node.value
                return None

        visitor = DeadCodeVisitor(self)
        return visitor.visit(node)


# 初始化全局解析器实例（保持原API）
cycy_parser = LazyASTParser()