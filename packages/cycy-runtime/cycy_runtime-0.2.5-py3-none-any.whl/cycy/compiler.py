from enum import Enum
import ast
import os
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path
import shutil
import io

class OptimizeLevel(Enum):
    """优化等级枚举类（新增O3支持）"""
    LEVEL0 = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3  # 新增O3级别
    O0 = LEVEL0
    O1 = LEVEL1
    O2 = LEVEL2
    O3 = LEVEL3  # 新增O3别名

class MSVCCompilerError(Exception):
    """MSVC编译相关异常"""
    pass

class GenerationCompiler:
    def __init__(self, opt_level=OptimizeLevel.LEVEL1):
        """初始化编译器（兼容原有逻辑）"""
        self.compile_cache = {}
        self.opt_level = opt_level
        
        # 内部初始化MSVC环境（静默失败，兼容无MSVC环境）
        try:
            self.msvc_env = self._find_and_configure_msvc()
            self.msvc_available = True if self.msvc_env else False
        except Exception as e:
            self.msvc_env = None
            self.msvc_available = False
            print(f"⚠️ 未找到MSVC环境，将使用模拟编译模式：{str(e)[:50]}")

    def _find_msvc_path(self):
        """内部方法：查找MSVC安装路径"""
        vswhere_paths = [
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft Visual Studio", "Installer", "vswhere.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft Visual Studio", "Installer", "vswhere.exe")
        ]
        vswhere_exe = None
        for path in vswhere_paths:
            if os.path.exists(path):
                vswhere_exe = path
                break
        
        if not vswhere_exe:
            raise MSVCCompilerError("未找到vswhere.exe，请安装Visual Studio Build Tools或Visual Studio")
        
        cmd = [
            vswhere_exe,
            "-latest",
            "-products", "*",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property", "installationPath"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        vs_install_path = result.stdout.strip()
        if not vs_install_path:
            raise MSVCCompilerError("vswhere未返回有效的VS安装路径")
        
        msvc_root = Path(vs_install_path) / "VC" / "Tools" / "MSVC"
        if not msvc_root.exists():
            raise MSVCCompilerError(f"未找到MSVC工具链: {msvc_root}")
        
        msvc_versions = [v for v in msvc_root.iterdir() if v.is_dir()]
        if not msvc_versions:
            raise MSVCCompilerError(f"在{msvc_root}下未找到MSVC版本目录")
        
        latest_msvc = sorted(msvc_versions, reverse=True)[0]
        return latest_msvc

    def _configure_msvc_env(self, msvc_path):
        """内部方法：配置MSVC环境变量"""
        arch = "x64" if sys.maxsize > 2**32 else "x86"
        env = os.environ.copy()
        
        env["MSVC_ROOT"] = str(msvc_path)
        bin_path = msvc_path / "bin" / "Hostx64" / arch
        if not bin_path.exists():
            bin_path = msvc_path / "bin" / "Hostx86" / arch
        env["PATH"] = f"{str(bin_path)};{env['PATH']}"
        
        include_path = msvc_path / "include"
        env["INCLUDE"] = f"{str(include_path)};{env.get('INCLUDE', '')}"
        
        lib_path = msvc_path / "lib" / arch
        env["LIB"] = f"{str(lib_path)};{env.get('LIB', '')}"
        
        # 验证MSVC是否可用
        try:
            subprocess.run(
                ["cl.exe", "/?"],
                env=env,
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise MSVCCompilerError("配置MSVC环境后仍无法执行cl.exe")
        
        return env

    def _find_and_configure_msvc(self):
        """内部方法：查找并配置MSVC环境（封装异常）"""
        try:
            msvc_path = self._find_msvc_path()
            return self._configure_msvc_env(msvc_path)
        except Exception as e:
            print(f"MSVC配置失败: {e}")
            return None

    def _ast_to_source(self, ast_tree):
        """内部方法：将AST树转换为Python源代码"""
        if isinstance(ast_tree, ast.AST):
            return ast.unparse(ast_tree)
        elif isinstance(ast_tree, str):
            return ast_tree
        else:
            raise ValueError("ast_tree必须是AST对象或字符串")

    def _compile_with_msvc(self, source_code, code_fingerprint):
        """内部方法：使用MSVC编译Python代码（修复模块名后缀问题）"""
        # 创建临时目录
        output_dir = tempfile.mkdtemp(prefix="python_msvc_compile_")
        output_dir = Path(output_dir)
        
        # 生成模块名和文件（固定模块名，避免后缀干扰）
        module_name = f"compiled_{code_fingerprint[:8]}"
        src_file = output_dir / f"{module_name}.pyx"
        setup_file = output_dir / "setup.py"
        
        # 写入Cython源文件
        with open(src_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        # 优化参数配置（O3级极致优化）
        opt_flags = {
            OptimizeLevel.LEVEL0: ["/O0", "/Od"],
            OptimizeLevel.LEVEL1: ["/O1"],
            OptimizeLevel.LEVEL2: ["/O2", "/Ot"],
            OptimizeLevel.LEVEL3: ["/O2", "/Ot", "/Ox", "/Oy", "/Ob2", "/GF", "/Gy"]
        }[self.opt_level]
        
        # 生成setup.py（核心修复：强制模块名一致）
        setup_code = f"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import sys
import os

# 强制禁用自动后缀，保证模块名匹配
os.environ['CYTHON_CCOMPILER_NO_DECORATED_NAMES'] = '1'

ext_modules = [
    Extension(
        name="{module_name}",
        sources=["{src_file.name}"],
        extra_compile_args={opt_flags + ["/MD", "/nologo", "/EHsc", "/DNDEBUG"]},
        extra_link_args=["/DLL", "/NOLOGO"],
        language="c++",
        define_macros=[
            ("CYTHON_MODULE_NAME", "{module_name}"),
            ("PY_SSIZE_T_CLEAN", 1)
        ],
        undef_macros=["_DEBUG"]
    )
]

setup(
    name="{module_name}",
    ext_modules=cythonize(
        ext_modules,
        language_level=sys.version_info[0],
        compiler_directives={{
            'boundscheck': False,
            'wraparound': False,
            'nonecheck': False,
            'cdivision': True
        }}
    ),
    options={{
        "build_ext": {{
            "inplace": True,
            "suffix": ".pyd",
            "force": True,
            "build_lib": "{output_dir}",
            "build_temp": "{output_dir / 'temp'}"
        }}
    }}
)
"""
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_code)
        
        # 执行编译命令
        compile_cmd = [
            sys.executable,
            str(setup_file),
            "build_ext",
            "--inplace",
            "--quiet"
        ]
        
        result = subprocess.run(
            compile_cmd,
            env=self.msvc_env,
            cwd=str(output_dir),
            capture_output=True,
            text=True
        )
        
        # 检查编译是否成功
        if result.returncode != 0:
            raise MSVCCompilerError(f"MSVC编译失败：{result.stderr[:200]}")
        
        # 查找.pyd文件（兼容两种命名方式）
        pyd_files = []
        # 方式1：精准匹配模块名.pyd
        exact_pyd = output_dir / f"{module_name}.pyd"
        if exact_pyd.exists():
            pyd_files.append(exact_pyd)
        # 方式2：模糊匹配（兼容残留后缀）
        if not pyd_files:
            pyd_files = list(output_dir.glob(f"{module_name}*.pyd"))
        
        if not pyd_files:
            raise MSVCCompilerError(f"未找到编译生成的.pyd文件，输出：{result.stdout[:200]}")
        
        return {
            'pyd_path': str(pyd_files[0]),
            'src_path': str(src_file),
            'setup_path': str(setup_file),
            'output_dir': str(output_dir),
            'compile_output': result.stdout,
            'compile_stderr': result.stderr,
            'module_name': module_name
        }

    def set_opt_level(self, level):
        """设置优化等级（支持0-3）"""
        if isinstance(level, int):
            self.opt_level = OptimizeLevel(min(max(level, 0), 3))
        elif isinstance(level, OptimizeLevel):
            self.opt_level = level
        else:
            self.opt_level = OptimizeLevel.LEVEL1
        print(f"⚙️ 设置优化等级：{self.opt_level.name} (值：{self.opt_level.value})")

    def compile(self, ast_tree, code_fingerprint):
        """核心编译方法（兼容缓存+降级）"""
        # 缓存逻辑
        if code_fingerprint in self.compile_cache:
            print(f"📌 复用缓存编译结果：{code_fingerprint[:8]}...")
            return self.compile_cache[code_fingerprint]
        
        print(f"🔧 编译代码（优化等级：{self.opt_level.value}）")
        
        # 基础返回结果
        compiled_result = {
            'ast': ast_tree,
            'fingerprint': code_fingerprint,
            'opt_level': self.opt_level.value,
            'is_jit': self.opt_level.value >= 1,
            'compiler': 'SIMULATED'
        }
        
        # 尝试MSVC编译
        if self.msvc_available:
            try:
                print("🔨 使用MSVC进行原生编译...")
                source_code = self._ast_to_source(ast_tree)
                msvc_result = self._compile_with_msvc(source_code, code_fingerprint)
                compiled_result.update(msvc_result)
                compiled_result['compiler'] = 'MSVC'
            except Exception as e:
                print(f"⚠️ MSVC编译失败，降级为模拟编译：{str(e)[:50]}")
        
        # 存入缓存
        self.compile_cache[code_fingerprint] = compiled_result
        return compiled_result

    def invalidate_cache(self, code_fingerprint):
        """失效缓存并清理临时文件"""
        if code_fingerprint in self.compile_cache:
            cached = self.compile_cache[code_fingerprint]
            # 清理临时文件
            if 'output_dir' in cached and os.path.exists(cached['output_dir']):
                try:
                    shutil.rmtree(cached['output_dir'], ignore_errors=True)
                except:
                    pass
            # 删除缓存
            del self.compile_cache[code_fingerprint]
            print(f"🗑️ 失效缓存：{code_fingerprint[:8]}...")

    def clear_cache(self):
        """清空所有编译缓存"""
        for fp in list(self.compile_cache.keys()):
            self.invalidate_cache(fp)
        print("🧹 已清空所有编译缓存")

# 全局编译器实例（必须在全局作用域，供外部导入）
cycy_compiler = GenerationCompiler()

# 测试代码（仅在直接运行compiler.py时执行）
if __name__ == "__main__":
    # 测试O3编译
    test_code = """
def factorial(n: int) -> int:
    res = 1
    for i in range(2, n+1):
        res *= i
    return res

if __name__ == '__main__':
    print(factorial(10))
"""
    test_ast = ast.parse(test_code)
    cycy_compiler.set_opt_level(OptimizeLevel.O3)
    result = cycy_compiler.compile(test_ast, "test_fingerprint_12345678")
    
    print("\n=== 编译测试结果 ===")
    print(f"优化等级：{result['opt_level']}")
    print(f"编译器：{result['compiler']}")
    if 'pyd_path' in result:
        print(f"生成的.pyd文件：{result['pyd_path']}")
    print("测试完成！")