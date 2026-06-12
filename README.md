# DataPulse E-commerce — Pipeline de Datos

Pipeline de datos para **TiendaConecta SpA**, una tienda online que vende productos de varias categorías (electrónica, ropa, hogar, deportes, etc).

El objetivo de este proyecto es tomar los datos "sucios" de la tienda (clientes, productos, pedidos y devoluciones) y dejarlos limpios, validados y guardados en una base de datos relacional, lista para hacer reportes o análisis.

## ¿Qué hace el pipeline?

El proceso se divide en 4 pasos, uno detrás de otro:

```
data/clientes.csv  ─┐
data/productos.csv  ├──▶ 1. INGESTA ──▶ 2. LIMPIEZA ──▶ 3. VALIDACIÓN ──▶ 4. CARGA ──▶ MySQL/MariaDB
data/pedidos.csv    │
data/devoluciones.csv ─┘
```

### 1. Ingesta (`ingesta.py`)
Lee los 4 archivos CSV originales, revisa cómo vienen (cuántas filas, columnas, datos vacíos, duplicados) y guarda una copia de respaldo en `data/raw/respaldo/` por si algo sale mal después.

### 2. Limpieza (`limpieza.py`)
Arregla los problemas típicos de los datos:
- Elimina filas duplicadas
- Rellena o elimina datos vacíos
- Corrige formatos de fecha
- Estandariza textos (mayúsculas/minúsculas, espacios)
- Recalcula el total de los pedidos para que sea correcto
- Crea columnas nuevas útiles (ej: rango de edad, rango de precio)

### 3. Validación (`validacion.py`)
Revisa que los datos cumplan reglas básicas usando la librería `pandera`:
- Que los IDs tengan el formato correcto (ej: `C001`, `P001`)
- Que los precios, edades y descuentos estén en rangos lógicos
- Que no haya IDs duplicados

Los datos que pasan se guardan en `data/validados/` y los que fallan en `data/error/` (con el motivo del error).

### 4. Carga (`carga_datos.py`)
Crea las tablas en MySQL/MariaDB (con sus llaves primarias y foráneas) y carga ahí los datos ya validados. Si algo falla, no se guarda nada a medias (rollback automático).

## Estructura del proyecto

```
├── main.py              ← ejecuta todo el pipeline de una vez
├── scrips/
│   ├── ingesta.py
│   ├── limpieza.py
│   ├── validacion.py
│   └── carga_datos.py
├── data/
│   ├── clientes.csv, productos.csv, pedidos.csv, devoluciones.csv
│   ├── raw/respaldo/    ← copias originales
│   ├── processed/       ← datos limpios
│   ├── validados/       ← datos que pasaron la validación
│   └── error/           ← datos rechazados (con motivo)
└── logs/                 ← un log por cada etapa
```

## Cómo correrlo

### 1. Instalar dependencias

```bash
pip install pandas pandera sqlalchemy mysql-connector-python --break-system-packages
```

### 2. Tener una base de datos lista

Necesitas MySQL o MariaDB corriendo, con una base de datos llamada `ecommerce`:

```sql
CREATE DATABASE ecommerce;
```

### 3. Configurar la conexión

En `scrips/carga_datos.py`, cambia el usuario y contraseña según tu configuración:

```python
engine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://usuario:contraseña@localhost/ecommerce"
)
```

### 4. Ejecutar todo el pipeline

```bash
python main.py
```

Esto corre las 4 etapas en orden y deja todo registrado en `logs/`.

### También se puede correr cada etapa por separado

```bash
python scrips/ingesta.py
python scrips/limpieza.py
python scrips/validacion.py
python scrips/carga_datos.py
```

## Resultado final

Al terminar, en la base de datos `ecommerce` quedan 4 tablas conectadas entre sí:

- **clientes** — información de los clientes
- **productos** — catálogo de productos
- **pedidos** — compras (conectado a clientes y productos)
- **devoluciones** — devoluciones (conectado a pedidos y clientes)

## Equipo

| Integrante | Rol |
|---|---|
| Fernando Villalobos | Desarrollo del pipeline (ingesta, limpieza, validación, carga) |
| Nicolás Sotomayor | Desarrollo del pipeline (ingesta, limpieza, validación, carga) |
| Joan Rojas | Documentación (README) |
| Felipe Arriagada | Presentación y planificación |
