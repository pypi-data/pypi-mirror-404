
""" Compruebo la libreria visor-vari con_vent_2 """


"============================================="

import tkinter as tk

from visor_vari.visorquipus import gentil, riel, ultimate
from visor_vari.see import refer

"- - - - - - - - "

nada= None

def milu(etapa):
    
    if etapa == 1:
        
        refer.selda_0= 15
        refer.selda_1= 15
    
    if etapa == 2:
        refer.selda_0= 28

    if etapa == 3:
        refer.selda_3= 379


class Via:
    
    def __init__(self):
        self.vent= None

principal= Via()


"============================================="

def minoury():

    riel(1)
    
    milu(1)
    gentil(2, "serie", principal.vent)
    milu(3)
    gentil(2, "serie", principal.vent)
    milu(2)
    gentil(1, "serie", principal.vent)

def minou():

    hello= 0

    while hello < 3:

        print("num ola: ", hello)

        riel(0)
        
        milu(1)
        gentil(1, "paralelo", principal.vent)
        milu(3)
        gentil(1, "paralelo", principal.vent)
        milu(2)
        gentil(2, "paralelo", principal.vent)
        
        ultimate()
        
        hello += 1

principal.vent= tk.Tk()

principal.vent.title("con la ventana_1")
principal.vent.geometry("250x200")

bon_1= tk.Button(principal.vent, text= "tipo_1", command= minoury)
bon_1.pack()

bon_2= tk.Button(principal.vent, text= "tipo_2", command= minou)
bon_2.pack()

principal.vent.mainloop()

