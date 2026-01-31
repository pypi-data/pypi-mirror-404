"""
Circle Drawing Classifier for CatLLM

A simplified interface for classifying circle drawings using a fine-tuned DINOv2 model.
This module integrates with the catllm ecosystem as a standalone function.

Usage:
    from catllm.circle_classifier import classify_circles
    
    # LOCAL: Auto-downloads model and runs on your machine
    results = classify_circles(images="./test_images")
    
    # CLOUD: Runs on HuggingFace Inference API (no download needed)
    results = classify_circles(images="./test_images", use_api=True)
"""

import json
import os
import base64
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from io import BytesIO

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

from transformers import Dinov2Model
from peft import LoraConfig, get_peft_model
from huggingface_hub import hf_hub_download, InferenceClient, try_to_load_from_cache


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_HF_MODEL = "chrissoria/circle-classifier"  # Your HuggingFace repo
MODEL_FILENAME = "final_model.pt"
MODEL_SIZE_MB = 350  # Approximate size for user info


# =============================================================================
# CONFIGURATION
# =============================================================================

DIMENSIONS = {
    "presence": {
        "categories": ["circle", "no_circle"],
        "short_names": {"circle": "circle", "no_circle": "no_circle"},
    },
    "closure": {
        "categories": ["closed", "not_closed", "na"],
        "short_names": {"closed": "closed", "not_closed": "not_closed", "na": "na"},
    },
    "circularity": {
        "categories": ["circular", "not_circular", "na"],
        "short_names": {"circular": "circular", "not_circular": "not_circular", "na": "na"},
    },
}

EMBEDDING_DIM = 768  # DINOv2 ViT-B/14 hidden size


# =============================================================================
# MODEL (minimal version for inference only)
# =============================================================================

class _CircleClassifier(nn.Module):
    """DINOv2 multi-head classifier for circle analysis."""

    def __init__(self, dropout: float = 0.5):
        super().__init__()
        self.backbone = Dinov2Model.from_pretrained("facebook/dinov2-base")
        hidden_size = self.backbone.config.hidden_size

        self.classifiers = nn.ModuleDict({
            dim: nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden_size, len(cfg["categories"])))
            for dim, cfg in DIMENSIONS.items()
        })

    def forward(self, pixel_values: torch.Tensor, return_embeddings: bool = False) -> Dict[str, torch.Tensor]:
        features = self.backbone(pixel_values).last_hidden_state[:, 0]  # [batch, 768]
        logits = {dim: head(features) for dim, head in self.classifiers.items()}

        if return_embeddings:
            logits["_embeddings"] = features

        return logits


