"""
Build script for mps-correlation.
"""

import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class ObjCppBuildExt(build_ext):
    """Custom build_ext that handles .mm (Objective-C++) files."""

    def build_extension(self, ext):
        self.compiler.src_extensions.append('.mm')
        original_compile = self.compiler._compile

        def patched_compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
            if src.endswith('.mm'):
                try:
                    self.compiler.compiler_so = ['clang++'] + [
                        arg for arg in self.compiler.compiler_so[1:]
                        if arg not in ['-Wstrict-prototypes']
                    ]
                except:
                    pass
            return original_compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

        self.compiler._compile = patched_compile
        super().build_extension(ext)


def get_extensions():
    import torch
    from torch.utils.cpp_extension import CppExtension

    torch_include = torch.utils.cpp_extension.include_paths()

    ext_modules = [
        CppExtension(
            name="mps_correlation._C",
            sources=["mps_correlation/csrc/correlation_mps.mm"],
            include_dirs=torch_include,
            extra_compile_args=["-std=c++17", "-O3", "-DTORCH_EXTENSION_NAME=_C"],
            extra_link_args=[
                "-framework", "Metal",
                "-framework", "Foundation",
                "-framework", "MetalPerformanceShaders",
            ],
        )
    ]
    return ext_modules


setup(
    name="mps-correlation",
    version="0.1.0",
    description="Correlation layer for optical flow on Apple Silicon (MPS)",
    author="mpsops",
    packages=["mps_correlation"],
    ext_modules=get_extensions(),
    cmdclass={"build_ext": ObjCppBuildExt},
    install_requires=["torch>=2.0.0"],
    python_requires=">=3.10",
)
