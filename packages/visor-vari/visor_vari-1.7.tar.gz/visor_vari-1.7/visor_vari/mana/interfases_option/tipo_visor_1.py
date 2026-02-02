
""" visor_vari opcion primera (unica) """


if True: # Descripcion
    """
    Este modulo trabaja sin sacar una ventana.
    muestra el dato por consola.
    """

"====================================================="

from visor_vari.mana.elementos_de_conducto.conducto_uno import *

"====================================================="

class Tipo_uno:
    
    def __init__(self):
        
        objeto= tk.Tk()
        ini.objeto_tk= objeto
        
        linea.numero_de_ola= 1
        linea.sub_numero= linea.enau_ment + 1
        linea.enau_ment= linea.sub_numero
        
        objeto.geometry("250x25")
        objeto.title ("visor_vari")

        self.primer_marco= tk.LabelFrame(objeto, bd= 0)
        self.primer_marco.pack(expand= True, fill= tk.BOTH)
        
        burbuja.boton_mues(self.primer_marco)
        
        objeto.mainloop()

        
