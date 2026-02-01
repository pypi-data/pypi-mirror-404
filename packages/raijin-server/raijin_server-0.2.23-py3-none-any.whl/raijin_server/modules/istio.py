"""Instalacao do Istio usando istioctl com configuracoes production-ready."""

import socket
import time

import typer

from raijin_server.utils import ExecutionContext, ensure_tool, require_root, run_cmd


ISTIO_PROFILES = ["default", "demo", "minimal", "ambient", "empty"]


def _detect_node_name(ctx: ExecutionContext) -> str:
    """Detecta nome do node para nodeSelector."""
    result = run_cmd(
        ["kubectl", "get", "nodes", "-o", "jsonpath={.items[0].metadata.name}"],
        ctx,
        check=False,
    )
    if result.returncode == 0 and (result.stdout or "").strip():
        return (result.stdout or "").strip()
    return socket.gethostname()


def _check_existing_istio(ctx: ExecutionContext) -> bool:
    """Verifica se existe instalacao do Istio."""
    result = run_cmd(
        ["kubectl", "get", "namespace", "istio-system"],
        ctx,
        check=False,
    )
    return result.returncode == 0


def _uninstall_istio(ctx: ExecutionContext) -> None:
    """Remove instalacao anterior do Istio."""
    typer.echo("Removendo instalacao anterior do Istio...")
    
    run_cmd(
        ["istioctl", "uninstall", "--purge", "-y"],
        ctx,
        check=False,
    )
    
    run_cmd(
        ["kubectl", "delete", "namespace", "istio-system", "--ignore-not-found"],
        ctx,
        check=False,
    )
    
    time.sleep(5)


def _wait_for_istio_ready(ctx: ExecutionContext, timeout: int = 300) -> bool:
    """Aguarda pods do Istio ficarem Ready."""
    typer.echo("Aguardando pods do Istio ficarem Ready...")
    deadline = time.time() + timeout
    
    while time.time() < deadline:
        result = run_cmd(
            [
                "kubectl", "-n", "istio-system", "get", "pods",
                "-o", "jsonpath={range .items[*]}{.metadata.name}={.status.phase} {end}",
            ],
            ctx,
            check=False,
        )
        
        if result.returncode == 0:
            output = (result.stdout or "").strip()
            if output:
                pods = []
                for item in output.split():
                    if "=" in item:
                        parts = item.rsplit("=", 1)
                        if len(parts) == 2:
                            pods.append((parts[0], parts[1]))
                
                if pods and all(phase in ("Running", "Succeeded") for _, phase in pods):
                    typer.secho(f"  Todos os {len(pods)} pods Ready.", fg=typer.colors.GREEN)
                    return True
                
                pending = [name for name, phase in pods if phase not in ("Running", "Succeeded")]
                if pending:
                    typer.echo(f"  Aguardando: {', '.join(pending[:3])}...")
        
        time.sleep(10)
    
    typer.secho("  Timeout aguardando pods do Istio.", fg=typer.colors.YELLOW)
    return False


def run(ctx: ExecutionContext) -> None:
    require_root(ctx)
    ensure_tool("istioctl", ctx, install_hint="Baixe em https://istio.io/latest/docs/setup/getting-started/")
    typer.echo("Instalando Istio...")

    # Prompt opcional de limpeza
    if _check_existing_istio(ctx):
        cleanup = typer.confirm(
            "Instalacao anterior do Istio detectada. Limpar antes de reinstalar?",
            default=False,
        )
        if cleanup:
            _uninstall_istio(ctx)

    # Selecao de perfil
    typer.echo(f"\nPerfis disponiveis: {', '.join(ISTIO_PROFILES)}")
    profile = typer.prompt("Perfil do Istio", default="default")
    if profile not in ISTIO_PROFILES:
        typer.secho(f"Perfil '{profile}' invalido. Usando 'default'.", fg=typer.colors.YELLOW)
        profile = "default"

    node_name = _detect_node_name(ctx)
    
    # Instala com tolerations para control-plane
    # IMPORTANTE: Ao fazer override em arrays do Istio, precisamos especificar o 'name'
    # do componente para que o merge funcione corretamente
    install_cmd = [
        "istioctl", "install",
        "--set", f"profile={profile}",
        # Tolerations para istiod (control plane)
        "--set", "components.pilot.k8s.tolerations[0].key=node-role.kubernetes.io/control-plane",
        "--set", "components.pilot.k8s.tolerations[0].operator=Exists",
        "--set", "components.pilot.k8s.tolerations[0].effect=NoSchedule",
        "--set", "components.pilot.k8s.tolerations[1].key=node-role.kubernetes.io/master",
        "--set", "components.pilot.k8s.tolerations[1].operator=Exists",
        "--set", "components.pilot.k8s.tolerations[1].effect=NoSchedule",
        # NodeSelector para istiod
        "--set", f"components.pilot.k8s.nodeSelector.kubernetes\\.io/hostname={node_name}",
        # Tolerations para ingress gateway (DEVE incluir o name!)
        "--set", "components.ingressGateways[0].name=istio-ingressgateway",
        "--set", "components.ingressGateways[0].enabled=true",
        "--set", "components.ingressGateways[0].k8s.tolerations[0].key=node-role.kubernetes.io/control-plane",
        "--set", "components.ingressGateways[0].k8s.tolerations[0].operator=Exists",
        "--set", "components.ingressGateways[0].k8s.tolerations[0].effect=NoSchedule",
        "--set", "components.ingressGateways[0].k8s.tolerations[1].key=node-role.kubernetes.io/master",
        "--set", "components.ingressGateways[0].k8s.tolerations[1].operator=Exists",
        "--set", "components.ingressGateways[0].k8s.tolerations[1].effect=NoSchedule",
        # NodeSelector para ingress gateway
        "--set", f"components.ingressGateways[0].k8s.nodeSelector.kubernetes\\.io/hostname={node_name}",
        "-y",
    ]
    
    run_cmd(install_cmd, ctx)
    
    # Aguarda pods ficarem prontos
    if not ctx.dry_run:
        _wait_for_istio_ready(ctx)
    
    # Pergunta sobre injection
    enable_injection = typer.confirm(
        "Habilitar sidecar injection automatico no namespace 'default'?",
        default=True,
    )
    if enable_injection:
        run_cmd(
            ["kubectl", "label", "namespace", "default", "istio-injection=enabled", "--overwrite"],
            ctx,
        )
    
    typer.secho("\n✓ Istio instalado com sucesso.", fg=typer.colors.GREEN, bold=True)
