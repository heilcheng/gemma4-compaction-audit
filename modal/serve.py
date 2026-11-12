"""vLLM server for Gemma 4 12B QAT on Modal. One container max (allocation rule), scales to zero."""
import subprocess
import modal

MODEL = "google/gemma-4-12B-it-qat-w4a16-ct"
REV = "1d2c2d7f2466070e69d6fb3fd5ce9a7d75f2f6ee"
GPU = "A100-80GB"
PORT = 8000

image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("vllm==0.33.0", "huggingface_hub[hf_transfer]")
         .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/cache", "VLLM_NO_USAGE_STATS": "1", "VLLM_USE_FLASHINFER_SAMPLER": "0"}))
cache = modal.Volume.from_name("kaggle-g4paper-cache", create_if_missing=True)
app = modal.App("kaggle-g4paper-serve")


@app.function(image=image, volumes={"/cache": cache}, timeout=1800)
def fetch():
    from huggingface_hub import snapshot_download
    p = snapshot_download(MODEL, revision=REV)
    cache.commit()
    return p


@app.function(image=image, gpu=GPU, volumes={"/cache": cache}, max_containers=2,
              scaledown_window=300, timeout=6 * 3600)
@modal.concurrent(max_inputs=24)
@modal.web_server(PORT, startup_timeout=900)
def serve():
    subprocess.Popen(["vllm", "serve", MODEL, "--revision", REV, "--served-model-name", "gemma4-12b",
                      "--port", str(PORT), "--max-model-len", "32768", "--enable-prefix-caching",
                      "--gpu-memory-utilization", "0.90", "--max-num-seqs", "16"])