def _load_model(model: str, device: torch.device, silent: bool = False) -> nn.Module:
    """
    Load trained model from local path or Hugging Face Hub.
    
    Args:
        model: Either a local file path (.pt) or HuggingFace model ID (e.g., "chrissoria/circle-classifier")
        device: Torch device
        silent: If True, suppress download messages
    
    Returns:
        Loaded model ready for inference
    """
    # Determine if it's a local path or HuggingFace model ID
    model_path = Path(model)
    
    if model_path.exists() and model_path.is_file():
        # Local file path
        checkpoint_path = str(model_path)
        if not silent:
            print(f"Loading model from: {checkpoint_path}")
    else:
        # Check if already cached
        cached_path = try_to_load_from_cache(
            repo_id=model,
            filename=MODEL_FILENAME,
        )
        
        if cached_path is not None:
            # Model is already cached
            checkpoint_path = cached_path
            if not silent:
                print(f"Loading model from cache: {model}")
        else:
            # Need to download
            if not silent:
                print(f"\n{'='*60}")
                print(f"CIRCLE CLASSIFIER - First-Time Model Download")
                print(f"{'='*60}")
                print(f"Model:       {model}")
                print(f"Size:        ~{MODEL_SIZE_MB} MB (one-time download)")
                print(f"Cache:       ~/.cache/huggingface/")
                print(f"")
                print(f"Architecture: 1 model with 3 classification heads")
                print(f"  • DINOv2 backbone (shared feature extractor)")
                print(f"  • Presence head  → circle | no_circle")
                print(f"  • Closure head   → closed | not_closed | na")
                print(f"  • Circularity    → circular | not_circular | na")
                print(f"{'='*60}")
                print(f"Downloading...\n")
            
            try:
                checkpoint_path = hf_hub_download(
                    repo_id=model,
                    filename=MODEL_FILENAME,
                    cache_dir=None,  # Uses default HF cache (~/.cache/huggingface)
                )
                if not silent:
                    print(f"\n✓ Download complete! Model cached for future use.\n")
            except Exception as e:
                raise ValueError(
                    f"\nCould not download model '{model}'.\n"
                    f"Ensure it's a valid HuggingFace model ID or local file path.\n"
                    f"Error: {e}"
                )
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    classifier = _CircleClassifier(dropout=0.5)
    
    # Apply LoRA if used during training
    if "lora_r" in checkpoint:
        for param in classifier.backbone.parameters():
            param.requires_grad = True
        lora_config = LoraConfig(
            r=checkpoint["lora_r"],
            lora_alpha=checkpoint["lora_alpha"],
            target_modules=["query", "value"],
            lora_dropout=0.1,
            bias="none",
        )
        classifier.backbone = get_peft_model(classifier.backbone, lora_config)
    
    classifier.load_state_dict(checkpoint["model_state_dict"])
    classifier.to(device)
    classifier.eval()
    return classifier


# =============================================================================
# TRANSFORMS
# =============================================================================

