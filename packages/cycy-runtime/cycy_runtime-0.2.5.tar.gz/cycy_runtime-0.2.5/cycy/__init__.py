"""CyCy: 新一代Python全场景运行时
- 100%兼容CPython
- 全自动无感加速
- 零依赖开箱即用
"""
__version__ = "0.2.5"

from .parser import cycy_parser, LazyASTParser
from .compiler import cycy_compiler, GenerationCompiler, OptimizeLevel
from .runtime import cycy_runtime, RuntimeManager