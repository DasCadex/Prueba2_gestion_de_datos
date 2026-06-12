import pandas as pd 
import os 
import shutil
import logging 
from datetime import datetime 


os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")


os.makedirs('logs',exist_ok=True)
os.makedirs('data/processed',exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/limpieza.log"),
        logging.StreamHandler()
    ]

)
def rango_etario(edad):#definimos una funcion para clasificar a los clientes en rangos etarios
        if edad < 25:   return "joven"#si la edad es menor a 25 lo clasifica como joven
        elif edad < 45: return "adulto"
        elif edad < 65: return "adulto_mayor"
        else:           return "senior"

def limpieza_clientes(df):
    logging.info("inciando liempieza de usuario / clientes :D")

    antes= len(df)#contamos el numero de filas antes de eliminar los duplicados
    df =df.drop_duplicates()#eliminamos los duplicados

    logging.info(f"datos duplicados eliminados: {antes-len(df)}")

    # rellenamos los valores nulos 
    df['nombre'] = df['nombre'].fillna("desconocido")
    df['email']= df['email'].fillna("sin_correo@gmail.com")
    df['edad']    = pd.to_numeric(df['edad'], errors="coerce")
    df['edad'] = df['edad'].fillna(df['edad'].median())

    df = df[df['edad'].between(0, 120)]

    #correcion de datos letras ( espacion en blanco etx)

    df['ciudad']= df['ciudad'].str.strip().str.title()
    df['nombre']= df['nombre'].str.strip().str.title()
    df['pais']=df['pais'].str.strip().str.upper()#con el upper lo pasamos a mayusculas

    #correcion del genero 

    df['genero']= df['genero'].replace({'M': 'Masculino', 'F': 'Femenino', 'O': 'Otro','m': 'Masculino','f': 'Femenino','o': 'Otro'})#corregimos la columna genero para que sea mas legible y consistente

    

    

    df['rango_etario'] = df['edad'].apply(rango_etario)#aplicamos la funcion a la columna edad para crear una nueva columna con el rango etario

    logging.info("Columna nueva creada: rango_etario")

    
    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"], errors="coerce")#convertimos la columna fecha_registro a formato datetime, si hay errores los convertimos a NaT (Not a Time)
    df["fecha_registro"] = df["fecha_registro"].dt.strftime("%Y-%m-%d")

    logging.info(f"Clientes limpios: {len(df)} filas")
    return df


#limpieza productos 


def limpiar_productos(df):
    logging.info("iniciando la limpieza de productos :D")

    df=df.drop_duplicates()#eliminamos los duplicados
    #nulos y tipos 
    df['precio']  = pd.to_numeric(df['precio'],  errors="coerce")#convertimos a numerico, si hay errores los convertimos a NaN
    df['stock']   = pd.to_numeric(df['stock'],   errors="coerce").fillna(0).astype(int)#convertimos a numerico, si hay errores los convertimos a NaN, luego los rellenamos con 0 y finalmente los convertimos a enteros
    df['peso_kg'] = pd.to_numeric(df['peso_kg'], errors="coerce")#convertimos a numerico, si hay errores los convertimos a NaN


    #eliminanmos filas con numeros negativos o precio 0
    df = df[df['precio'] > 0]#eliminamos los productos con precio menor o igual a 0
    df = df[df['stock']  >= 0]#eliminamos los productos con stock negativo

    df['activo'] = df['activo'].astype(str).str.strip().str.lower()
    df['activo'] = df['activo'].replace({
        'true': 'Sí', '1': 'Sí', 'si': 'Sí', 'sí': 'Sí',
        'false': 'No', '0': 'No', 'no': 'No',
        'none': 'No especificado', 'nan': 'No especificado'
    })

    df['categoria'] = df['categoria'].str.strip().str.title()


    df['rango_precio'] = pd.cut(
        df['precio'],
        bins=[0, 50, 200, float("inf")],
        labels=["economico", "medio", "premium"]
    )

    logging.info(f"Productos limpios: {len(df)} filas")
    return df

