
""" Este es un modulo intermedio entre la ventana
    'muestra carapteres' y la subventana.

    En este modulo se llama la subventana """


"=============================================="

from visor_vari.carpeta_de_apoyo.canales_de_apoyo.apoyo_de_revisar import *

"=============================================="

def ver_registro(tkinter):

    class La_mini:

        def __init__(self):
            
            self.muestro_v_principal= True
            self.sub_ventana()
            
        def sub_ventana(self):
                        
            muestra_varis(1) # es uno (1) por la version simple

            if True:    # visual y botones

                dereizq= tkinter.LabelFrame(ini.seg_tkven, padx= 10, pady= 10, bd= 0)
                dereizq.pack (expand= True, fill= tkinter.BOTH)

                "... panel lateral derecho ..."

                perimetro= tkinter.LabelFrame(dereizq) # marco derecho (botones de control)
                perimetro.config(bd= 0)
                perimetro.pack (side= tkinter.RIGHT, fill= tkinter.Y, expand= True)

                boton_0= tkinter.Button(perimetro, text= "sin\nVentana\nde\nRespaldo", command= self.sin_ventana_principal)
                boton_0.pack(fill= tkinter.BOTH, expand= True)

                boton_1= tkinter.Button(perimetro, text= "Actualiza\nceldas", command= self.actualizar)
                boton_1.pack(fill= tkinter.BOTH, expand= True)

                "... Creo el LabelFrame del marco de la ventana ..."
                "... y que contendra los otros marcos (celdas) ..."

                perimetro= tkinter.LabelFrame(dereizq, padx= 10, pady= 10, bg= "red")
                perimetro.pack (expand= True, fill= tkinter.BOTH)

                entorno= tkinter.LabelFrame(perimetro, padx= 30, pady= 30) # marco izquierdo (de texto)
                entorno.pack (expand= True, fill= tkinter.BOTH)
    
            if True:    # aqui estan los marcos de las celdas
                self.gajo_0= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_0.grid(row= 0, column= 0)

                self.gajo_1= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_1.grid(row= 0, column= 1)

                self.gajo_2= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_2.grid(row= 0, column= 2)


                self.gajo_3= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_3.grid(row= 1, column= 0)

                self.gajo_4= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_4.grid(row= 1, column= 1)

                self.gajo_5= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_5.grid(row= 1, column= 2)


                self.gajo_6= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_6.grid(row= 2, column= 0)

                self.gajo_7= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_7.grid(row= 2, column= 1)

                self.gajo_8= tkinter.LabelFrame(entorno, padx= 15, pady= 15)
                self.gajo_8.grid(row= 2, column= 2)

            self.visual_celda_0()

        "........................"

        "manipulacion de la ventana_muestra_carapteres"

        def sin_ventana_principal(self):
            
            if self.muestro_v_principal == True:
                ini.objeto_tk.geometry("0x0")
                self.muestro_v_principal= False
            else:
                ini.objeto_tk.geometry("200x25")
                self.muestro_v_principal= True

        def actualizar(self):
            ini.objeto_tk.destroy()
        
        "........................"

        def visual_celda_0(self):

            self.prueva0_0= tkinter.Button (self.gajo_0, text= refer.selda_0)
            self.prueva0_0.config (bg= "white")
            self.prueva0_0.grid(row= 0, column= 0)

            self.prueva1_0= tkinter.Button (self.gajo_0, text= refer.selda_1)
            self.prueva1_0.config (bg= "white")
            self.prueva1_0.grid(row= 0, column= 1)

            self.prueva2_0= tkinter.Button (self.gajo_0, text= refer.selda_2)
            self.prueva2_0.config (bg= "white")
            self.prueva2_0.grid(row= 0, column= 2)

            ""
            self.prueva3_0= tkinter.Button (self.gajo_0, text= refer.selda_3)
            self.prueva3_0.config (bg= "white")
            self.prueva3_0.grid(row= 1, column= 0)

            self.prueva4_0= tkinter.Button (self.gajo_0, text= refer.selda_4)
            self.prueva4_0.config (bg= "white")
            self.prueva4_0.grid(row= 1, column= 1)

            self.prueva5_0= tkinter.Button (self.gajo_0, text= refer.selda_5)
            self.prueva5_0.config (bg= "white")
            self.prueva5_0.grid(row= 1, column= 2)

            ""
            self.prueva6_0= tkinter.Button (self.gajo_0, text= refer.selda_6)
            self.prueva6_0.config (bg= "white")
            self.prueva6_0.grid(row= 2, column= 0)

            self.prueva7_0= tkinter.Button (self.gajo_0, text= refer.selda_7)
            self.prueva7_0.config (bg= "white")
            self.prueva7_0.grid(row= 2, column= 1)

            self.prueva8_0= tkinter.Button (self.gajo_0, text= refer.selda_8)
            self.prueva8_0.config (bg= "white")
            self.prueva8_0.grid(row= 2, column= 2)

            self.visual_celda_1()

        def visual_celda_1(self):

            self.prueva0_1= tkinter.Button (self.gajo_1, text= refer.selda_9)
            self.prueva0_1.config (bg= "white")
            self.prueva0_1.grid(row= 0, column= 0)

            self.prueva1_1= tkinter.Button (self.gajo_1, text= refer.selda_10)
            self.prueva1_1.config (bg= "white")
            self.prueva1_1.grid(row= 0, column= 1)

            self.prueva2_1= tkinter.Button (self.gajo_1, text= refer.selda_11)
            self.prueva2_1.config (bg= "white")
            self.prueva2_1.grid(row= 0, column= 2)

            ""
            self.prueva3_1= tkinter.Button (self.gajo_1, text= refer.selda_12)
            self.prueva3_1.config (bg= "white")
            self.prueva3_1.grid(row= 1, column= 0)

            self.prueva4_1= tkinter.Button (self.gajo_1, text= refer.selda_13)
            self.prueva4_1.config (bg= "white")
            self.prueva4_1.grid(row= 1, column= 1)

            self.prueva5_1= tkinter.Button (self.gajo_1, text= refer.selda_14)
            self.prueva5_1.config (bg= "white")
            self.prueva5_1.grid(row= 1, column= 2)

            ""
            self.prueva6_1= tkinter.Button (self.gajo_1, text= refer.selda_15)
            self.prueva6_1.config (bg= "white")
            self.prueva6_1.grid(row= 2, column= 0)

            self.prueva7_1= tkinter.Button (self.gajo_1, text= refer.selda_16)
            self.prueva7_1.config (bg= "white")
            self.prueva7_1.grid(row= 2, column= 1)

            self.prueva8_1= tkinter.Button (self.gajo_1, text= refer.selda_17)
            self.prueva8_1.config (bg= "white")
            self.prueva8_1.grid(row= 2, column= 2)

            self.visual_celda_2()

        def visual_celda_2(self):

            self.prueva0= tkinter.Button (self.gajo_2, text= refer.selda_18)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_2, text= refer.selda_19)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_2, text= refer.selda_20)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_2, text= refer.selda_21)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_2, text= refer.selda_22)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_2, text= refer.selda_23)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_2, text= refer.selda_24)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_2, text= refer.selda_25)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_2, text= refer.selda_26)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_3()

        def visual_celda_3(self):

            self.prueva0= tkinter.Button (self.gajo_3, text= refer.selda_27)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_3, text= refer.selda_28)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_3, text= refer.selda_29)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_3, text= refer.selda_30)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_3, text= refer.selda_31)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_3, text= refer.selda_32)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_3, text= refer.selda_33)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_3, text= refer.selda_34)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_3, text= refer.selda_35)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_4()

        def visual_celda_4(self):

            self.prueva0= tkinter.Button (self.gajo_4, text= refer.selda_36)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_4, text= refer.selda_37)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_4, text= refer.selda_38)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_4, text= refer.selda_39)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_4, text= refer.selda_40)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_4, text= refer.selda_41)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_4, text= refer.selda_42)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_4, text= refer.selda_43)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_4, text= refer.selda_44)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_5()

        def visual_celda_5(self):

            self.prueva0= tkinter.Button (self.gajo_5, text= refer.selda_45)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_5, text= refer.selda_46)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_5, text= refer.selda_47)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_5, text= refer.selda_48)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_5, text= refer.selda_49)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_5, text= refer.selda_50)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_5, text= refer.selda_51)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_5, text= refer.selda_52)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_5, text= refer.selda_53)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_6()

        def visual_celda_6(self):

            self.prueva0= tkinter.Button (self.gajo_6, text= refer.selda_54)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_6, text= refer.selda_55)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_6, text= refer.selda_56)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_6, text= refer.selda_57)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_6, text= refer.selda_58)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_6, text= refer.selda_59)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_6, text= refer.selda_60)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_6, text= refer.selda_61)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_6, text= refer.selda_62)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_7()

        def visual_celda_7(self):

            self.prueva0= tkinter.Button (self.gajo_7, text= refer.selda_63)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_7, text= refer.selda_64)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_7, text= refer.selda_65)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_7, text= refer.selda_66)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_7, text= refer.selda_67)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_7, text= refer.selda_68)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_7, text= refer.selda_69)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_7, text= refer.selda_70)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_7, text= refer.selda_71)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

            self.visual_celda_8()

        def visual_celda_8(self):

            self.prueva0= tkinter.Button (self.gajo_8, text= refer.selda_72)
            self.prueva0.config (bg= "white")
            self.prueva0.grid(row= 0, column= 0)

            self.prueva1= tkinter.Button (self.gajo_8, text= refer.selda_73)
            self.prueva1.config (bg= "white")
            self.prueva1.grid(row= 0, column= 1)

            self.prueva2= tkinter.Button (self.gajo_8, text= refer.selda_74)
            self.prueva2.config (bg= "white")
            self.prueva2.grid(row= 0, column= 2)

            ""
            self.prueva3= tkinter.Button (self.gajo_8, text= refer.selda_75)
            self.prueva3.config (bg= "white")
            self.prueva3.grid(row= 1, column= 0)

            self.prueva4= tkinter.Button (self.gajo_8, text= refer.selda_76)
            self.prueva4.config (bg= "white")
            self.prueva4.grid(row= 1, column= 1)

            self.prueva5= tkinter.Button (self.gajo_8, text= refer.selda_77)
            self.prueva5.config (bg= "white")
            self.prueva5.grid(row= 1, column= 2)

            ""
            self.prueva6= tkinter.Button (self.gajo_8, text= refer.selda_78)
            self.prueva6.config (bg= "white")
            self.prueva6.grid(row= 2, column= 0)

            self.prueva7= tkinter.Button (self.gajo_8, text= refer.selda_79)
            self.prueva7.config (bg= "white")
            self.prueva7.grid(row= 2, column= 1)

            self.prueva8= tkinter.Button (self.gajo_8, text= refer.selda_80)
            self.prueva8.config (bg= "white")
            self.prueva8.grid(row= 2, column= 2)

    "........................"

    La_mini()

