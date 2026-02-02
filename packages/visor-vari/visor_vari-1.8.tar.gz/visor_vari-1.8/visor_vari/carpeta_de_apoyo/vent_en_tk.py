
""" Modulo que alberga muchas posibles sub-ventanas """


"=============================================="

from visor_vari.mas_bajo_nivel.variables_valores import ini, linea, tk

"=============================================="

def muestra_varis(enla_l):
    
    if enla_l == 1:
        ini.seg_tkven= tk.Toplevel(ini.objeto_tk)
        ini.seg_tkven.title("Oleada: " + str(linea.numero_de_ola) + "   Ventana n: " + str(linea.sub_numero))

    if enla_l == 2:
        ini.seg_tkven= tk.Toplevel(ini.objeto_tk)
        ini.seg_tkven.title("Oleada: " + str(linea.numero_de_ola) + "   Ventana n: " + str(linea.sub_numero))

    if enla_l == 3:
        ini.seg_tkven= tk.Toplevel(ini.objeto_tk)
        ini.seg_tkven.title("Oleada: " + str(linea.numero_de_ola) + "   Ventana n: " + str(linea.sub_numero))

    if enla_l == 4:
        ini.seg_tkven= tk.Toplevel(ini.objeto_tk)
        ini.seg_tkven.title("Oleada: " + str(linea.numero_de_ola) + "   Ventana n: " + str(linea.sub_numero))

    if enla_l == 5:
        ini.seg_tkven= tk.Toplevel(ini.objeto_tk)
        ini.seg_tkven.title("Oleada: " + str(linea.numero_de_ola) + "   Ventana n: " + str(linea.sub_numero))

