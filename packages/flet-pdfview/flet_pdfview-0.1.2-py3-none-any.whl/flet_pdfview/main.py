from flet import Column,Image,ScrollMode,BoxFit
import asyncio , os,pymupdf,gc
from typing import Optional
class PdfColumn(Column):
    """
**FLET PDF VIEW** 
**EXMEPLE CODE**: 
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

make sure if the path do not end with .pdf or the path not exists the PdfColumn will do not show anything !
    """
    def __init__(self,src:str="",widht:Optional[int]=None,height:Optional[int]=None,spacing:Optional[int]=None,expand_loose:Optional[bool]=False,expand:Optional[bool]=False,scroll:ScrollMode=ScrollMode.ADAPTIVE,dpi:int=150,fitImage:BoxFit=BoxFit.FILL,visible:Optional[bool]=True):
        super().__init__()
        self._src=src
        self.expand=expand
        self.expand_loose=expand_loose
        self.scroll=scroll
        self.spacing=spacing
        self.widht=widht
        self.height=height
        self.controls=[]
        self._fitImage=fitImage
        self._dpi=dpi
        self.visible=visible
        asyncio.create_task(self.__start_converte(src))
    async def __start_converte(self,path:str="",dpi:int=150):
        self.controls.clear()
        if os.path.exists(path) and path.endswith(".pdf"):
            
            pdf_pages = pymupdf.open(path)
            
            for pdf_page in pdf_pages:
                if self.src==path:
                    pix = pdf_page.get_pixmap(dpi=dpi)
                    
                    # pix.save(filename="file.png",output=ram)
                    self.controls.append(
                        Image(
                            expand=self.expand,
                            expand_loose=self.expand_loose,
                            width=self.widht,
                            height=self.height,
                            src=pix.tobytes(),
                            fit=self.fitImage
                        )
                    
                    )
                    
                    self.update()
                    gc.collect()
                    await asyncio.sleep(0.3)
                else:
                    break
            

    @property
    def src(self):
        return self._src
    @src.setter
    def src(self,new_src):
        self._src=new_src
        asyncio.create_task(self.__start_converte(new_src,))
    @property
    def fitImage(self):
        return self._fitImage
    @fitImage.setter
    def fitImage(self,new_fitImage):
        self._fitImage=new_fitImage
        for image in self.controls:
            if isinstance(image,Image):
                image.fit=new_fitImage
    @property
    def dpi(self):
        return self._dpi
    @dpi.setter
    def dpi(self,new_dpi):
        self._dpi=new_dpi
        asyncio.create_task(self.__start_converte(self.src,))