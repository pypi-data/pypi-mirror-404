
print("\
\n\
Comenzare explicando los cuatro funcionamientos que \n\
no utilizan ventanas. Estos cuatro tipos tiene cada uno \n\
su propio configuracion de atributos de entrada, \n\
que son los que quiero explicar aqui, y son: \n\
\n\
ESTE ES VACIO (NO CONTIENE ATRIBUTOS) \n\
1. gentil( ) \n\
Funcionamiento: Recorre cada uno de estos \n\
sin excepcion hasta el final. \n\
\n\
CON DOS ATRIBUTOS DE ENTRADAS \n\
2. gentil( int, str ) \n\
Funcionamiento: Segun sea el numero del 1er gentil \n\
que encuentre... todos (del resto) de gentiles tambien \n\
seran ejecutados. los que tengan un numero diferente \n\
no seran ejecutados. \n\
ademas, el segundo atributo puede ser solo una de (2) dos \n\
posibles palabras, para este caso deberia ser 'serie'. \n\
Un ejemplo para este caso seria: \n\
gentil( 1, 'serie' ) \n\
gentil( 3, 'serie' ) \n\
gentil( 1, 'serie' ) \n\
gentil( 1, 'serie' ) \n\
gentil( 2, 'serie' ) \n\
Aqui se mostrarian (3) tres visor_varis (los numeros 1) \n\
pero si al primero se le cambia el 1 por el 2 \n\
gentil( 2, 'serie' ) \n\
gentil( 3, 'serie' ) \n\
gentil( 1, 'serie' ) \n\
gentil( 1, 'serie' ) \n\
gentil( 2, 'serie' ) \n\
se mostrarian (2) dos visor_varis (los numeros 2) \n\
\n\
TRABAJA TAMBIEN CON DOS ATRIBUTOS \n\
3. gentil( int, str ) \n\
Funcionamiento: Si, este tipo, emplea lo mismo que el \n\
anterior, de hecho la palabra STR es la misma: 'serie'. \n\
Lo que hace cambiar el comportamiento de esta, es que, \n\
antes de, el interprete encontrarse con el 1er gentil debera \n\
encontrarse con una funcion 'riel( int, int )' que deberas \n\
importarla desde el modulo visorquipus e ingresarle uno \n\
o dos enteros. \n\
Con este entero usted podra ver solo uno o dos \n\
gentiles, no mas, de todos los que tiene la linea habilitada \n\
para que se ejecute \n\
(asi como se explico en el caso 2 que pueden haber varios \n\
y solo serán ejecutadas... los 5 por ejemplo: gentil( 5, 'serie' ) ) \n\
Este tipo es muy flexible porque puede pasar del tipo 2 al 3 \n\
solo predefiniendo riel( ). O del 3 al 2 solo quitandoselo. \n\
Un ejemplo: \n\
riel( 0, 1 ) \n\
gentil( 1, 'serie' ) # Este se mostrará \n\
gentil( 3, 'serie' ) \n\
gentil( 1, 'serie' ) # Este se mostrará \n\
gentil( 1, 'serie' ) # Este, sin embargo, no se mostrará \n\
gentil( 2, 'serie' ) \n\
otro... \n\
riel( 1 ) \n\
gentil( 1, 'serie' ) # Este, sin embargo, no se mostrará \n\
gentil( 3, 'serie' ) \n\
gentil( 1, 'serie' ) # Este se mostrará \n\
gentil( 1, 'serie' ) # Este, sin embargo, no se mostrará \n\
gentil( 2, 'serie' ) \n\
\n\
REQUIERE DOS ATRIBUTOS DE ENTRADA \n\
4. gentil( int, str ) \n\
Funcionamiento: Este tipo o forma de emplear visor_vari es \n\
parecida a la anterior, pero ocure que, la palabra STR \n\
del segundo atributo es 'paralelo'. \n\
Y si, tambien hace uso de riel( ), pero demas... a esto, \n\
deberas incorporar otra funcion como importacion, \n\
que se encuentra ubicada en el modulo visorquipus. \n\
y se llama 'ultimate'. \n\
La diferencia con todos los demas tipo de funcionamiento, \n\
es que este, hace funcionar todas las lineas de pulso \n\
una por una. Ejemplo: \n\
gentil( 1, 'paralelo' ) \n\
gentil( 2, 'paralelo' ) \n\
gentil( 1, 'paralelo' ) \n\
gentil( 2, 'paralelo' ) \n\
En este ejemplo, hace sacar primero los dos 1 y \n\
despues, muestra los valores de los gentiles 2. \n\
Por supuesto que aqui riel sería riel( 0, 1 ) y asi mostraria \n\
ambos de cada linea. pero como mencione anteriormente tambien \n\
puede funcionar con un solo atributo si usted quiere. \n\
Pero debo mencionar que para este caso o tipo \n\
de ejecucion se le permitio a riel pasar por atributo \n\
una lista segun el punto que se quiera ver de cada linea \n\
y su posible siguiente gentil. \n\
ejemplo: \n\
riel( list ) # muestra los puntos indicados en la lista, respectivamente. \n\
... \n\
otro ejemplo: \n\
riel( list, True ) # muestra los puntos y ademas los adyacentes debajo. \n\
... \n\
Quitandole el None al segundo atributo, con True, podra ver ademas \n\
el supuesto siguiente gentil, aparte del que fue señalado en la linea \n\
en riel (que se encuentre justo debajo). \n\
Con este tipo de division usted puede visualizar que esta \n\
pasando en un objeto con los gentiles 1 y que esta \n\
pasando en los datos o instancias de otro objeto con el \n\
gentil 2. \n\
\n\
PARA EL CASO DE LAS VENTANAS \n\
(de momentos solo tkinter) \n\
tienen todas las cuatro tambien el mismo funcionamiento \n\
sin embargo y por supuesto que la sentencia incluye \n\
pasar el objeto de la ventana por atributo, esto es asi: \n\
self.mi_vent= tk.TK( ) \n\
gentil( int, str, objeto ) \n\
Es claro que: 'mi_vent' es una instancia de objeto. \n\
")

