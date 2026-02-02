
""" Metodos creados para dar apoyo al modulo principal de
    la libreria """
    

"========================================================"

from visor_vari.mas_bajo_nivel.variables_valores import base
from visor_vari.mas_bajo_nivel.variables_valores import linea
from visor_vari.mas_bajo_nivel.variables_valores import pulso

from visor_vari.carpeta_de_apoyo.revisar import ver_registro

from visor_vari.mas_bajo_nivel.variables_valores import tk

"========================================================"

class Asiste:

    def boton_mues(self, marco):
        
        self.panel_control= tk.LabelFrame(marco)
        self.panel_control.pack(anchor= "w")

        boton_para_crear_nuevo_carapter= tk.Button (self.panel_control, text= "mostrar carapteres", command= self.mirar_las_varis)
        boton_para_crear_nuevo_carapter.config(padx= 24)
        boton_para_crear_nuevo_carapter.pack ()

    def mirar_las_varis(self):
        ver_registro(tk)

    "- - - - - - - - - - -"

burbuja= Asiste()

"- - - - - - - - - - -"

def enumer_sub():
    
    if True: # Detecto...
        
        if base.argment_1 != pulso.escalon:
            pulso.cambio_de_fase= False
        
        else: # si son iguales "disloco" para demostrar
            pulso.escalon += 1
            pulso.cambio_de_fase= True
            base.activo_para_2= True
            
    if True: # Si hay un cambio, cuento
        
        if pulso.cambio_de_fase == False:
            pulso.sub_cuenta += 1
            linea.enau_ment += 1
        else:
            pulso.sub_cuenta= 1
            linea.enau_ment += 1
        
    if pulso.cambio_de_fase == True: # igualando, para poder entrar.
        pulso.entrada += 1

