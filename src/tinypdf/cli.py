import os
import shutil
import subprocess
import click
import pathlib
import time
import threading
from colorama import init, Fore, Style
from prettytable import PrettyTable

init(autoreset=True)


class TinyPDF:
    @staticmethod
    def isInputValid(ctx, param, value):
        value = str(value)
        if not value.lower().endswith(".pdf"):
            raise click.BadParameter(f"{param.name} must be a PDF file.")
        if not os.path.isfile(value):
            raise click.BadParameter(f"{param.name} file '{value}' does not exist.")
        return value

    @staticmethod
    def isOutputValid(ctx, param, value):
        if value:
            value = str(value)
            p = pathlib.Path(value)
            if p.suffix == "":
                p = p.with_suffix(".pdf")
            if p.suffix.lower() != ".pdf":
                raise click.BadParameter("Output must be a PDF file.")
            out_dir = str(p.parent)
            if out_dir and not os.path.isdir(out_dir):
                raise click.BadParameter(f"Output directory '{out_dir}' does not exist.")
            return str(p)
        return value

    @staticmethod
    @click.command()
    @click.option(
        "-i",
        "--input",
        "inputFile",
        type=click.Path(exists=True, dir_okay=False, readable=True),
        required=True,
        callback=isInputValid,
        help="Path to the input PDF file.",
    )
    @click.option(
        "-o",
        "--output",
        "outputFile",
        # Do NOT set readable=True for a file that will be created
        type=click.Path(exists=False, dir_okay=False),
        required=False,
        callback=isOutputValid,
        help="Optional output PDF file. Defaults to '<input>_tiny.pdf'.",
    )
    def compress(inputFile, outputFile):
        # Ensure Ghostscript exists
        if shutil.which("gs") is None:
            raise click.ClickException("Ghostscript 'gs' not found. Install it: brew install ghostscript")

        # Default output path
        if not outputFile:
            ip = pathlib.Path(inputFile)
            outputFile = str(ip.with_name(f"{ip.stem}_tiny.pdf"))

        # Ghostscript args (no shell)
        args = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            "-dPDFSETTINGS=/screen",
            "-dNumRenderingThreads=8",
            "-dBandBufferSpace=500000000",
            "-dBufferSpace=2000000000",
            "-dNOGC",
            "-q",
            "-o" + outputFile,  # avoid space to prevent quoting issues
            inputFile,
        ]

        def runCompression():
            subprocess.run(args, check=False)

        def formatSize(size):
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size < 1024:
                    return f"{size:.2f} {unit}", unit
                size /= 1024

        def formatTime(seconds):
            m, s = divmod(int(seconds), 60)
            return f"{m}m {s}s" if m else f"{s}s"

        def showSpinner():
            spinner = ["|", "/", "-", "\\"]
            idx = 0
            while compressionThread.is_alive():
                elapsed = time.time() - startTime
                print(
                    f"\r{Fore.CYAN}Compressing PDF {spinner[idx % 4]} "
                    f"Elapsed: {Fore.GREEN}{formatTime(elapsed)}{Style.RESET_ALL}",
                    end="",
                )
                idx += 1
                time.sleep(0.1)

        compressionThread = threading.Thread(target=runCompression, daemon=True)
        spinnerThread = threading.Thread(target=showSpinner, daemon=True)

        startTime = time.time()
        compressionThread.start()
        spinnerThread.start()
        compressionThread.join()
        spinnerThread.join()

        inputSize = os.path.getsize(inputFile)
        outputSize = os.path.getsize(outputFile)
        fin, _ = formatSize(inputSize)
        fout, _ = formatSize(outputSize)
        elapsed = formatTime(time.time() - startTime)

        table = PrettyTable(header=False)
        table.title = f"{Fore.LIGHTMAGENTA_EX}{outputFile}{Style.RESET_ALL}"
        details = (
            f"{Fore.RED}{fin}{Style.RESET_ALL} {Fore.CYAN}->{Style.RESET_ALL} "
            f"{Fore.YELLOW}{fout}{Style.RESET_ALL}\n"
            f"Elapsed Time: {Fore.GREEN}{elapsed}{Style.RESET_ALL}"
        )
        details = "\n".join(line.center(35) for line in details.split("\n"))
        table.add_row([details])
        table.align = "c"
        print(f"\n\n{table}")