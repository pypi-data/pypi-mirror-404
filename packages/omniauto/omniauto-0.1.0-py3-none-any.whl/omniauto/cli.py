#!/usr/bin/env python3
"""
CLI para OmniAuto.
"""
import sys
import os

# Agregar el directorio del paquete al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click

# Importaciones ABSOLUTAS (no relativas)
from omniauto.core import auto
from omniauto.generator import StubGenerator

@click.group()
@click.version_option()
def cli():
    """OmniAuto - Single Point of Truth dinámico para proyectos Python"""
    pass

@cli.command()
@click.option('--type', '-t', 
              type=click.Choice(['python', 'ai', 'all']),
              default='all',
              help='Tipo de stub a generar')
@click.option('--output', '-o', 
              type=click.Path(),
              help='Ruta de salida personalizada')
def generate(type, output):
    """Genera stubs para IDE o contexto para IA"""
    # NO necesita import aquí, ya está importado arriba
    generator = StubGenerator()
    
    if type in ['python', 'all']:
        out_path = output or "auto_stub.pyi"
        generator.generate_python_stub(out_path)
        click.echo(f"[ok] Stub Python generado en: {out_path}")
    
    if type in ['ai', 'all']:
        out_path = output or ".copilot/omniauto_context.json"
        generator.generate_ai_context(out_path)
        click.echo(f"[ok] Contexto IA generado en: {out_path}")

@cli.command()
@click.option('--category', '-c', help='Filtrar por categoría')
def list(category):
    """Lista funciones registradas"""
    # 'auto' ya está importado arriba, disponible globalmente
    
    funcs = auto.list_functions(category)
    
    if category:
        click.echo(f"Funciones en categoría '{category}':")
        if funcs:
            for func in funcs:
                click.echo(f"  • {func}")
        else:
            click.echo("  (vacío)")
    else:
        click.echo("Funciones registradas por categoría:")
        for cat_name, cat_funcs in funcs.items():
            click.echo(f"\n{cat_name.upper()}:")
            if cat_funcs:
                for func in cat_funcs:
                    click.echo(f"  • {func}")
            else:
                click.echo("  (vacío)")

@cli.command()
def reload():
    """Recarga módulos automáticamente"""
    # 'auto' ya está importado arriba
    auto.reload_modules()
    click.echo("[ok] Módulos recargados")

@cli.command()
@click.argument('path', type=click.Path(exists=True), required=False)
def discover(path):
    """Descubre módulos en una ruta específica"""
    # 'auto' ya está importado arriba
    auto.discover_modules(path)
    if auto._modules:
        click.echo(f"[ok] Módulos descubiertos: {list(auto._modules.keys())}")
    else:
        click.echo("[info] No se encontraron módulos")

def main():
    """Punto de entrada principal"""
    try:
        cli()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())