"""Configuracao do Traefik via Helm com TLS/ACME e ingressClass."""

import socket

import typer

from raijin_server.utils import ExecutionContext, helm_upgrade_install, require_root, run_cmd


def _detect_node_name(ctx: ExecutionContext) -> str:
    """Tenta obter o nome do node via kubectl; fallback para hostname local.

    Em execucao no control-plane, o nome do node retornado pelo kubeadm init e o desejado
    para o nodeSelector (kubernetes.io/hostname)."""

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


def run(ctx: ExecutionContext) -> None:
    require_root(ctx)
    typer.echo("Instalando Traefik via Helm...")

    acme_email = typer.prompt("Email para ACME/Let's Encrypt", default="admin@example.com")
    dashboard_host = typer.prompt("Host para dashboard (opcional)", default="traefik.local")

    node_name = _detect_node_name(ctx)

    values = [
        "ingressClass.enabled=true",
        "ingressClass.isDefaultClass=true",
        "service.type=LoadBalancer",
        f"certificatesResolvers.letsencrypt.acme.email={acme_email}",
        "certificatesResolvers.letsencrypt.acme.storage=/data/acme.json",
        "certificatesResolvers.letsencrypt.acme.httpChallenge.entryPoint=web",
        "logs.general.level=INFO",
        "providers.kubernetesIngress.ingressClass=traefik",
        # Permite agendar em control-plane de cluster single-node
        "tolerations[0].key=node-role.kubernetes.io/control-plane",
        "tolerations[0].operator=Exists",
        "tolerations[0].effect=NoSchedule",
        "tolerations[1].key=node-role.kubernetes.io/master",
        "tolerations[1].operator=Exists",
        "tolerations[1].effect=NoSchedule",
        f"nodeSelector.kubernetes.io/hostname={node_name}",
    ]

    if dashboard_host:
        values.append("ingressRoute.dashboard.enabled=true")
        values.append(f"ingressRoute.dashboard.match=Host(`{dashboard_host}`)")

    helm_upgrade_install(
        release="traefik",
        chart="traefik",
        namespace="traefik",
        repo="traefik",
        repo_url="https://traefik.github.io/charts",
        ctx=ctx,
        values=values,
    )
