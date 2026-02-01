"""Provisiona MetalLB (L2) com pool de IPs para LoadBalancer em ambientes bare metal."""

import socket

import typer

from raijin_server.utils import ExecutionContext, helm_upgrade_install, require_root, run_cmd


def _detect_node_name(ctx: ExecutionContext) -> str:
    """Tenta obter o nome do node via kubectl; fallback para hostname local."""

    result = run_cmd(
        [
            "kubectl",
            "get",
            "nodes",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ],
        ctx,
        check=False,
    )
    if result.returncode == 0:
        node_name = (result.stdout or "").strip()
        if node_name:
            return node_name
    return socket.gethostname()


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
        default="192.168.1.100-192.168.1.250",
    )

    node_name = _detect_node_name(ctx)

    values = [
        # Permite agendar em control-plane de cluster single-node
        "controller.tolerations[0].key=node-role.kubernetes.io/control-plane",
        "controller.tolerations[0].operator=Exists",
        "controller.tolerations[0].effect=NoSchedule",
        "controller.tolerations[1].key=node-role.kubernetes.io/master",
        "controller.tolerations[1].operator=Exists",
        "controller.tolerations[1].effect=NoSchedule",
        "speaker.tolerations[0].key=node-role.kubernetes.io/control-plane",
        "speaker.tolerations[0].operator=Exists",
        "speaker.tolerations[0].effect=NoSchedule",
        "speaker.tolerations[1].key=node-role.kubernetes.io/master",
        "speaker.tolerations[1].operator=Exists",
        "speaker.tolerations[1].effect=NoSchedule",
        # Escapa a chave com ponto; evita map literal que quebra o schema do chart
        f"controller.nodeSelector.kubernetes\\.io/hostname={node_name}",
        f"speaker.nodeSelector.kubernetes\\.io/hostname={node_name}",
    ]

    # Instala control-plane + speaker
    helm_upgrade_install(
        release="metallb",
        chart="metallb",
        namespace="metallb-system",
        repo="metallb",
        repo_url="https://metallb.github.io/metallb",
        ctx=ctx,
        values=values,
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
