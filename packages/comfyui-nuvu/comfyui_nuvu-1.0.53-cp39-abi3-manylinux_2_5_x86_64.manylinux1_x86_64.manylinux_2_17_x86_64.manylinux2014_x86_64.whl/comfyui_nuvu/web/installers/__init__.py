"""nuvu package installers.

Each installer module exposes install/uninstall entry points used by web/package_installer.py.
"""

from comfyui_nuvu.web.installers.shared import (
    _verify_prerequisites, 
    logger,
    get_pip_base_cmd,
    make_pip_install_cmd,
    make_pip_uninstall_cmd,
    make_pip_show_cmd,
    # Pending uninstall marker system (for file lock handling)
    create_pending_uninstall_marker,
    remove_pending_uninstall_marker,
    has_pending_uninstall,
    get_pending_uninstall_packages,
    is_file_lock_error,
    is_record_file_error,
    is_uninstall_blocked_error,
    # Pending install marker system (for locked file upgrades)
    is_install_blocked_error,
    create_pending_install_marker,
    get_all_pending_installs,
    clear_pending_installs,
)

from comfyui_nuvu.web.installers.pytorch_installer import install_pytorch, reinstall_custom_nodes
from comfyui_nuvu.web.installers.sageattention_installer import install_sageattention, uninstall_sageattention
from comfyui_nuvu.web.installers.onnxruntime_installer import install_onnxruntime_gpu, uninstall_onnxruntime_gpu
from comfyui_nuvu.web.installers.triton_installer import install_triton_windows, uninstall_triton_windows
from comfyui_nuvu.web.installers.cuda_installer import install_cuda_toolkit
from comfyui_nuvu.web.installers.vs_build_tools_installer import install_vs_build_tools, open_vs_build_shell

__all__ = [
    # Shared utilities
    '_verify_prerequisites',
    'logger',
    'get_pip_base_cmd',
    'make_pip_install_cmd',
    'make_pip_uninstall_cmd',
    'make_pip_show_cmd',
    # Pending uninstall marker system
    'create_pending_uninstall_marker',
    'remove_pending_uninstall_marker',
    'has_pending_uninstall',
    'get_pending_uninstall_packages',
    'is_file_lock_error',
    'is_record_file_error',
    'is_uninstall_blocked_error',
    # Pending install marker system
    'is_install_blocked_error',
    'create_pending_install_marker',
    'get_all_pending_installs',
    'clear_pending_installs',
    # PyTorch
    'install_pytorch',
    'reinstall_custom_nodes',
    # SageAttention
    'install_sageattention',
    'uninstall_sageattention',
    # ONNX Runtime
    'install_onnxruntime_gpu',
    'uninstall_onnxruntime_gpu',
    # Triton
    'install_triton_windows',
    'uninstall_triton_windows',
    # CUDA
    'install_cuda_toolkit',
    # VS Build Tools
    'install_vs_build_tools',
    'open_vs_build_shell',
]





