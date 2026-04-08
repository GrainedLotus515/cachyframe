from __future__ import annotations

from pathlib import Path


def render_launch_env(
    prefix_dir: Path,
    proxy_host: str,
    proxy_port: int,
    cert_path: Path,
) -> dict[str, str]:
    return {
        "WINEPREFIX": str(prefix_dir),
        "HTTP_PROXY": f"http://{proxy_host}:{proxy_port}",
        "HTTPS_PROXY": f"http://{proxy_host}:{proxy_port}",
        "REQUESTS_CA_BUNDLE": str(cert_path),
    }


def render_instructions(prefix_dir: Path, proxy_host: str, proxy_port: int, cert_path: Path) -> str:
    env = render_launch_env(prefix_dir, proxy_host, proxy_port, cert_path)
    lines = [
        "Proton TLS capture setup:",
        f"- Prefix: {prefix_dir}",
        f"- Proxy: {proxy_host}:{proxy_port}",
        f"- CA certificate: {cert_path}",
        "- Export these variables before launching Warframe inside the same prefix:",
    ]
    lines.extend([f"  {key}={value}" for key, value in env.items()])
    return "\n".join(lines)
