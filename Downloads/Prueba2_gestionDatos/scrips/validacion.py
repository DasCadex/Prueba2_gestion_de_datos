import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check
import os
import logging
from datetime import datetime
import pandera.pandas as pa

os.makedirs("logs",exist_ok=True)
os.makedirs("data/validados",exist_ok=True)
os.makedirs("data/error",exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/validacion.log"),
        logging.StreamHandler()
    ]
)

#definimos el esquema de validacion para la tabla clientes
schema_clientes = DataFrameSchema({
   
    "cliente_id": Column(str, Check.str_matches(r"^C\d{3}$")),#le decimos que el id debe empezar con la c y tener 3 digitos numericos y que es un string 
    
    "email":      Column(str, Check.str_matches(r".+@.+\..+"), nullable=True),#le decimos que el email sea string y que cumpla con un @ y un punto y que puede ser nulo
    
    "edad":       Column(float, Check.between(0, 120), nullable=True),#que se aun float y entre un rango de 
    "nombre":     Column(str,   nullable=True),#que sea un string y que puede ser nulo
    "ciudad":     Column(str,   nullable=True),#que sea un string y que puede ser nulo
    "genero":     Column(str,   Check.isin(["Masculino", "Femenino", "Otro","masculino","femenino","otro"]), nullable=True),#que sea un string y que solo pueda ser M, F o Otro y que puede ser nulo
},
    #en esta parte le decimos que no puede haber cliente_id duplicados, es decir que cada cliente_id debe ser unico
    checks=Check(lambda df: ~df["cliente_id"].duplicated().any(),
                 error="cliente_id duplicado")
)

schema_productos = DataFrameSchema({
    "producto_id": Column(str,   Check.str_matches(r"^P\d{3}$")),
    "precio":      Column(float, Check.greater_than(0)),          
    "stock":       Column(int,   Check.greater_than_or_equal_to(0)),  
    "activo": Column(str, Check.isin(["Sí", "No", "No especificado"]), nullable=True),                                   #
    "categoria":   Column(str,   nullable=True),
})

schema_pedidos = DataFrameSchema({
    "pedido_id":       Column(str,   Check.str_matches(r"^O\d{4}$")),   
    "cantidad":        Column(float, Check.greater_than(0)),            
    "descuento_pct":   Column(float, Check.between(0, 100)),             
    "precio_unitario": Column(float, Check.greater_than(0), nullable=True),
    "estado":          Column(str,   Check.isin(["completado","pendiente","enviado","cancelado"]), nullable=True),
},
    checks=[
        # le decimos que el total calculado (precio_unitario * cantidad) debe ser positivo ademas no puede ser 0 
        Check(lambda df: (df["precio_unitario"] * df["cantidad"] > 0).all(),
              error="total calculado debe ser positivo"),
        #en esta parte le decimos que no puede haber pedido_id duplicados, es decir que cada pedido_id debe ser unico
        Check(lambda df: ~df["pedido_id"].duplicated().any(),
              error="pedido_id duplicado"),
    ]
)

schema_devoluciones = DataFrameSchema({
    "devolucion_id":   Column(str,   Check.str_matches(r"^D\d{3}$")),
    "monto_reembolso": Column(float, Check.greater_than_or_equal_to(0)),  
    "estado_devolucion": Column(str, Check.isin(["aprobada","rechazada","pendiente"])),  
    "motivo":          Column(str,   nullable=True),                       
})

ESQUEMAS = {
    "clientes":     schema_clientes,
    "productos":    schema_productos,
    "pedidos":      schema_pedidos,
    "devoluciones": schema_devoluciones,
}


def validar(nombre, schema):
    ruta = f"data/processed/{nombre}_clean.csv"
    if not os.path.exists(ruta):
        logging.error(f"No existe: {ruta}")
        return

    df = pd.read_csv(ruta)
    logging.info(f"=== Validando: {nombre} ({len(df)} filas) ===")

    validos   = []
    invalidos = []

    # Validar fila por fila para separar válidos de inválidos
    for i, row in df.iterrows():
        fila = pd.DataFrame([row])
        try:
            schema.validate(fila, lazy=True)
            validos.append(row)
        except pa.errors.SchemaErrors as e:
            row["error_validacion"] = str(e.failure_cases["failure_case"].values)
            invalidos.append(row)

    df_validos   = pd.DataFrame(validos)
    df_invalidos = pd.DataFrame(invalidos)

    df_validos.to_csv(f"data/validados/{nombre}_validados.csv",  index=False)
    df_invalidos.to_csv(f"data/error/{nombre}_error.csv",      index=False)

    logging.info(f"Válidos:   {len(df_validos)}")
    logging.info(f"Inválidos: {len(df_invalidos)}")


if __name__ == "__main__":
    logging.info("====== ETAPA 3: VALIDACIÓN ======")
    inicio = datetime.now()
    for nombre, schema in ESQUEMAS.items():
        validar(nombre, schema)
    logging.info(f"Tiempo: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 3 ======")

def ejecutar_validacion():
    logging.info("====== ETAPA 3: VALIDACIÓN ======")
    inicio = datetime.now()
    for nombre, schema in ESQUEMAS.items():
        validar(nombre, schema)
    logging.info(f"Tiempo: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 3 ======")