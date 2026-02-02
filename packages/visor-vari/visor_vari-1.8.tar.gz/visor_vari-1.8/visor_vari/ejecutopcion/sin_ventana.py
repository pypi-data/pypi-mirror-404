
""" Probador...

    Con este modulo quiero probar que funcione
    la segunda version (la que es de flujo pero
    sin ventana de tkinter) """
    

"=========================================="

from visor_vari.visorquipus import gentil, ultimate, riel
from visor_vari.see import refer

"=========================================="

def ejecutando(opcion, hola):

    NADA= None
    nume= 1

    "- - - - - - -"

    if opcion == 1:

        tu= hola
        
        while tu != 0:
            
            print()
            print("hola n°: " + str(nume)); nume += 1
            print()
            
            refer.selda_0= 1
            gentil()
            refer.selda_0= 2
            gentil()
            refer.selda_0= 26
            gentil()
            refer.selda_0= 3
            gentil()
            """refer.selda_0= 4
            gentil()
            refer.selda_0= 5
            gentil()
            refer.selda_0= 8
            gentil()
            refer.selda_0= 9
            gentil()"""

            tu -= 1
    
    "- - - - - - -"

    if opcion == 2:

        tu= hola
        
        while tu != 0:
            
            print()
            print("hola n°: " + str(nume)); nume += 1
            print()

            refer.selda_0= 1
            gentil(1, "serie")
            refer.selda_0= 12
            gentil(1, "serie")
            
            refer.selda_0= 2
            gentil(2, "serie")
            refer.selda_0= 27
            gentil(2, "serie")
            
            refer.selda_0= 34
            gentil(3, "serie")
            refer.selda_0= 38
            gentil(1, "serie")

            tu -= 1
        
    "- - - - - - -"

    if opcion == 3:

        tu= hola
        
        while tu != 0:
                        
            print()
            print("hola n°: " + str(nume)); nume += 1
            print()

            riel(1, 2)

            refer.selda_0= 1
            gentil(1, "serie")
            refer.selda_0= 12
            gentil(1, "serie")
            
            refer.selda_0= 2
            gentil(2, "serie")
            refer.selda_0= 27
            gentil(2, "serie")
            
            refer.selda_0= 34
            gentil(1, "serie")
            refer.selda_0= 38
            gentil(1, "serie")

            tu -= 1
            
    "- - - - - - -"

    if opcion == 4:

        tu= hola
        
        while tu != 0:
                        
            print()
            print("hola n°: " + str(nume)); nume += 1
            print()

            #un_d= [0,1]
            
            riel(0, 1)
            
            #bo= True
            #riel(un_d, bo)

            refer.selda_0= 1
            gentil(1, "paralelo")
            refer.selda_0= 12
            gentil(1, "paralelo")
            
            refer.selda_0= 2
            gentil(2, "paralelo")
            refer.selda_0= 27
            gentil(2, "paralelo")
            
            refer.selda_0= 34
            gentil(1, "paralelo")
            refer.selda_0= 38
            gentil(1, "paralelo")
            
            tu -= 1
            
            ultimate()
            