def _get_transforms(image_size: int = 224):
    """Standard inference transforms."""
    return transforms.Compose([
        transforms.Resize(int(image_size * 1.14)),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def _get_tta_transforms(image_size: int = 224):
    """Test-time augmentation transforms."""
    base = transforms.Compose([
        transforms.Resize(int(image_size * 1.14)),
        transforms.CenterCrop(image_size),
    ])
    flip = transforms.Compose([
        transforms.Resize(int(image_size * 1.14)),
        transforms.CenterCrop(image_size),
        transforms.RandomHorizontalFlip(p=1.0),
    ])
    normalize = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return base, flip, normalize


# =============================================================================
# API INFERENCE (Cloud)
# =============================================================================

def _encode_image(image_path: str) -> str:
    """Encode image to base64 for API transmission."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _predict_via_api(
    image_paths: List[Path],
    model: str,
    hf_token: Optional[str],
    show_progress: bool,
) -> List[Dict[str, Any]]:
    """
    Classify images using HuggingFace Inference API.
    
    Requires the model to be deployed as an Inference Endpoint on HuggingFace.
    """
    # Get token from parameter or environment
    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError(
            "HuggingFace API token required for cloud inference.\n"
            "Either pass hf_token parameter or set HF_TOKEN environment variable.\n"
            "Get your token at: https://huggingface.co/settings/tokens"
        )
    
    # Initialize client
    client = InferenceClient(model=model, token=token)
    
    results = []
    iterator = tqdm(image_paths, desc="Classifying (API)") if show_progress else image_paths
    
    for img_path in iterator:
        try:
            # Read image bytes
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            
            # Call inference API
            response = client.post(
                json={
                    "inputs": base64.b64encode(image_bytes).decode("utf-8"),
                    "parameters": {}
                }
            )
            
            # Parse response (format depends on your inference handler)
            if isinstance(response, bytes):
                response = json.loads(response.decode("utf-8"))
            
            # Map response to our standard format
            results.append({
                "image": img_path.name,
                **response
            })
            
        except Exception as e:
            print(f"Warning: Failed to classify {img_path.name}: {e}")
            results.append({
                "image": img_path.name,
                "error": str(e)
            })
    
    return results


def _format_api_response(
    raw_results: List[Dict[str, Any]],
    output_format: str,
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """Format API response to match local inference output."""
    if output_format == "json":
        return raw_results
    
    # Convert to DataFrame format
    rows = []
    for result in raw_results:
        if "error" in result:
            row = {"image": result["image"]}
            # Fill with NaN for error cases
            for dim in ["presence", "closure", "circularity"]:
                for short in DIMENSIONS[dim]["short_names"].values():
                    row[f"{dim}_{short}"] = None
                row[f"{dim}_pred"] = "error"
            rows.append(row)
        else:
            row = {"image": result["image"]}
            for dim in ["presence", "closure", "circularity"]:
                if dim in result:
                    for key, value in result[dim].items():
                        if key != "prediction":
                            row[f"{dim}_{key}"] = value
                    row[f"{dim}_pred"] = result[dim].get("prediction", "")
            rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Order columns
    cols = ["image"]
    for dim in ["presence", "closure", "circularity"]:
        for short in DIMENSIONS[dim]["short_names"].values():
            cols.append(f"{dim}_{short}")
        cols.append(f"{dim}_pred")
    
    return df[[c for c in cols if c in df.columns]]


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def classify_circles(
    images: Union[str, Path, List[str]],
    model: str = DEFAULT_HF_MODEL,
    output_format: str = "dataframe",
    output_path: Optional[str] = None,
    use_tta: bool = True,
    device: Optional[str] = None,
    show_progress: bool = True,
    use_api: bool = False,
    hf_token: Optional[str] = None,
    silent: bool = False,
    return_embeddings: bool = False,
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Classify circle drawings along three dimensions: presence, closure, circularity.
    
    This function uses a SINGLE model with THREE classification heads:
        - One shared DINOv2 backbone (~340 MB)
        - Three small classification heads (~3 KB each)
        - Total download size: ~350 MB (one-time, cached locally)
    
    Supports two modes:
        - LOCAL (default): Downloads model to your machine, runs inference locally
        - CLOUD (use_api=True): Sends images to HuggingFace Inference API
    
    Args:
        images: Path to image directory, single image path, or list of image paths
        model: HuggingFace model ID or local path to checkpoint (.pt file)
               Default: "chrissoria/circle-classifier"
        output_format: "dataframe" (default) or "json"
        output_path: Optional path to save results (CSV or JSON based on format)
        use_tta: Use test-time augmentation for better accuracy (default True, local only)
        device: "cuda", "mps", "cpu", or None for auto-detect (local only)
        show_progress: Show progress bar (default True)
        use_api: If True, use HuggingFace Inference API instead of local inference
        hf_token: HuggingFace API token (required for use_api=True, or set HF_TOKEN env var)
        silent: If True, suppress download/loading messages (default False)
        return_embeddings: If True, include 768-dim DINOv2 embeddings in output (local only)
                          Embeddings are the visual feature vectors before classification heads.
                          Useful for downstream ML tasks (e.g., dementia prediction models).

    Returns:
        DataFrame or list of dicts with predictions and probabilities for all 3 dimensions.
        If return_embeddings=True, includes columns emb_0 through emb_767 (DataFrame) or
        "_embeddings" key with numpy array (JSON format).
    
    Example:
        >>> from catllm.circle_classifier import classify_circles
        >>> 
        >>> # === LOCAL MODE (default) ===
        >>> # First run: downloads ~350MB model (cached for future runs)
        >>> results = classify_circles(images="./test_images")
        >>> 
        >>> # Use a local model file
        >>> results = classify_circles(
        ...     images="./test_images",
        ...     model="./checkpoints/final_model.pt"
        ... )
        >>> 
        >>> # === CLOUD MODE ===
        >>> # Run on HuggingFace servers (no download needed)
        >>> results = classify_circles(
        ...     images="./test_images",
        ...     use_api=True,
        ...     hf_token="hf_..."  # or set HF_TOKEN env var
        ... )
        >>> 
        >>> # === OUTPUT OPTIONS ===
        >>> # Get JSON output and save to file
        >>> results = classify_circles(
        ...     images="./test_images",
        ...     output_format="json",
        ...     output_path="results.json"
        ... )
        >>> 
        >>> # Suppress download messages
        >>> results = classify_circles(images="./test_images", silent=True)
        >>> 
        >>> # Filter uncertain predictions
        >>> uncertain = results[results["presence_circle"] < 0.7]
        >>>
        >>> # === EMBEDDINGS MODE ===
        >>> # Get 768-dim feature vectors for downstream ML
        >>> results = classify_circles(
        ...     images="./test_images",
        ...     return_embeddings=True
        ... )
        >>> # Embedding columns: emb_0, emb_1, ..., emb_767
        >>> embedding_cols = [c for c in results.columns if c.startswith("emb_")]
        >>> X = results[embedding_cols].values  # Use as features for another model
    
    Output columns (DataFrame):
        - image: filename
        - presence_circle, presence_no_circle: probabilities
        - presence_pred: predicted category
        - closure_closed, closure_not_closed, closure_na: probabilities
        - closure_pred: predicted category
        - circularity_circular, circularity_not_circular, circularity_na: probabilities
        - circularity_pred: predicted category
        - emb_0 through emb_767: embedding values (if return_embeddings=True)
    
    Notes:
        MODEL ARCHITECTURE:
            This downloads ONE model file containing:
            - Shared DINOv2 backbone (feature extractor)
            - 3 classification heads (one per dimension)
            All 3 predictions come from a single forward pass.
        
        LOCAL mode:
            - First run downloads ~350MB model (cached for future runs)
            - Faster if you have a GPU
            - Works offline after first download
        
        CLOUD mode:
            - No download required
            - Works without GPU
            - Requires HuggingFace token and internet connection
            - Model must be deployed as Inference Endpoint on HuggingFace
    """
    # Collect image paths first (same for both modes)
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff"}
    
    if isinstance(images, (str, Path)):
        path = Path(images)
        if path.is_dir():
            image_paths = sorted([p for p in path.iterdir() if p.suffix.lower() in image_extensions])
        elif path.is_file():
            image_paths = [path]
        else:
            raise FileNotFoundError(f"Path not found: {images}")
    else:
        image_paths = [Path(p) for p in images]
    
    if not image_paths:
        raise ValueError("No valid images found")
    
    # === CLOUD MODE ===
    if use_api:
        raw_results = _predict_via_api(image_paths, model, hf_token, show_progress)
        results = _format_api_response(raw_results, output_format)
        
        # Save if requested
        if output_path:
            if output_format == "json":
                with open(output_path, "w") as f:
                    json.dump(results, f, indent=2)
            else:
                results.to_csv(output_path, index=False)
        
        return results
    
    # === LOCAL MODE ===
    if device is None:
        # Auto-detect best device: CUDA > MPS > CPU
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    device = torch.device(device)
    
    # Load model (from HuggingFace or local path)
    loaded_model = _load_model(model, device, silent=silent)
    
    # Classify
    results = []
    iterator = tqdm(image_paths, desc="Classifying") if show_progress else image_paths
    
    for img_path in iterator:
        preds = _predict_single(loaded_model, str(img_path), device, use_tta, return_embeddings)

        # Extract embeddings if present
        embeddings = preds.pop("_embeddings", None) if return_embeddings else None

        if output_format == "json":
            record = {"image": img_path.name}
            for dim, probs in preds.items():
                short_names = DIMENSIONS[dim]["short_names"]
                record[dim] = {
                    short_names[cat]: round(prob, 4) for cat, prob in probs.items()
                }
                record[dim]["prediction"] = max(probs, key=probs.get)
            if embeddings is not None:
                record["_embeddings"] = embeddings.tolist()
            results.append(record)
        else:
            row = {"image": img_path.name}
            for dim, probs in preds.items():
                short_names = DIMENSIONS[dim]["short_names"]
                for cat, prob in probs.items():
                    row[f"{dim}_{short_names[cat]}"] = round(prob, 4)
                row[f"{dim}_pred"] = max(probs, key=probs.get)
            if embeddings is not None:
                for i, val in enumerate(embeddings):
                    row[f"emb_{i}"] = round(float(val), 6)
            results.append(row)
    
    # Format output
    if output_format == "json":
        if output_path:
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
        return results
    else:
        df = pd.DataFrame(results)
        # Order columns
        cols = ["image"]
        for dim in ["presence", "closure", "circularity"]:
            for short in DIMENSIONS[dim]["short_names"].values():
                cols.append(f"{dim}_{short}")
            cols.append(f"{dim}_pred")
        df = df[[c for c in cols if c in df.columns]]
        
        if output_path:
            df.to_csv(output_path, index=False)
        return df


def _predict_single(
    model: nn.Module,
    image_path: str,
    device: torch.device,
    use_tta: bool,
    return_embeddings: bool = False,
) -> Dict[str, Any]:
    """Predict for single image, optionally returning embeddings."""
    image = Image.open(image_path).convert("RGB")

    if use_tta:
        base, flip, normalize = _get_tta_transforms()
        all_logits = {dim: [] for dim in DIMENSIONS}
        all_embeddings = []

        with torch.no_grad():
            for tfm in [base, flip]:
                img = normalize(tfm(image)).unsqueeze(0).to(device)
                logits = model(img, return_embeddings=return_embeddings)
                for dim in DIMENSIONS:
                    all_logits[dim].append(logits[dim])
                if return_embeddings:
                    all_embeddings.append(logits["_embeddings"])

        avg_logits = {dim: torch.stack(all_logits[dim]).mean(0) for dim in DIMENSIONS}
        if return_embeddings:
            avg_embeddings = torch.stack(all_embeddings).mean(0)
    else:
        transform = _get_transforms()
        img = transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            avg_logits = model(img, return_embeddings=return_embeddings)
        if return_embeddings:
            avg_embeddings = avg_logits.pop("_embeddings")

    # Convert to probabilities
    results = {}
    for dim, cfg in DIMENSIONS.items():
        probs = F.softmax(avg_logits[dim], dim=1).squeeze()
        results[dim] = {cat: probs[i].item() for i, cat in enumerate(cfg["categories"])}

    if return_embeddings:
        results["_embeddings"] = avg_embeddings.squeeze().cpu().numpy()

    return results


# =============================================================================
# HUGGINGFACE HUB UTILITIES
# =============================================================================

def upload_model_to_hub(
    model_path: str,
    repo_id: str,
    token: Optional[str] = None,
    private: bool = False,
    commit_message: str = "Upload circle classifier model",
    include_inference_handler: bool = True,
) -> str:
    """
    Upload a trained model to Hugging Face Hub.
    
    Args:
        model_path: Local path to the trained model (.pt file)
        repo_id: HuggingFace repo ID (e.g., "chrissoria/circle-classifier")
        token: HuggingFace API token (uses cached token if None)
        private: Whether to make the repo private
        commit_message: Commit message for the upload
        include_inference_handler: If True, also upload handler.py for Inference API
    
    Returns:
        URL of the uploaded model
    
    Example:
        >>> from catllm.circle_classifier import upload_model_to_hub
        >>> 
        >>> url = upload_model_to_hub(
        ...     model_path="./checkpoints/final_model.pt",
        ...     repo_id="chrissoria/circle-classifier",
        ...     token="hf_..."  # or run `huggingface-cli login` first
        ... )
        >>> print(f"Model uploaded to: {url}")
    
    Notes:
        To enable cloud inference (use_api=True), you need to:
        1. Upload the model with include_inference_handler=True
        2. Go to huggingface.co/{repo_id} → Settings → Inference Endpoints
        3. Deploy as an Inference Endpoint (may require paid plan for custom models)
    """
    from huggingface_hub import HfApi, create_repo
    
    api = HfApi(token=token)
    
    # Create repo if it doesn't exist
    try:
        create_repo(repo_id, token=token, private=private, exist_ok=True)
    except Exception as e:
        print(f"Note: {e}")
    
    # Upload the model file
    api.upload_file(
        path_or_fileobj=model_path,
        path_in_repo=MODEL_FILENAME,
        repo_id=repo_id,
        commit_message=commit_message,
    )
    
    # Upload inference handler if requested
    if include_inference_handler:
        handler_code = _generate_inference_handler()
        api.upload_file(
            path_or_fileobj=handler_code.encode("utf-8"),
            path_in_repo="handler.py",
            repo_id=repo_id,
            commit_message="Add inference handler for API",
        )
        
        # Upload requirements
        requirements = "torch>=2.0.0\ntorchvision>=0.15.0\ntransformers>=4.35.0\npeft>=0.7.0\nPillow>=9.0.0"
        api.upload_file(
            path_or_fileobj=requirements.encode("utf-8"),
            path_in_repo="requirements.txt",
            repo_id=repo_id,
            commit_message="Add requirements for inference",
        )
    
    url = f"https://huggingface.co/{repo_id}"
    print(f"Model uploaded successfully to: {url}")
    
    if include_inference_handler:
        print("\nTo enable cloud inference (use_api=True):")
        print(f"  1. Go to {url}/settings")
        print("  2. Navigate to 'Inference Endpoints'")
        print("  3. Deploy the model")
    
    return url


def _generate_inference_handler() -> str:
    """Generate the handler.py for HuggingFace Inference Endpoints."""
    return '''"""
Inference handler for HuggingFace Inference Endpoints.
"""

import base64
import json
from io import BytesIO
from typing import Dict, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from transformers import Dinov2Model
from peft import LoraConfig, get_peft_model


DIMENSIONS = {
    "presence": {
        "categories": ["circle", "no_circle"],
        "short_names": {"circle": "circle", "no_circle": "no_circle"},
    },
    "closure": {
        "categories": ["closed", "not_closed", "na"],
        "short_names": {"closed": "closed", "not_closed": "not_closed", "na": "na"},
    },
    "circularity": {
        "categories": ["circular", "not_circular", "na"],
        "short_names": {"circular": "circular", "not_circular": "not_circular", "na": "na"},
    },
}


class CircleClassifier(nn.Module):
    def __init__(self, dropout: float = 0.5):
        super().__init__()
        self.backbone = Dinov2Model.from_pretrained("facebook/dinov2-base")
        hidden_size = self.backbone.config.hidden_size
        self.classifiers = nn.ModuleDict({
            dim: nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden_size, len(cfg["categories"])))
            for dim, cfg in DIMENSIONS.items()
        })
    
    def forward(self, pixel_values):
        features = self.backbone(pixel_values).last_hidden_state[:, 0]
        return {dim: head(features) for dim, head in self.classifiers.items()}


class EndpointHandler:
    def __init__(self, path: str = ""):
        # Auto-detect best device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        
        # Load model
        checkpoint = torch.load(f"{path}/final_model.pt", map_location=self.device)
        self.model = CircleClassifier(dropout=0.5)
        
        if "lora_r" in checkpoint:
            for param in self.model.backbone.parameters():
                param.requires_grad = True
            lora_config = LoraConfig(
                r=checkpoint["lora_r"],
                lora_alpha=checkpoint["lora_alpha"],
                target_modules=["query", "value"],
                lora_dropout=0.1,
                bias="none",
            )
            self.model.backbone = get_peft_model(self.model.backbone, lora_config)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        
        # Transform
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        inputs = data.get("inputs", "")
        
        # Decode base64 image
        image_bytes = base64.b64decode(inputs)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        # Transform and predict
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(img_tensor)
        
        # Format results
        results = {}
        for dim, cfg in DIMENSIONS.items():
            probs = F.softmax(logits[dim], dim=1).squeeze()
            short_names = cfg["short_names"]
            results[dim] = {
                short_names[cat]: round(probs[i].item(), 4)
                for i, cat in enumerate(cfg["categories"])
            }
            results[dim]["prediction"] = cfg["categories"][probs.argmax().item()]
        
        return results
'''


__all__ = ["classify_circles", "upload_model_to_hub"]
