import os
import click
import locale
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
        if not value.endswith(".pdf"):
            raise click.BadParameter(f"{param.name} must be a PDF file.")
        if not os.path.isfile(value):
            raise click.BadParameter(f"{param.name} file '{value}' does not exist.")
        return value

    @staticmethod
    def isOutputValid(ctx, param, value):
        if value:
            value = str(value)
            if pathlib.Path(value).suffix == "":
                value = f"{value}.pdf"
            if pathlib.Path(value).suffix != ".pdf":
                raise click.BadParameter("Output must be a PDF file.")
            outputDir = os.path.dirname(value)
            if outputDir and not os.path.isdir(outputDir):
                raise click.BadParameter(
                    f"Output directory '{outputDir}' does not exist."
                )
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
        type=click.Path(exists=False, dir_okay=False, readable=True),
        required=False,
        callback=isOutputValid,
        help="Path to the output PDF file (optional). If not provided, the output will be input filename with '_tiny' suffix.",
    )
    def compress(inputFile, outputFile):
        if not outputFile:
            inputPath = pathlib.Path(inputFile)
            outputFile = str(inputPath.with_name(f"{inputPath.stem}_tiny.pdf"))

        args = [
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            "-dPDFSETTINGS=/screen",
            "-dNumRenderingThreads=8",
            "-dBandBufferSpace=500000000",
            "-dBufferSpace=2000000000",
            "-dNOGC",
            "-q",
            f"-o {outputFile}",
            inputFile,
        ]

        encoding = locale.getpreferredencoding()
        encodedArgs = [
            arg.encode(encoding) if isinstance(arg, str) else arg for arg in args
        ]
        command = (b"gs " + b" ".join(encodedArgs)).decode(encoding)

        def runCompression():
            os.system(command)

        def formatSize(size):
            """Format file size to KB, MB, or GB."""
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size < 1024:
                    return f"{size:.2f} {unit}", unit
                size /= 1024

        def formatTime(seconds):
            """Format elapsed time to minutes and seconds if necessary."""
            minutes, seconds = divmod(seconds, 60)
            if minutes > 0:
                return f"{int(minutes)}m {int(seconds)}s"
            else:
                return f"{int(seconds)}s"

        def showSpinner():
            spinner = ["|", "/", "-", "\\"]
            idx = 0
            while compressionThread.is_alive():
                elapsedTime = time.time() - startTime
                formattedTime = formatTime(elapsedTime)
                print(
                    f"\r{Fore.CYAN}Compressing PDF {spinner[idx % len(spinner)]} Elapsed time: {Fore.GREEN}{formattedTime}{Style.RESET_ALL}",
                    end="",
                )
                idx += 1
                time.sleep(0.1)

        compressionThread = threading.Thread(target=runCompression)
        spinnerThread = threading.Thread(target=showSpinner)

        startTime = time.time()

        compressionThread.start()
        spinnerThread.start()

        compressionThread.join()
        spinnerThread.join()

        endTime = time.time()
        elapsedTime = endTime - startTime
        inputSize = os.path.getsize(inputFile)
        outputSize = os.path.getsize(outputFile)

        formattedInputSize, _ = formatSize(inputSize)
        formattedOutputSize, _ = formatSize(outputSize)
        formattedElapsedTime = formatTime(elapsedTime)

        table = PrettyTable(header=False)
        table.title = f"{Fore.LIGHTMAGENTA_EX}{outputFile}{Style.RESET_ALL}"

        details = f"{Fore.RED}{formattedInputSize}{Style.RESET_ALL} {Fore.CYAN}->{Style.RESET_ALL} {Fore.YELLOW}{formattedOutputSize}{Style.RESET_ALL}\nElapsed Time: {Fore.GREEN}{formattedElapsedTime}{Style.RESET_ALL}"

        defaultWidth = 35
        lines = details.split("\n")
        centeredLines = [line.center(defaultWidth) for line in lines]
        details = "\n".join(centeredLines)

        table.add_row([details])
        table.align = "c"
        print(f"\n\n{table}")