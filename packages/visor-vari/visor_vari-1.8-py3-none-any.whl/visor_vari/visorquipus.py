
""" Ventana principal del visor de variables """


"========================================================"

#visor_vari.
from visor_vari.mas_bajo_nivel.variables_valores import *

from visor_vari.mana.interfases_option.tipo_visor_1 import *
from visor_vari.mana.interfases_option.tipo_visor_2 import *
from visor_vari.mana.interfases_option.tipo_visor_3 import *
from visor_vari.mana.interfases_option.tipo_visor_4 import *
from visor_vari.mana.interfases_option.hilo_para_vent import *

"========================================================"

class Visor_vari_quipues_alfa:
        
    def primer_modo(self):      # uno a uno
        Tipo_uno()
        
    def segundo_modo(self):     # el 1er_gentil abre todos los suyos 
        Tipo_dos()

    def tercer_modo(self):      # abre puntual del 1er_gentil
        Tipo_tres()
        
    def cuarto_modo(self):      # todo puntuales (en paralelo)
        Tipo_cuatro()
        
sin_ventana= Visor_vari_quipues_alfa()


class Visor_vari_quipues_beta_a:
            
    def primer_modo(self, vent):
        proceso_adyacente(1, vent)

    def segundo_modo(self, vent):
        proceso_adyacente(2, vent)

con_ventana_1= Visor_vari_quipues_beta_a()


class Visor_vari_quipues_beta_b:
            
    def primer_modo(self, vent):
        proceso_adyacente(3, vent)

    def segundo_modo(self, vent):
        proceso_adyacente(4, vent)

con_ventana_2= Visor_vari_quipues_beta_b()

"------------------------------------"

def riel(posicion, atado= None):
    
    base.posi_driel= posicion
    base.posi_atada= atado

def ultimo_numero(act_num):
    
    if base.tipo_visor == 1:
        pass
    if base.tipo_visor == 2:
        pass
    if base.tipo_visor == 3:
        pass
    else:                   # Solo 4 emplean 'todo.limit'
        if act_num > todo.limit:
            todo.limit= act_num
        else:
            pass

def gentil(numero= None, extension= None, objet_supre= None):
    
    if True: # depositando valores
        
        base.argment_1= numero  # Alojo el 1er atributo de gentil
        objetivo= objet_supre   # Solo para la cuarta forma del visualizacion.

    if True: # filtrando configuraciones de 'sin ventana'
    
        if (numero == None) and (extension == None) and (objetivo == None):
            
            base.tipo_visor= 1
            sin_ventana.primer_modo()
            
            base.argment_1= 1
        
        if (numero != None) and (extension == "serie") and (objetivo == None):
            
            if base.posi_driel != None:
                
                base.tipo_visor= 3
                sin_ventana.tercer_modo()
            else:
                base.tipo_visor= 2
                sin_ventana.segundo_modo()

        if (numero != None) and (extension == "paralelo") and (objetivo == None):
            
            base.tipo_visor= 4
            sin_ventana.cuarto_modo()

    "- - - - - - - - - - - - - - - - - - -"

    if True: # filtrando configuraciones de 'con ventana'

        if (numero == None) and (extension == None) and (objetivo != None):
            
            base.tipo_visor= 5
            con_ventana_1.primer_modo(objetivo)
            
            base.argment_1= 1
        
        if (numero != None) and (extension == "serie") and (objetivo != None):
            
            if base.posi_driel != None:
                
                base.tipo_visor= 7
                con_ventana_2.primer_modo(objetivo)
            else:
                base.tipo_visor= 6
                con_ventana_1.segundo_modo(objetivo)

        if (numero != None) and (extension == "paralelo") and (objetivo != None):
            
            base.tipo_visor= 8
            con_ventana_2.segundo_modo(objetivo)

    # ultimo_numero(base.argment_1) # para otra version

def ultimate():
    
    if base.tipo_visor == 4:
        
        todo.other_ola += 1
        base.enumer_geltil= 0

