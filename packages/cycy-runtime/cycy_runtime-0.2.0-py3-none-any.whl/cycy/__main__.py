import sys
import argparse
from .parser import cycy_parser
from .compiler import cycy_compiler, OptimizeLevel
from .runtime import cycy_runtime

def main():
    parser = argparse.ArgumentParser(description='CyCy Python Runtime')
    # 修改：opt-level范围改为0-3，默认保持1（兼容原有行为）
    parser.add_argument('-O', '--opt-level', type=int, default=1, choices=[0,1,2,3], 
                        help='Optimize level (0-3, O3=终极作弊优化)')
    parser.add_argument('--compat', action='store_true', help='Force CPython compat mode')
    parser.add_argument("script", help="要运行的Python脚本路径")
    parser.add_argument("script_args", nargs='*', help="传递给脚本的参数")
    args = parser.parse_args()
    original_argv = sys.argv
    sys.argv = [args.script] + args.script_args  # 替换为原生Python的argv格式

    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: No such file or directory: '{args.script}'", file=sys.stderr)
        sys.exit(1)

    # 初始化配置
    cycy_compiler.set_opt_level(args.opt_level)
    if args.compat:
        cycy_runtime.compat_mode = True
        print("🔄 已启用CPython兼容模式")

    # 解析+编译：核心修改 - 根据opt_level联动parser的O3优化
    print(f"🔍 解析脚本：{args.script}")
    # 映射：O0=无优化，O1=基础优化，O2=O2级，O3=终极O3级
    if args.opt_level == 0:
        ast_tree = cycy_parser.parse(source, args.script, optimize=False)
    elif args.opt_level == 1:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O1")
    elif args.opt_level == 2:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O2")
    elif args.opt_level == 3:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O3")
    
    fingerprint = cycy_runtime.get_code_fingerprint(source)
    compiled_result = cycy_compiler.compile(ast_tree, fingerprint)
    
    # 运行脚本（简化版：直接执行源码，后续对接C扩展）
    print(f"🚀 运行脚本（优化等级：{args.opt_level}）")
    try:
        # 如果是O3级别且非兼容模式，执行优化后的AST代码
        if args.opt_level == 3 and not args.compat:
            optimized_source = ast.unparse(ast_tree)
            exec(optimized_source, globals())
        else:
            exec(source, globals())
        print(f"✅ CyCy运行完成：{args.script}")
    except Exception as e:
        print(f"❌ 运行出错：{e}")
        sys.exit(1)
    finally:
        sys.argv = original_argv

if __name__ == '__main__':
    main()