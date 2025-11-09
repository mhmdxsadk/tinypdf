# TinyPDF

**TinyPDF** is a lightweight command-line tool for compressing PDF files using Ghostscript, built with Python and Click.

## Installation

Install using Homebrew:

```bash
brew tap mhmdxsadk/tools
brew install tinypdf
```

## Usage

```bash
tinypdf -i <input.pdf> [-o <output.pdf>]
```

If no output file is specified, TinyPDF automatically saves the result as `<input>_tiny.pdf`.

## Examples

Compress a PDF and create a new file:

```bash
tinypdf -i report.pdf
```

Compress a PDF and specify an output path:

```bash
tinypdf -i report.pdf -o compressed.pdf
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.