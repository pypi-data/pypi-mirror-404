import subprocess
import typer
import shutil

from typing import Annotated
from rich.console import Console
from rich.progress import track
from beaupy import confirm, prompt
from beaupy.spinners import Spinner, DOTS
from pathlib import Path

# convert a bunch of blend files to glb

app = typer.Typer()
console = Console()


def blender_exists() -> bool:
    console.log("checking blender...")
    spinner = Spinner(DOTS, "checking...")
    spinner.start()
    result = False
    if shutil.which("blender") is None:
        console.log("[red]Could not find Blender![/red]")
        result = False
    # TODO: Verbose, print the version
    else:
        console.log("[green]found blender[/green]")
        result = True
    spinner.stop()
    return result


@app.command()
def main(
    dirs: Annotated[list[Path] | None, typer.Argument()] = None,
    outdir: Annotated[Path, typer.Argument()] = None,
    ask: Annotated[bool, typer.Option(help="Ask for input on decisions")] = False,
):
    # Get all .blend files in dirs, and output to a desination.
    # If no files, assume current direcotry and down
    # if no output, ask to put them in ./GLB
    # console.print("Hello from blend-x-glb!")

    if not blender_exists():
        return

    targetDirectory = outdir
    if not outdir:
        # ask the user if we dump in ./GLB
        # goofy - if ask is on then we need to confirm
        # if ask is off then assume the answer is YES
        if not ask or confirm(
            "No destination specified, output to [blue]./GLB[/blue]?",
            default_is_yes=True,
        ):
            targetDirectory = Path("GLB")
        else:
            targetDirectory = Path.resolve(
                prompt(
                    prompt="Destination: ",
                    target_type=Path,
                )
            )
    if not (targetDirectory.exists() and targetDirectory.is_dir()):
        if not ask or confirm(
            f"directory {targetDirectory.absolute()} does not exist",
            default_is_yes=True,
        ):
            targetDirectory.mkdir(parents=True, exist_ok=False)
        else:
            console.print(f"Did not create {targetDirectory.absolute()}")
            abort()

    targets: list[Path] = []
    if not dirs and (
        not ask
        or confirm("No directories specified to scan: recursively checking from cwd?")
    ):
        targets = list(Path.cwd().rglob("*.blend"))
    elif dirs:
        for d in dirs:
            # Get all .blend files in these repositories
            # TODO: fix if we're given a file
            targets = list(d.rglob("*.blend"))
    else:
        console.print("Did not recursively scan for .blends")
        abort()

    # work all .blends
    console.log(f"found {len(targets)} files")
    if len(targets) == 0:
        return
    console.log("Start conversion")
    converted = 0
    failed = 0
    # TODO: fix this so the progress bar isn't BORKED
    for t in track(targets, description="Converting..."):
        destination = Path.joinpath(targetDirectory, f"{t.stem}.glb")
        console.print(f"dump to {destination.absolute()}")
        try:
            result = subprocess.run(
                [
                    "blender",
                    t.absolute(),
                    "-b",
                    "--python",
                    "blender_export.py",
                    "--",
                    destination,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            console.log(f"processed {t.absolute()}")
            console.log(f"res: {result}")
            converted += 1
        except subprocess.CalledProcessError as e:
            console.log(f"failed to process {t.absolute()}")
            console.print(e.stderr)
            failed += 1
    console.log(f"finished converting [green]{converted} files[/green]")
    if failed > 0:
        console.print(f"[red]failed {failed}[/red]")


def abort():
    console.print("Aborting...")
    exit


if __name__ == "__main__":
    app()
