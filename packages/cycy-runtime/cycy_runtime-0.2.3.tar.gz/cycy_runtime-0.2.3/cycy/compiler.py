def _compile_with_msvc(self, source_code, code_fingerprint):
    """内部方法：使用MSVC编译Python代码"""
    # 创建临时目录
    output_dir = tempfile.mkdtemp(prefix="python_msvc_compile_")
    output_dir = Path(output_dir)
    
    # 生成模块名和文件（保持不变）
    module_name = f"compiled_{code_fingerprint[:8]}"  # 核心模块名：compiled_039a0b1c
    src_file = output_dir / f"{module_name}.pyx"
    setup_file = output_dir / "setup.py"
    
    # 写入源代码（保持不变）
    with open(src_file, 'w', encoding='utf-8') as f:
        f.write(source_code)
    
    # 获取优化参数（保持不变）
    opt_flags = {
        OptimizeLevel.LEVEL0: ["/O0", "/Od"],
        OptimizeLevel.LEVEL1: ["/O1"],
        OptimizeLevel.LEVEL2: ["/O2", "/Ot"],
        OptimizeLevel.LEVEL3: ["/O2", "/Ot", "/Ox", "/Oy", "/Ob2", "/GF", "/Gy"]
    }[self.opt_level]
    
    # ========== 核心修改：生成setup.py时强制模块名 ==========
    setup_code = f"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import sys

# 强制模块名，禁用自动后缀
ext_modules = [
    Extension(
        name="{module_name}",  # 核心：模块名必须固定
        sources=["{src_file.name}"],
        extra_compile_args={opt_flags + ["/MD", "/nologo", "/EHsc"]},
        language="c++",
        # 关键：禁用Cython自动加后缀
        define_macros=[("CYTHON_CCOMPILER_NO_DECORATED_NAMES", "1")],
        # 关键：强制输出文件名和模块名一致
        undef_macros=["_DEBUG"],
    )
]

# 核心：编译时指定输出文件名，去掉Python版本后缀
setup(
    name="{module_name}",
    ext_modules=cythonize(
        ext_modules, 
        language_level=sys.version_info[0],
        # 强制生成的C文件使用正确的模块名
        compile_time_env={{"CYTHON_MODULE_NAME": "{module_name}"}}
    ),
    # 关键：指定输出文件名，去掉自动后缀
    options={{
        "build_ext": {{
            "inplace": True,
            "suffix": ".pyd",  # 强制后缀为.pyd，不加版本信息
            "force": True
        }}
    }}
)
"""
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(setup_code)
    
    # 执行编译（保持不变）
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
    
    # ========== 额外修复：查找.pyd文件时忽略后缀 ==========
    # 原来的查找方式：list(output_dir.glob(f"{module_name}*.pyd"))
    # 新方式：精准匹配模块名（去掉版本后缀）
    pyd_files = []
    for file in output_dir.glob("*.pyd"):
        # 只取文件名前缀（去掉.cp314-win_amd64等后缀）
        file_prefix = file.name.split('.')[0]
        if file_prefix == module_name:
            pyd_files.append(file)
    
    if not pyd_files:
        # 降级：如果还是找不到，用原来的模糊匹配
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