from enum import Enum
import ast
import os
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path
from setuptools import setup, Extension
import shutil
import io

class OptimizeLevel(Enum):
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
        # 完全保留原有初始化逻辑
        self.compile_cache = {}
        self.opt_level = opt_level
        
        # 内部初始化MSVC环境（静默失败，兼容无MSVC环境的情况）
        try:
            self.msvc_env = self._find_and_configure_msvc()
            self.msvc_available = True if self.msvc_env else False
        except:
            self.msvc_env = None
            self.msvc_available = False
            print("⚠️ 未找到MSVC环境，将使用模拟编译模式")

    def _find_msvc_path(self):
        """内部方法：查找MSVC路径"""
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
        """内部方法：查找并配置MSVC环境"""
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
            return ast_tree  # 兼容直接传入源代码的情况
        else:
            raise ValueError("ast_tree必须是AST对象或字符串")

    def _compile_with_msvc(self, source_code, code_fingerprint):
        """内部方法：使用MSVC编译Python代码"""
        # 创建临时目录
        output_dir = tempfile.mkdtemp(prefix="python_msvc_compile_")
        output_dir = Path(output_dir)
        
        # 生成模块名和文件
        module_name = f"compiled_{code_fingerprint[:8]}"
        src_file = output_dir / f"{module_name}.pyx"
        setup_file = output_dir / "setup.py"
        
        # 写入源代码
        with open(src_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        # 扩展优化参数：新增O3级别（MSVC的O3等价于/O2 + /Ot + /Ox + /Oy等）
        opt_flags = {
            OptimizeLevel.LEVEL0: ["/O0", "/Od"],
            OptimizeLevel.LEVEL1: ["/O1"],
            OptimizeLevel.LEVEL2: ["/O2", "/Ot"],
            OptimizeLevel.LEVEL3: ["/O2", "/Ot", "/Ox", "/Oy", "/Ob2", "/GF", "/Gy"]  # O3级编译参数
        }[self.opt_level]
        
        # 生成setup.py
        setup_code = f"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import sys

ext_modules = [
    Extension(
        name="{module_name}",
        sources=["{src_file.name}"],
        extra_compile_args={opt_flags + ["/MD", "/nologo", "/EHsc"]},
        language="c++"
    )
]

setup(
    name="{module_name}",
    ext_modules=cythonize(ext_modules, language_level=sys.version_info[0])
)
"""
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_code)
        
        # 执行编译
        compile_cmd = [
            sys.executable,
            str(setup_file),
            "build_ext",
            "--inplace",
            "--build-lib", str(output_dir),
            "--build-temp", str(output_dir / "temp")
        ]
        
        result = subprocess.run(
            compile_cmd,
            env=self.msvc_env,
            cwd=str(output_dir),
            capture_output=True,
            text=True,
            check=True
        )
        
        # 查找pyd文件
        pyd_files = list(output_dir.glob(f"{module_name}*.pyd"))
        if not pyd_files:
            raise MSVCCompilerError("未生成.pyd文件")
        
        return {
            'pyd_path': str(pyd_files[0]),
            'src_path': str(src_file),
            'setup_path': str(setup_file),
            'output_dir': str(output_dir),
            'compile_output': result.stdout,
            'compile_stderr': result.stderr
        }

    # 扩展set_opt_level：支持3级优化
    def set_opt_level(self, level):
        if isinstance(level, int):
            self.opt_level = OptimizeLevel(min(level, 3))  # 上限改为3
        elif isinstance(level, OptimizeLevel):
            self.opt_level = level
        print(f"⚙️ 设置优化等级：{self.opt_level.name}")

    # 完全保留原有方法签名和返回值格式
    def compile(self, ast_tree, code_fingerprint):
        # 原有缓存逻辑完全保留
        if code_fingerprint in self.compile_cache:
            print(f"📌 复用缓存编译结果：{code_fingerprint[:8]}...")
            return self.compile_cache[code_fingerprint]
        
        print(f"🔧 编译代码（优化等级：{self.opt_level.value}）")
        
        # 构建基础返回结果（完全兼容原有格式）
        compiled_result = {
            'ast': ast_tree,
            'fingerprint': code_fingerprint,
            'opt_level': self.opt_level.value,
            'is_jit': self.opt_level.value >= 1
        }
        
        # 如果MSVC可用，执行真实编译并扩展结果
        if self.msvc_available:
            try:
                print("🔨 使用MSVC进行真实编译...")
                # 将AST转换为源代码
                source_code = self._ast_to_source(ast_tree)
                # 调用MSVC编译
                msvc_result = self._compile_with_msvc(source_code, code_fingerprint)
                # 扩展结果（不修改原有字段）
                compiled_result.update(msvc_result)
                compiled_result['compiler'] = 'MSVC'
            except Exception as e:
                print(f"⚠️ MSVC编译失败，降级为模拟编译：{e}")
                compiled_result['compiler'] = 'SIMULATED'
        else:
            compiled_result['compiler'] = 'SIMULATED'
        
        # 原有缓存逻辑完全保留
        self.compile_cache[code_fingerprint] = compiled_result
        return compiled_result

    # 完全保留原有方法签名
    def invalidate_cache(self, code_fingerprint):
        if code_fingerprint in self.compile_cache:
            # 扩展清理逻辑：删除MSVC生成的文件
            cached = self.compile_cache[code_fingerprint]
            if 'output_dir' in cached and os.path.exists(cached['output_dir']):
                try:
                    shutil.rmtree(cached['output_dir'])
                except:
                    pass
            
            # 原有逻辑完全保留
            del self.compile_cache[code_fingerprint]
            print(f"🗑️ 失效缓存：{code_fingerprint[:8]}...")

# 完全保留原有实例化方式
cycy_compiler = GenerationCompiler()

# ------------------- 兼容测试示例 -------------------
if __name__ == "__main__":
    # 1. 原有调用方式完全可用
    # 创建测试AST树
    test_code = """
def main():
    print("Hello World!")
    return 42
"""
    test_ast = ast.parse(test_code)
    
    # 测试O3级别设置
    cycy_compiler.set_opt_level(OptimizeLevel.O3)
    result = cycy_compiler.compile(test_ast, "test_fingerprint_123456")
    
    # 验证原有字段存在
    print(f"\n原有字段验证：")
    print(f"AST: {result['ast']}")
    print(f"Fingerprint: {result['fingerprint']}")
    print(f"Opt Level: {result['opt_level']}")  # 现在会输出3
    print(f"Is JIT: {result['is_jit']}")
    
    # 验证扩展字段（MSVC编译结果）
    if 'pyd_path' in result:
        print(f"\nMSVC编译结果：")
        print(f"编译后的模块：{result['pyd_path']}")
    
    # 失效缓存（原有调用方式）
    cycy_compiler.invalidate_cache("test_fingerprint_123456")