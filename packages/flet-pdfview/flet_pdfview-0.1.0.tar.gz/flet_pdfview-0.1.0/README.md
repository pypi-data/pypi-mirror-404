**FLET PDF VIEW**
exemple : 
```
from flet_pdfview import PdfColumn
from flet import Page,run,BoxFit

def main(page:Page):
    page.add(
        PdfColumn(
            src="you/pdf/path",
            expand=True,
            dpi=300,
            fitImage=BoxFit.FILL
        )
    )
run(main)
```

make sure if the path do not end with .pdf or the path not exists the PdfColumn will do not show anything