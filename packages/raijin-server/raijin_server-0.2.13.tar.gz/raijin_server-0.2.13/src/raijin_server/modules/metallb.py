"""Provisiona MetalLB (L2) com pool de IPs para LoadBalancer em ambientes bare metal."""

import typer

from raijin_server.utils import ExecutionContext, helm_upgrade_install, require_root, run_cmd


def _rollout_wait(kind: str, name: str, ctx: ExecutionContext) -> None:
    run_cmd([
        "kubectl",
        "-n",
        "metallb-system",
        "rollout",
        "status",
        f"{kind}/{name}",
        "--timeout",
        "180s",
    ], ctx, check=False)


def _wait_webhook(ctx: ExecutionContext) -> None:
    # Descobre o nome do deployment do webhook (varia conforme chart), entao aguarda disponibilidade
    result = run_cmd(
        [
            "kubectl",
            "-n",
            "metallb-system",
            "get",
            "deploy",
            "-l",
            "app.kubernetes.io/component=webhook",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ],
        ctx,
        check=False,
    )
    if result.returncode == 0:
        name = (result.stdout or "").strip()
        if name:
            _rollout_wait("deployment", name, ctx)


def run(ctx: ExecutionContext) -> None:
    require_root(ctx)
    typer.echo("Instalando MetalLB via Helm...")

    pool = typer.prompt(
        "Pool de IPs (range ou CIDR) para services LoadBalancer",
        default="192.168.1.240-192.168.1.250",
    )

    # Instala control-plane + speaker
    helm_upgrade_install(
        release="metallb",
        chart="metallb",
        namespace="metallb-system",
        repo="metallb",
        repo_url="https://metallb.github.io/metallb",
        ctx=ctx,
        values=[],
    )

    # Espera recursos principais ficarem prontos
    _rollout_wait("deployment", "controller", ctx)
    _rollout_wait("daemonset", "speaker", ctx)
    _wait_webhook(ctx)
    run_cmd(["sleep", "5"], ctx, check=False)  # pequeno buffer para webhook responder

    # Aplica IPAddressPool + L2Advertisement
    manifest = f"""
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: raijin-pool
  namespace: metallb-system
spec:
  addresses:
    - {pool}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: raijin-l2
  namespace: metallb-system
spec:
  ipAddressPools:
    - raijin-pool
"""

    run_cmd(
        f"echo '{manifest}' | kubectl apply -f -",
        ctx,
        use_shell=True,
    )

    typer.secho("\n✓ MetalLB aplicado. Services LoadBalancer usarao o pool informado.", fg=typer.colors.GREEN, bold=True)
