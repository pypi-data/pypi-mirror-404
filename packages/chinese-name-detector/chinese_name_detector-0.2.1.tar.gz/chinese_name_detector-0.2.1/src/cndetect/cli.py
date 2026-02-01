import typer
import sys
import os
import json
from pathlib import Path
from typing import Optional, List, Union
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import pandas as pd
import yaml
from . import __version__, detect, detect_batch
from .config import settings, Settings
from .logger import logger, setup_logger

app = typer.Typer(help="Chinese Name Detection Tool", invoke_without_command=True)
console = Console()

def parse_names(names_str: Optional[str]) -> List[str]:
    if not names_str:
        return []
    # 尝试解析为 JSON
    try:
        data = json.loads(names_str)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    
    # 否则按逗号分隔
    return [n.strip() for n in names_str.split(",") if n.strip()]

@app.command()
def single(
    text: str,
    custom_names: Optional[str] = typer.Option(None, "--custom-names", help="Custom surnames (comma-separated or JSON list)"),
    exclude_names: Optional[str] = typer.Option(None, "--exclude-names", help="Excluded surnames (comma-separated or JSON list)"),
    mode: str = typer.Option(None, "--match-mode", "-mm", help="Match mode: overall, component, strict")
):
    """检测单条文本"""
    c_names = parse_names(custom_names) or settings.custom_family_names
    e_names = parse_names(exclude_names) or settings.exclude_family_names
    m_mode = mode or settings.matching.mode
    
    if m_mode not in ["overall", "component", "strict"]:
        console.print(f"[red]❌ Error: Invalid match mode '{m_mode}'. Available modes: overall, component, strict.[/red]")
        sys.exit(1)

    res = detect(text, custom_names=c_names, exclude_names=e_names, mode=m_mode)
    table = Table(title="Detection Result")
    table.add_column("Original Text", style="cyan")
    table.add_column("Has Chinese", style="magenta")
    table.add_column("Family Name", style="green")
    
    cn_status = "✅" if res.has_chinese else "❌"
    fn_status = res.family_name if res.family_name else "[dim]None[/dim]"
    
    table.add_row(res.text, cn_status, fn_status)
    console.print(table)