def limpieza_pedidos(df):
    logging.info("iniciando la limpiezax de los pedidos :D")
    df=df.drop_duplicates()#eliminamos los duplicados

    df['cantidad']        = pd.to_numeric(df['cantidad'],        errors="coerce")#convertimos a numerico, si hay errores los convertimos a NaN
    df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors="coerce")
    df['descuento_pct']   = pd.to_numeric(df['descuento_pct'],   errors="coerce").fillna(0)
    df['total']           = pd.to_numeric(df['total'],           errors="coerce")

    #eliminamos cosas que sean sera ( ya que es imposible xd)
    df = df[df['cantidad'] > 0]
    df = df[df['precio_unitario'] > 0]

    #correguimos formato de texto y eliminamos espacios en blanco
    df['estado']      = df['estado'].str.strip().str.lower()
    df['metodo_pago'] = df['metodo_pago'].str.strip().str.lower()

    #recalculamos el total para asegurarnos de que sea correcto, ya que a veces puede haber errores en los datos originales
    df['total'] = (df['precio_unitario'] * df['cantidad'] * (1 - df['descuento_pct'] / 100)).round(2)
    logging.info("Total recalculado correctamente")

    #creamos una nueva columna para indicar si el pedido tiene descuento o no 

    df['tiene_descuento'] = df['descuento_pct'] > 0
    #si el porcentaje de descuento es mayor a 0, entonces tiene descuento

    df['cantidad']      = df['cantidad'].astype(float)
    df['descuento_pct'] = df['descuento_pct'].astype(float)

    df['fecha_pedido'] = pd.to_datetime(df['fecha_pedido'], errors="coerce")#convertimos la fecha en datetime, si hay error lo pasara a ant 
    df['fecha_pedido'] = df['fecha_pedido'].dt.strftime("%Y-%m-%d")#pasamo la fecha a string 
    df = df.dropna(subset=['fecha_pedido', 'cliente_id', 'producto_id'])#eliminamos los pedidos que no tengan fecha , el cliente y el producto 

    logging.info(f"Pedidos limpios: {len(df)} filas")
    return df

def limpieza_devoluciones(df):
    logging.info("inicinado limpieza de devoluciones :D")
    df=df.drop_duplicates()#eliminamos los duplicados

    df['monto_reembolso']= pd.to_numeric(df['monto_reembolso'], errors="coerce").fillna(0)#convertimos en numero y relenamos los nulos con 0 

    df = df[df['monto_reembolso'] > 0]# el momnto no puedo ser 0 o negativo 

    #pasamos a minusculas y eliminamos espacios en blanco
    df['motivo']= df['motivo'].str.strip().str.lower().fillna("sin motivo")
    df['estado_devolucion'] = df['estado_devolucion'].str.strip().str.lower()


    #remplazamos los estados de devolucion 
    df['estado_devolucion']=df['estado_devolucion'].replace({'pendiente': 'procesando', 'completada': 'completada', 'rechazada': 'rechazada'})

    df['fecha_devolucion'] = pd.to_datetime(df['fecha_devolucion'], errors="coerce")
    df['fecha_devolucion'] = df['fecha_devolucion'].dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=['fecha_devolucion', 'pedido_id'])

    logging.info(f"Devoluciones limpias: {len(df)} filas")
    return df

def ejecutar_limpieza():
    logging.info("====== ETAPA 2: LIMPIEZA ======")
    inicio = datetime.now()

    funciones = {
        "clientes":     limpieza_clientes,
        "productos":    limpiar_productos,
        "pedidos":      limpieza_pedidos,
        "devoluciones": limpieza_devoluciones,
    }

    for nombre, funcion in funciones.items():
        ruta = f"data/raw/{nombre}.csv"
        if not os.path.exists(ruta):
            logging.error(f"No existe: {ruta}")
            continue
        df = pd.read_csv(ruta)
        df_limpio = funcion(df)
        df_limpio.to_csv(f"data/processed/{nombre}_clean.csv", index=False)
        logging.info(f"Guardado: data/processed/{nombre}_clean.csv")

    logging.info(f"Tiempo: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 2 ======")

if __name__ == "__main__":
    ejecutar_limpieza()



