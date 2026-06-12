import pandas as pd 
import os 
import shutil
import logging 
from datetime import datetime 

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.makedirs('logs', exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("data/raw/respaldo", exist_ok=True)

#iniciamos el logging para que pueda registrar los eventos de la ingesta de datos, tanto en un archivo como en la consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ingesta.log"),
        logging.StreamHandler()
    ]

)

ARCHIVOS = {#definimos un diccionario con los nombres de los datasets y sus rutas para que sepa donde se encuentran los archivos a ingestar
    "clientes":     "data/raw/clientes.csv",
    "productos":    "data/raw/productos.csv",
    "pedidos":      "data/raw/pedidos.csv",
    "devoluciones": "data/raw/devoluciones.csv"
}

def ingestar_datos(nombre,ruta):#recibe el nombre del scv y su ruta 
    logging.info(f"iniciando el data set {nombre}:D")
    
    #si no encuntra los archivos csv donde le decimos dara error 
    if not os.path.exists(ruta):
        logging.error(f"archivos no encontrados en {ruta}")
        return None
    
    #cargamos los datos en un data frame 
    df=pd.read_csv(ruta)
    logging.info(f"Archivo cargado: {ruta}")#confirmamos que el archivo se ha cargado correctamente

    logging.info(f"shape: {df.shape[0]} filas y {df.shape[1]} columnas")#contamos filas y columnas 
    logging.info(f"lista : {list(df.columns)}")#mostramos las columnas del dataset

    logging.info(f"tipo de datos \n: {df.dtypes.to_string()}")#tipo de datos de cada columna 
    logging.info(f"Valores nulos por columna:\n{df.isnull().sum().to_string()}")
    logging.info(f"Duplicados: {df.duplicated().sum()}")


    #respaldo archivos origuinales
    respaldo  = (f"data/raw/respaldo/{nombre}.csv")#donde los guardara 
    shutil.copy(ruta, respaldo)#antes de hacer todo los gurda 
    logging.info(f"Copia guardada en: {respaldo}")#mensaje 

    logging.info(f"=== Ingesta finalizada: {nombre} ===\n")
    return df

#bloque de ejecucion del script 
def ejecutar_ingesta():
    logging.info("====== INICIO PIPELINE - ETAPA 1: INGESTA ======")#mensaje de inicio del proceso de ingesta
    inicio = datetime.now()#le decimos que tome el timpo desde que se ejecuta el programa 

    datasets = {}#definimos un diccionario vacio para guardar los data frames de cada dataset que se ingesten
    for nombre, ruta in ARCHIVOS.items():#
        df = ingestar_datos(nombre, ruta)#
        if df is not None:
            datasets[nombre] = df

    logging.info(f"Tablas ingestadas: {list(datasets.keys())}")
    logging.info(f"Tiempo total: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 1: INGESTA ======")

if __name__ == "__main__":
    ejecutar_ingesta()