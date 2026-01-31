import argparse
import asyncio
import sys


def main() -> None:
    """CLI entry point for xm-agent."""
    parser = argparse.ArgumentParser(description="XM Agent - HTTP API for model management")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the HTTP server")
    serve_parser.add_argument("--host", type=str, help="Bind address (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, help="Port number (default: 8765)")

    # dl command
    dl_parser = subparsers.add_parser("dl", help="Download models by CivitAI model IDs")
    dl_parser.add_argument("ids", nargs="+", help="CivitAI model IDs")

    args = parser.parse_args()

    if args.command == "dl":
        asyncio.run(download_models(args.ids))
    elif args.command == "serve" or args.command is None:
        # Override settings from CLI args
        import os

        if args.command == "serve":
            if args.host:
                os.environ["XM_AGENT_HOST"] = args.host
            if args.port:
                os.environ["XM_AGENT_PORT"] = str(args.port)

        from xm_agent.server import run_server

        run_server()
    else:
        parser.print_help()


# Map CivitAI model types to local directories
CIVITAI_TYPE_MAP = {
    "Checkpoint": "checkpoints",
    "LORA": "loras",
    "LoCon": "loras",
    "TextualInversion": "embeddings",
    "VAE": "vae",
    "Controlnet": "controlnet",
}


async def download_models(model_ids: list[str]) -> None:
    """Download models by CivitAI model IDs (latest version)."""
    import httpx
    from xm_agent.config import get_settings
    from xm_agent.download import download_file, DownloadError

    settings = get_settings()
    headers = {}
    if settings.civitai_api_key:
        headers["Authorization"] = f"Bearer {settings.civitai_api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model_id in model_ids:
            print(f"\n[{model_id}] Fetching info...")

            # Get model info (includes all versions)
            try:
                resp = await client.get(
                    f"https://civitai.com/api/v1/models/{model_id}",
                    headers=headers,
                )
                if resp.status_code == 404:
                    print(f"[{model_id}] Not found")
                    continue
                resp.raise_for_status()
                model_data = resp.json()
            except Exception as e:
                print(f"[{model_id}] Failed to fetch info: {e}")
                continue

            # Get latest version
            versions = model_data.get("modelVersions", [])
            if not versions:
                print(f"[{model_id}] No versions available")
                continue

            data = versions[0]  # First is latest

            # Extract info
            model_name = model_data.get("name", "Unknown")
            version_name = data.get("name", "")
            model_type = model_data.get("type", "")
            files = data.get("files", [])

            # Find primary file
            primary = next((f for f in files if f.get("primary")), files[0] if files else None)
            if not primary:
                print(f"[{model_id}] No downloadable file")
                continue

            filename = primary.get("name", f"{model_id}.safetensors")
            download_url = primary.get("downloadUrl") or data.get("downloadUrl")

            if not download_url:
                print(f"[{model_id}] No download URL")
                continue

            # Determine destination directory
            local_type = CIVITAI_TYPE_MAP.get(model_type)
            if not local_type:
                print(f"[{model_id}] Unknown type '{model_type}', skipping")
                continue

            dest_dir = settings.get_model_path(local_type)
            dest_path = dest_dir / filename

            if dest_path.exists():
                print(f"[{model_id}] {filename} already exists, skipping")
                continue

            print(f"[{model_id}] {model_name} - {version_name}")
            print(f"[{model_id}] Type: {model_type} -> {local_type}/")
            print(f"[{model_id}] Downloading {filename}...")

            # Download with progress
            def on_progress(p):
                pct = p.progress_percent or 0
                print(f"\r[{model_id}] {pct}% - {p.speed_str}    ", end="", flush=True)

            try:
                await download_file(download_url, dest_path, on_progress=on_progress)
                print(f"\n[{model_id}] Done: {dest_path}")
            except DownloadError as e:
                print(f"\n[{model_id}] Download failed: {e}")
            except Exception as e:
                print(f"\n[{model_id}] Error: {e}")
