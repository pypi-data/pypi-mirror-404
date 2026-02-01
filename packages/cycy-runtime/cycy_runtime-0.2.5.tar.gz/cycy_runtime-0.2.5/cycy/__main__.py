import sys
import argparse
import importlib.util
import os
import tempfile
from .parser import cycy_parser
from .compiler import cycy_compiler, OptimizeLevel
from .runtime import cycy_runtime
import ast 
def load_compiled_module(pyd_path):
    """加载编译后的.pyd模块（核心函数）"""
    # 1. 获取模块名（从路径提取：compiled_12345678.pyd → compiled_12345678）
    module_name = os.path.splitext(os.path.basename(pyd_path))[0]
    # 2. 创建模块规范
    spec = importlib.util.spec_from_file_location(module_name, pyd_path)
    if spec is None:
        raise ImportError(f"无法创建模块规范：{pyd_path}")
    # 3. 加载模块
    compiled_module = importlib.util.module_from_spec(spec)
    # 4. 执行模块（等价于运行脚本）
    spec.loader.exec_module(compiled_module)
    return compiled_module

def main():
    parser = argparse.ArgumentParser(description='CyCy Python Runtime')
    parser.add_argument('-O', '--opt-level', type=int, default=1, choices=[0,1,2,3], 
                        help='Optimize level (0-3, O3=终极作弊优化)')
    parser.add_argument('--compat', action='store_true', help='Force CPython compat mode')
    parser.add_argument("--keep-temp", action='store_true', help='保留编译临时文件（调试用）')
    parser.add_argument("script", help="要运行的Python脚本路径")
    parser.add_argument("script_args", nargs='*', help="传递给脚本的参数")
    args = parser.parse_args()
    original_argv = sys.argv
    sys.argv = [args.script] + args.script_args  # 模拟原生Python的argv

    # 1. 读取源码
    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: No such file or directory: '{args.script}'", file=sys.stderr)
        sys.exit(1)

    # 2. 初始化配置
    cycy_compiler.set_opt_level(args.opt_level)
    if args.compat:
        cycy_runtime.compat_mode = True
        print("🔄 已启用CPython兼容模式")

    # 3. 解析+编译（核心步骤）
    print(f"🔍 解析脚本：{args.script}")
    # 根据优化级别选择解析策略
    if args.opt_level == 0:
        ast_tree = cycy_parser.parse(source, args.script, optimize=False)
    elif args.opt_level == 1:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O1")
    elif args.opt_level == 2:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O2")
    elif args.opt_level == 3:
        ast_tree = cycy_parser.parse(source, args.script, optimize=True, optimize_level="O3")
    
    # 编译生成.pyd（如果MSVC可用）
    fingerprint = cycy_runtime.get_code_fingerprint(source)
    compiled_result = cycy_compiler.compile(ast_tree, fingerprint)

    # 4. 运行编译后的代码（核心改造！）
    print(f"🚀 运行脚本（优化等级：{args.opt_level}，编译器：{compiled_result['compiler']}）")
    try:
        # 优先运行编译后的.pyd模块（MSVC编译成功时）
        if compiled_result['compiler'] == 'MSVC' and 'pyd_path' in compiled_result:
            pyd_path = compiled_result['pyd_path']
            print(f"⚡ 加载编译后的二进制模块：{os.path.basename(pyd_path)}")
            # 把.pyd所在目录加入sys.path（确保能导入）
            pyd_dir = os.path.dirname(pyd_path)
            sys.path.insert(0, pyd_dir)
            # 加载并运行.pyd模块
            compiled_module = load_compiled_module(pyd_path)
            # 如果脚本有__main__逻辑，手动触发（模拟python script.py）
            if hasattr(compiled_module, '__main__'):
                compiled_module.__main__()
        # 降级方案1：O3优化但无MSVC → 运行优化后的AST源码
        elif args.opt_level == 3 and not args.compat:
            print(f"⚡ 运行O3级优化后的AST源码")
            optimized_source = ast.unparse(ast_tree)
            exec(optimized_source, globals())
        # 降级方案2：兼容模式/低优化级 → 运行原始源码
        else:
            print(f"▶️ 运行原始源码（兼容模式/低优化级）")
            exec(source, globals())
        
        print(f"✅ CyCy运行完成：{args.script}")
    except Exception as e:
        print(f"❌ 运行出错：{e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # 清理临时文件（除非指定--keep-temp）
        if not args.keep_temp and 'output_dir' in compiled_result:
            try:
                import shutil
                shutil.rmtree(compiled_result['output_dir'], ignore_errors=True)
            except:
                pass
        sys.argv = original_argv

if __name__ == '__main__':
    main()