
""" Con este modulo pretendo acceder a cualquier tipo
    que emplee de entrada ya una ventana tkinter """
    
    
"===================================================="

from visor_vari.mana.interfases_option.con_vent_1.tipo_visor_5 import Tipo_cinco
from visor_vari.mana.interfases_option.con_vent_1.tipo_visor_6 import Tipo_seis

from visor_vari.mana.interfases_option.con_vent_2.tipo_visor_7 import Tipo_siete
from visor_vari.mana.interfases_option.con_vent_2.tipo_visor_8 import Tipo_ocho

from visor_vari.mas_bajo_nivel.variables_valores import ini
from threading import Thread

"===================================================="

def vallamos_al_tipo_5(vent):
    Tipo_cinco(vent)
    
def vallamos_al_tipo_6(vent):
    Tipo_seis(vent)

def vallamos_al_tipo_7(vent):
    Tipo_siete(vent)
    
def vallamos_al_tipo_8(vent):
    Tipo_ocho(vent)

"- - - - - - - - - - - - - - - -"

def proceso_adyacente(num, dato):
    
    def deten_impulso():
        
        sigue= input("next : ")

        if (sigue == "n") or (sigue == "N"):
            ini.seg_tkven.destroy()
    
    if num == 1:
    
        print("2do hilo tipo 5")
        
        traspaso= Thread(target= vallamos_al_tipo_5, args= (dato,))
        traspaso.start()

        deten_impulso()
        
    if num == 2:
    
        print("2do hilo tipo 6")
        
        traspaso= Thread(target= vallamos_al_tipo_6, args= (dato,))
        traspaso.start()

        deten_impulso()

    if num == 3:
    
        print("2do hilo tipo 7")
        
        traspaso= Thread(target= vallamos_al_tipo_7, args= (dato,))
        traspaso.start()

        deten_impulso()

    if num == 4:
    
        print("2do hilo tipo 8")
        
        traspaso= Thread(target= vallamos_al_tipo_8, args= (dato,))
        traspaso.start()

        deten_impulso()

