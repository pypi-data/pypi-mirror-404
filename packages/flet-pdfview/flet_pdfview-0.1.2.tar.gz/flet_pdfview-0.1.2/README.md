# 📄 flet-pdfview

**A lightweight and efficient PDF viewer component for Flet applications.**

`flet-pdfview` provides a simple way to render PDF files inside your UI while keeping performance, stability, and user experience in mind.

---

### ✨ Features

* 🧩 **Native PDF rendering** inside Flet layouts.
* 📐 **High-resolution** rendering with custom DPI.
* 🖼️ **Flexible image fitting** using `BoxFit`.
* 📱 **Fully responsive** (via `expand=True`).
* 🚫 **Silent failure** for invalid paths (no crashes, no UI freezes).
* ⚡ **Optimized** for performance and UI stability.

---

### 📦 Installation

Install the package directly from PyPI:

```bash
pip install flet-pdfview
```
### 🚀 Basic UsagePython
```
from flet_pdfview import PdfColumn
from flet import Page, run, BoxFit

def main(page: Page):
    page.add(
        PdfColumn(
            src="path/to/your/file.pdf",
            expand=True,
            dpi=300,
            fitImage=BoxFit.FILL
        )
    )

run(main)
```
### ⚠️ Important Behavior

`PdfColumn` will not render anything if:

1. The provided **path does not exist**.
2. The file path **does not end with `.pdf`**.

> [!IMPORTANT]
> **This behavior is intentional:**
> * **No exceptions** ❌
> * **No error dialogs** ❌
> * **No UI interruption** ❌
> 
> The component simply stays silent and allows the application to continue running normally.

---

### 🎯 Why Silent Failure?

This design choice ensures:

* 🛡️ **Application stability**: Prevents crashes due to missing files.
* 🧠 **Clean Experience**: A distraction-free UI for the end-user.
* 🚀 **Production Ready**: Predictable behavior in live environments.

**In short:** *No valid PDF → No rendering → App remains stable.*