@app.command()
def batch(
    file: Path = typer.Argument(..., help="Path to Excel file", exists=True, file_okay=True, dir_okay=False, readable=True),
    column: str = typer.Option(None, "--column", "-c", help="Column name to scan"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    custom_names: Optional[str] = typer.Option(None, "--custom-names", help="Custom surnames (comma-separated or JSON list)"),
    exclude_names: Optional[str] = typer.Option(None, "--exclude-names", help="Excluded surnames (comma-separated or JSON list)"),
    mode: str = typer.Option(None, "--match-mode", "-mm", help="Match mode: overall, component, strict")
):
    """批量扫描 Excel 指定列"""
    _batch_impl(file, column, output, custom_names, exclude_names, mode)

def _batch_impl(
    file: Path,
    column: Optional[str] = None,
    output: Optional[Path] = None,
    custom_names: Optional[Union[str, List[str]]] = None,
    exclude_names: Optional[Union[str, List[str]]] = None,
    mode: Optional[str] = None
):
    col_name = column or settings.excel.column
    m_mode = mode or settings.matching.mode
    
    if m_mode not in ["overall", "component", "strict"]:
        console.print(f"[red]❌ Error: Invalid match mode '{m_mode}'. Available modes: overall, component, strict.[/red]")
        sys.exit(1)
    
    if isinstance(custom_names, str):
        c_names = parse_names(custom_names)
    else:
        c_names = custom_names or settings.custom_family_names
        
    if isinstance(exclude_names, str):
        e_names = parse_names(exclude_names)
    else:
        e_names = exclude_names or settings.exclude_family_names
    
    try:
        df = pd.read_excel(file)
    except Exception as e:
        console.print(f"[red]❌ Error reading file: {e}[/red]")
        sys.exit(2)
        
    if col_name not in df.columns:
        console.print(f"[red]❌ Column '{col_name}' not found.[/red]")
        sys.exit(2)

    import time
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Processing {file.name}...", total=len(df))
        
        from .core import get_detector
        detector = get_detector(custom_names=c_names, exclude_names=e_names, mode=m_mode)
        
        has_chinese_list = []
        family_name_list = []
        detector_list = []
        for val in df[col_name]:
            val_str = str(val)
            res = detector.detect(val_str)
            
            has_cn = "✅" if res.has_chinese else "❌"
            fam_name = res.family_name if res.family_name else ""
            
            has_chinese_list.append(has_cn)
            family_name_list.append(fam_name)
            
            # ChineseDetector 逻辑：包含中文 OR 识别出姓氏 -> 保留原始值；否则为空
            if res.has_chinese or fam_name:
                detector_list.append(val)
            else:
                detector_list.append("")
                
            progress.advance(task)
            
    df["HasChinese"] = has_chinese_list
    df["FamilyName"] = family_name_list
    df["ChineseDetector"] = detector_list
    
    # 根据要求：删除输出文件中的 HasChinese 和 FamilyName 列
    df_output = df.drop(columns=["HasChinese", "FamilyName"])
    
    # Save output
    if output:
        out_path = output
    else:
        suffix = settings.excel.output_suffix
        out_path = file.parent / f"{file.stem}{suffix}.xlsx"
        
    df_output.to_excel(out_path, index=False)
    
    elapsed = time.time() - start_time
    # 统计逻辑：将 Hits 计数改为仅基于 ChineseDetector 列，只要有值（非空且非空字符串）就算作一次命中
    hit_count = (df["ChineseDetector"].notna() & (df["ChineseDetector"] != "")).sum()
    
    console.print(f"\n[green]✅ Batch scan completed![/green]")
    console.print(f"Total rows: {len(df)}")
    console.print(f"Hits: {hit_count}")
    console.print(f"Saved to: [bold]{out_path}[/bold]")
    console.print(f"Time elapsed: {elapsed:.2f}s")

@app.command()
def config(output_dir: Path = typer.Option(".", "--output-dir", "-o", help="Directory to save template")):
    """生成配置模板"""
    template = {
        "family_name_path": None,
        "custom_family_names": ["MyName", "慕容"],
        "exclude_family_names": ["SomeFakeName"],
        "excel": {
            "paths": ["data.xlsx"],
            "column": "Name",
            "output_suffix": "_cn",
            "output_dir": "./result"
        },
        "log": {
            "level": "INFO",
            "file": "./logs/cndetect.log",
            "rotation": "1 MB",
            "retention": "7 days",
            "redact_names": True
        }
    }
    
    out_file = output_dir / "cndetect.yaml"
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(template, f, sort_keys=False)
        
    console.print(f"[green]✅ Config template generated at: {out_file}[/green]")

@app.command()
def run(config_path: Path = typer.Option(..., "--config", "-c", help="Path to YAML config")):
    """按 YAML 配置执行批量任务"""
    if not config_path.exists():
        console.print(f"[red]❌ Config file not found: {config_path}[/red]")
        sys.exit(2)
        
    cfg = Settings.load_settings(str(config_path))
    setup_logger(level=cfg.log.level, log_file=cfg.log.file)
    
    if not cfg.excel.paths:
        console.print("[yellow]⚠️ No paths specified in config.[/yellow]")
        return
        
    for p in cfg.excel.paths:
        path = Path(p)
        if not path.exists():
            console.print(f"[red]❌ File not found: {p}[/red]")
            continue
        
        # Reuse batch implementation
        _batch_impl(
            file=path, 
            column=cfg.excel.column, 
            custom_names=cfg.custom_family_names, 
            exclude_names=cfg.exclude_family_names,
            mode=cfg.matching.mode
        )

@app.callback()
def main(version: bool = typer.Option(None, "--version", "-v", is_eager=True, help="Show version")):
    if version:
        console.print(f"cndetect version: {__version__}")
        raise typer.Exit()

if __name__ == "__main__":
    app()
