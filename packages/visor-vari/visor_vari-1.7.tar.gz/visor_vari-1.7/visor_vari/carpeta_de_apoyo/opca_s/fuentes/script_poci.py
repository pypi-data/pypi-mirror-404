
""" codigo que muebe la operacion de pociciones 
    que se entienden bajo el concepto de rieles """
    

"============================================"

from visor_vari.mas_bajo_nivel.variables_valores import base, todo
from visor_vari.mas_bajo_nivel.variables_valores import permiso_a

"============================================"

class Esenario_de_pociciones:

    def riel_de_serie(self):

        if base.posi_atada != None:
            if base.enumer_geltil == base.posi_atada:
                permiso_a.caso_3= True

        if base.enumer_geltil == base.posi_driel:
            permiso_a.caso_3= True
        else:
            base.enumer_geltil += 1
        
    def riel_de_paralelo(self):
        
        if base.posi_driel != None:
            
            if isinstance(base.posi_driel, list):
                
                dubi= todo.other_ola - 1
                por_dict= base.posi_driel[dubi]
                
                if base.posi_atada == True:
                    if base.enumer_geltil == (por_dict + 1):
                        permiso_a.caso_4= True
                
                if base.enumer_geltil == por_dict:
                    permiso_a.caso_4= True
                else:
                    base.enumer_geltil += 1
                
                # (este angulo actua) empleando una lista
                
            else: # con riel normal
            
                if base.posi_atada != None:
                    if base.enumer_geltil == base.posi_atada:
                        permiso_a.caso_4= True
                    
                if base.enumer_geltil == base.posi_driel:
                    permiso_a.caso_4= True
                else:
                    base.enumer_geltil += 1
                    
        else: # sin riel
            permiso_a.caso_4= True

actor_02= Esenario_de_pociciones()

