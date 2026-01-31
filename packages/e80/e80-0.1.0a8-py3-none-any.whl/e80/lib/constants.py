E80_COMMAND = "8080"

E80_VERSION = "0.1.0a8"

E80_HTTP_CUDA_PACKAGES = """
# These should match the requirements file in the base image.
# requirements_gpu.txt
nvidia-cublas==13.0.0.19
nvidia-cuda-cupti==13.0.48
nvidia-cuda-nvrtc==13.0.48
nvidia-cuda-runtime==13.0.48
nvidia-cudnn-cu13==9.13.0.50
nvidia-cufft==12.0.0.15
nvidia-cufile==1.15.0.42
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.3.29
nvidia-cusparse==12.6.2.49
nvidia-cusparselt-cu13==0.8.0
nvidia-nccl-cu13==2.27.7
nvidia-nvjitlink==13.0.39
nvidia-nvshmem-cu13==3.3.24
nvidia-nvtx==13.0.39
triton==3.5.1
# requirements_torch.txt
torch==2.9.1+cu130
torchaudio==2.9.1+cu130
torchvision==0.24.1+cu130
"""
