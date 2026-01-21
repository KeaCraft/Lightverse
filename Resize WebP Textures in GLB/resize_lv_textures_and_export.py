import bpy
import sys
from pathlib import Path


# ----------------------------
# Core helpers
# ----------------------------

def resize_image(img: bpy.types.Image, max_size: int = 512) -> bool:
    """
    Resize image so that its larger dimension equals max_size (maintain aspect ratio).
    Returns True if resized, False if already within limits or invalid size.
    """
    if not img or not hasattr(img, "size"):
        return False

    width, height = img.size[0], img.size[1]
    if width <= 0 or height <= 0:
        return False

    if width <= max_size and height <= max_size:
        return False

    if width >= height:
        new_width = max_size
        new_height = max(1, int((max_size / width) * height))
    else:
        new_height = max_size
        new_width = max(1, int((max_size / height) * width))

    img.scale(new_width, new_height)
    return True


def get_images_from_material(mat: bpy.types.Material) -> set:
    """Collect all images used by Image Texture nodes in a material's node tree."""
    images = set()
    if not mat or not mat.use_nodes or not mat.node_tree:
        return images

    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and getattr(node, "image", None):
            images.add(node.image)
    return images


def parse_cli_args() -> dict:
    """
    Parse arguments passed after '--' in Blender:
      blender -b -P script.py -- --input ... --output ... --max_size 512
    """
    args = {}
    if "--" not in sys.argv:
        return args

    tail = sys.argv[sys.argv.index("--") + 1:]
    i = 0
    while i < len(tail):
        token = tail[i]
        if token in ("--input", "--output", "--max_size"):
            if i + 1 >= len(tail):
                raise ValueError(f"Missing value for {token}")
            args[token] = tail[i + 1]
            i += 2
        else:
            i += 1
    return args


def log(msg: str) -> None:
    print(msg, flush=True)


# ----------------------------
# Processing
# ----------------------------

def process_model(input_path: Path, output_path: Path, max_size: int) -> None:
    """
    Process a single GLB model:
    - reset Blender to factory empty state (prevents .001/.002 suffixes)
    - import GLB
    - resize textures used by materials starting with 'LV_'
    - export GLB
    """
    log(f"Processing: {input_path}")

    # Hard reset to avoid datablock collisions across files (.001/.002 suffixes)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.context.preferences.edit.use_global_undo = False
    except Exception:
        pass

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=str(input_path))

    # Collect images from LV_ materials
    images_to_resize = set()
    for mat in bpy.data.materials:
        if mat and mat.name.startswith("LV_"):
            images_to_resize.update(get_images_from_material(mat))

    # Resize images
    resized_count = 0
    for img in images_to_resize:
        try:
            w, h = img.size[0], img.size[1]
            if resize_image(img, max_size=max_size):
                resized_count += 1
                log(f"  Resized: {img.name} {w}x{h} -> {img.size[0]}x{img.size[1]}")
            else:
                log(f"  Kept:    {img.name} ({w}x{h})")
        except Exception as e:
            log(f"  Warning: Failed resizing image '{getattr(img, 'name', 'UNKNOWN')}' - {e}")

    log(f"  Textures resized: {resized_count}")

    # Export GLB
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLB",
        export_image_format="AUTO",
    )

    log(f"  Exported: {output_path}")


def main() -> None:
    script_dir = Path(__file__).parent if "__file__" in globals() else Path.cwd()

    # Defaults
    input_dir = script_dir / "input"
    output_dir = script_dir / "output"
    max_size = 512

    # CLI overrides
    cli = parse_cli_args()
    if "--input" in cli:
        input_dir = Path(cli["--input"]).expanduser()
    if "--output" in cli:
        output_dir = Path(cli["--output"]).expanduser()
    if "--max_size" in cli:
        try:
            max_size = int(cli["--max_size"])
            if max_size <= 0:
                raise ValueError
        except Exception:
            raise ValueError(f"Invalid --max_size value: {cli['--max_size']}")

    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    glb_files = sorted(input_dir.rglob("*.glb"))
    if not glb_files:
        log(f"No .glb files found in: {input_dir}")
        return

    log("========================================")
    log("LV GLB Texture Resizer")
    log("========================================")
    log(f"Input : {input_dir}")
    log(f"Output: {output_dir}")
    log(f"Max   : {max_size}px")
    log(f"Files : {len(glb_files)}")
    log("")

    processed = 0
    skipped = 0
    failed = 0

    for glb_file in glb_files:
        rel = glb_file.relative_to(input_dir)
        out_file = output_dir / rel

        # Skip if already exists
        if out_file.exists():
            log(f"Skipping: {rel} (output exists)")
            log("")
            skipped += 1
            continue

        try:
            process_model(glb_file, out_file, max_size=max_size)
            processed += 1
            log("")
        except Exception as e:
            failed += 1
            log(f"ERROR processing {rel}: {e}")
            log("")
            continue

    log("========================================")
    log("Done")
    log("========================================")
    log(f"Processed: {processed}")
    log(f"Skipped  : {skipped}")
    log(f"Failed   : {failed}")


if __name__ == "__main__":
    main()
