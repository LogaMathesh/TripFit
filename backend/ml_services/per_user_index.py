import os
import json
import faiss
import numpy as np
from ml_services.clip_embed_utils import embed_image, embed_text

# -----------------------------
# CONFIG
# -----------------------------
INDEX_DIR = "indexes"
os.makedirs(INDEX_DIR, exist_ok=True)

FAISS_DIM = 768   # CLIP ViT-Large Patch-14 outputs 1024-dim vectors


# -----------------------------
# PATH HELPERS
# -----------------------------
def _user_paths(user_id):
    """Get file paths for user's index and metadata"""
    idx_path = os.path.join(INDEX_DIR, f"{user_id}.index")
    meta_path = os.path.join(INDEX_DIR, f"{user_id}_meta.json")
    return idx_path, meta_path


# -----------------------------
# INDEX MANAGEMENT
# -----------------------------
def _create_new_index():
    """Create new FAISS index with correct CLIP dimension"""
    return faiss.IndexIDMap(faiss.IndexFlatIP(FAISS_DIM))


def load_user_index(user_id):
    """Load FAISS index + metadata; create new if missing"""
    idx_path, meta_path = _user_paths(user_id)

    # Existing index
    if os.path.exists(idx_path) and os.path.exists(meta_path):
        idx = faiss.read_index(idx_path)
        meta = json.load(open(meta_path))
        return idx, meta

    # Create new index
    idx = _create_new_index()
    meta = {"_next_id": 1, "items": {}}

    faiss.write_index(idx, idx_path)
    json.dump(meta, open(meta_path, "w"))

    return idx, meta


def save_user_index(user_id, idx, meta):
    """Persist FAISS index + metadata"""
    idx_path, meta_path = _user_paths(user_id)
    faiss.write_index(idx, idx_path)
    json.dump(meta, open(meta_path, "w"))


# -----------------------------
# ADD IMAGE TO INDEX
# -----------------------------
def add_image_for_user(user_id, image_path, style=None, color=None):
    """Add image embedding to user's FAISS index"""

    # Ensure absolute path
    abs_path = os.path.abspath(image_path)

    # Load index + metadata
    idx, meta = load_user_index(user_id)

    # Prevent duplicates
    for item_id, item_data in meta["items"].items():
        if item_data["path"] == abs_path:
            print(f"Image already indexed: {abs_path}")
            return int(item_id)

    # Generate CLIP embedding
    vec = embed_image(abs_path)
    if vec is None:
        print("❌ embed_image returned None")
        return None

    # Safety check: dimension must be 1024
    if vec.shape[0] != FAISS_DIM:
        print(f"❌ ERROR: Embedding dim {vec.shape[0]} != {FAISS_DIM}")
        return None

    # New vector ID
    nid = meta["_next_id"]

    # Add vector + id to FAISS index
    idx.add_with_ids(
        np.array([vec], dtype="float32"),
        np.array([nid], dtype="int64")
    )

    # Save metadata
    meta["items"][str(nid)] = {
        "path": abs_path,
        "style": style,
        "color": color
    }

    # Increment next id
    meta["_next_id"] = nid + 1

    # Save changes
    save_user_index(user_id, idx, meta)

    print(f"Indexed new image: {abs_path} with ID {nid}")
    print("Vector shape:", vec.shape)
    return nid


# -----------------------------
# QUERY USER IMAGES
# -----------------------------
def query_user(user_id, text_query, top_k=3):
    """Return images similar to text query"""

    vec = embed_text(text_query)
    if vec is None:
        print("❌ embed_text returned None")
        return []

    if vec.shape[0] != FAISS_DIM:
        print(f"❌ ERROR: Text embedding dim {vec.shape[0]} != {FAISS_DIM}")
        return []

    idx, meta = load_user_index(user_id)

    if idx.ntotal == 0:
        print(f"No images indexed for user {user_id}")
        return []

    # Search for similarity
    search_k = min(top_k * 2, idx.ntotal)
    D, I = idx.search(np.array([vec], dtype="float32"), search_k)

    results = []
    seen_paths = set()

    for dist, rid in zip(D[0], I[0]):
        rid = int(rid)
        if rid == -1:
            continue

        item = meta["items"].get(str(rid))
        if not item:
            continue

        # avoid duplicates
        if item["path"] in seen_paths:
            continue

        seen_paths.add(item["path"])

        results.append({
            "score": float(dist),
            "path": item["path"],
            "style": item.get("style", "Unknown"),
            "color": item.get("color", "Unknown")
        })

        if len(results) >= top_k:
            break

    return results
