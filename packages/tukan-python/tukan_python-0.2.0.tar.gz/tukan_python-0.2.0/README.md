# Tukan Python SDK

[![PyPI version](https://badge.fury.io/py/tukan_python.svg)](https://badge.fury.io/py/tukan_python)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Tukan](https://tukanmx.com) es la plataforma de datos más completa de México.

Si estás en búsqueda de una forma sencilla y eficiente para acceder a todos las estadísticas oficiales de la economía mexicana desde Python, esta es la solución para ti.

## Descripción

Tukan agrega y estandariza fuentes oficiales de datos públicos como INEGI, Banxico, CNBV, CNSF, CONSAR, entre otras. 

Este SDK permite consultar y analizar estos datos de forma sencilla desde Python.

Para acceder a la gran variedad de datos disponibles es necesario contar con un token y una suscripción activa en [Tukan](https://tukanmx.com). Sin embargo, algunas tablas pueden ser consultadas de forma gratuita.


## Instalación

```bash
pip install tukan_python
```

## Autenticación

Para obtener tu token debes primero regidstrarte en [Tukan](https://app.tukanmx.com/user/register).

Luego, podrás encontrar tu token en el [panel de usuario](https://app.tukanmx.com/account/).

![Token panel](images/token_panel.png)

Una vez obtenido tu token, puedes configurarlo como una variable de entorno

```bash
export API_TUKAN="tu_token_aqui"
```

o en un archivo `.env`:

```
API_TUKAN=tu_token_aqui
```

Otra alternativa es pasar el token directamente al inicializar el cliente:

```python
from tukan_python import Tukan

tukan = Tukan(token="tu_token_aqui")
```

## Inicio rápido

```python
from tukan_python import Query

# Consultar tipo de cambio FIX (MXN por USD)
q = Query()
q.set_table_name("mex_banxico_cf102")
q.add_date_filter("date", "2025-01-01", "2025-01-15")
q.add_date_reference_to_group_by("date", level="as_is")
q.add_aggregate("be08668718242ff", ["identity"])  # Tipo de cambio FIX
q.set_language("es")

resultado = q.execute_query()
print(resultado["df"])
```

Salida:
```
         date        indicator    value
0  2025-01-02  be08668718242ff  20.6917
1  2025-01-03  be08668718242ff  20.6708
2  2025-01-06  be08668718242ff  20.3195
3  2025-01-07  be08668718242ff  20.3440
4  2025-01-08  be08668718242ff  20.3823
...
```

## Ejemplos

### 1. Explorar tablas disponibles

```python
from tukan_python import Tukan

tukan = Tukan()

# Listar todas las tablas
tablas = tukan.all_tables()
print(f"Tablas disponibles: {len(tablas)}")

# Filtrar tablas de CNBV y ordenar alfabéticamente
cnbv = [t for t in tablas if t["id"].startswith("mex_cnbv")]
cnbv.sort(key=lambda x: x["id"])

for t in cnbv[:5]:
    print(f"- {t['id']}: {t['name']}")
```

Salida:
```
Tablas disponibles: 150+
- mex_cnbv_cb_balance_sheet_ifrs9: Instituciones de Banca Múltiple - Balance General Detallado (IFRS9)
- mex_cnbv_cb_capital_ratios: Instituciones de Banca Múltiple - Índice de Capitalización
- mex_cnbv_cb_ccl: Instituciones de Banca Múltiple - Coeficiente de Cobertura de Liquidez
- mex_cnbv_cb_claims_by_channel_and_status: Instituciones de Banca Múltiple - Reclamaciones por Estatus y Canal
- mex_cnbv_cb_clients_per_product: Clientes por Producto Financiero
```

### 2. Obtener metadata de una tabla

Antes de consultar datos, es útil explorar la estructura de la tabla:

```python
from tukan_python import Tukan

tukan = Tukan()

# Obtener metadata
meta = tukan.get_table_metadata("mex_cnbv_cb_orig_by_gender_monthly", language="es")

print("Nombre:", meta["data_table"]["name"])
print("Referencias:", [r["id"] for r in meta["data_table_references"]])
print("Rango de fechas:", meta["data_table"]["date_ranges"])

# Ver indicadores disponibles
indicadores = tukan.all_indicators_for_table("mex_cnbv_cb_orig_by_gender_monthly")
for ind in indicadores:
    print(f"- {ind['ref']}: {ind['name']}")
```

Salida:
```
Nombre: Banca Múltiple - Colocación de Créditos Empresariales y de Vivienda, por Sexo
Referencias: ['end_date', 'sex', 'start_date', 'institutions', 'geography', ...]
Rango de fechas: {'end_date': {'max': '2025-11-30', 'min': '2019-12-31'}}

- 05451c0b6d5ea78: Monto colocado
- 78256b18c54451f: Número de créditos
- b577c6dfc51ebef: Tasa ponderada
```

### 3. Consultar colocación de crédito bancario por sexo

```python
from tukan_python import Query

q = Query()
q.set_table_name("mex_cnbv_cb_orig_by_gender_monthly")
q.add_date_filter("end_date", "2024-01-01", "2024-06-30")
q.add_standard_filter("institutions", ["0c959ae6bc0d063"])  # Banca múltiple (agregado)
q.add_date_reference_to_group_by("end_date", level="monthly")
q.add_non_date_reference_to_group_by("sex")
q.add_aggregate("05451c0b6d5ea78", ["sum"])  # Monto colocado
q.set_language("es")

resultado = q.execute_query()
print(resultado["df"])
```

Salida:
```
       sex__ref    end_date             indicator         value       sex
0  34e63c6a4f88758  2024-01-01  05451c0b6d5ea78__sum  1.468993e+10  Femenino
1  34e63c6a4f88758  2024-02-01  05451c0b6d5ea78__sum  1.721803e+10  Femenino
2  653a519004568cb  2024-01-01  05451c0b6d5ea78__sum  3.000290e+10  Masculino
3  653a519004568cb  2024-02-01  05451c0b6d5ea78__sum  3.302666e+10  Masculino
...
```

### 4. Consultar el INPC (inflación)

El INPC requiere filtrar por producto. Primero exploramos el catálogo:

```python
from tukan_python import Tukan, Query

tukan = Tukan()

# Ver productos disponibles
productos = tukan.get_reference_flat_tree(
    table_name="mex_inegi_inpc_original_product_monthly",
    reference="mex_inegi_cpi_product_structure",
    only_in_table=True
)
print(productos[["ref", "name"]].head(10))
```

Salida:
```
                ref                                   name
0   9329306b0b5268c                    Todos los productos
1   a38da228dc862e7            Alimentos, bebidas y tabaco
2   714d22fe124b834                              Alimentos
3   1c70d647c151be7                               Vivienda
4   da9ee7065e99719                             Transporte
...
```

Ahora consultamos el índice general:

```python
q = Query()
q.set_table_name("mex_inegi_inpc_original_product_monthly")
q.add_date_filter("date", "2024-01-01", "2024-06-30")
q.add_standard_filter("mex_inegi_cpi_product_structure", ["9329306b0b5268c"])  # Todos los productos
q.add_date_reference_to_group_by("date", level="monthly")
q.add_aggregate("c572db59b8cd109", ["identity"])  # INPC
q.set_language("es")

resultado = q.execute_query()
print(resultado["df"])
```

Salida:
```
         date        indicator    value
0  2024-01-01  c572db59b8cd109  133.555
1  2024-02-01  c572db59b8cd109  133.681
2  2024-03-01  c572db59b8cd109  134.065
3  2024-04-01  c572db59b8cd109  134.336
4  2024-05-01  c572db59b8cd109  134.087
5  2024-06-01  c572db59b8cd109  134.594
```

### 5. Explorar catálogos jerárquicos

Las referencias estándar tienen estructura jerárquica (país → estado → municipio). El catálogo incluye columnas importantes como `raw` (ID original de la fuente) e `in_table` (si el valor tiene datos en la tabla):

```python
from tukan_python import Tukan

tukan = Tukan()

# Obtener catálogo de geografía
df_geo = tukan.get_reference_flat_tree(
    table_name="mex_inegi_census_people_reduced",
    reference="geography"
)

print(df_geo[["raw", "ref", "name", "parent_ref", "in_table"]].head(10))
```

Salida:
```
      raw              ref                   name       parent_ref  in_table
0      wd  2064d512d0da97d                  Mundo            FALSE     False
1      na  e5fc8e04967fe49           Norteamérica  2064d512d0da97d     False
2     mex  b815762a2c6a283                 México  e5fc8e04967fe49      True
3  mex_10  db3b32c946ffd13                Durango  b815762a2c6a283      True
4  mex_21  bd8b4a37deee845                 Puebla  b815762a2c6a283      True
5  mex_11  a3aa918bd45ac53             Guanajuato  b815762a2c6a283      True
6  mex_24  468bc66c95ecfe6        San Luis Potosí  b815762a2c6a283      True
...
```

La columna `raw` contiene el ID original (ej: `mex_10` para Durango), mientras que `ref` es el ID interno de Tukan. Usa `only_in_table=True` para filtrar solo valores con datos.

### 6. Motor Blizzard para consultas pesadas

Para consultas con grandes volúmenes de datos, usa el motor Blizzard:

```python
from tukan_python import Query

q = Query(engine="blizzard")
q.set_table_name("mex_cnbv_cb_orig_by_gender_monthly")
# ... configurar filtros y agregaciones ...
resultado = q.execute_query()
```

## Conceptos clave

### Tablas
Cada tabla representa una fuente de datos específica. Los IDs siguen el patrón general:
`{pais}_{fuente}_{dataset}`

Ejemplos:
- `mex_inegi_inpc_original_product_monthly` - INPC de INEGI
- `mex_cnbv_cb_orig_by_gender_monthly` - Colocación de créditos de CNBV
- `mex_inegi_census_people_reduced` - Censo de población de INEGI
- `mex_shcp_budget_expenditures_by_fc` - Gastos presupuestarios de SHCP

### Indicadores
Son las métricas o valores que se pueden consultar. Cada tabla tiene sus propios indicadores con IDs únicos (ej: `c572db59b8cd109` para el INPC).

### Referencias
Son las dimensiones que contextualizan los datos:
- **date**: Fechas (pueden tener diferentes nombres como `date`, `end_date`, `start_date`)
- **standard**: Catálogos jerárquicos como `geography`, `sex`, `economic_activity`
- **free**: Texto libre
- **numeric**: Valores numéricos adicionales

### Operaciones de agregación
- `identity`: Valor original sin modificar
- `sum`: Suma de valores
- `avg`: Promedio

## Fuentes de datos

Tukan integra datos de múltiples fuentes oficiales mexicanas:

| Fuente | Datos disponibles |
|--------|-------------------|
| **INEGI** | Censos, INPC, PIB, encuestas económicas |
| **Banxico** | Tasas de interés, tipo de cambio, agregados monetarios |
| **CNBV** | Estados financieros de bancos, SOFOMES, aseguradoras |
| **SHCP** | Finanzas públicas, presupuesto, deuda |
| **CONAPO** | Proyecciones de población |

## Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

## Links

- [Sitio web](https://tukanmx.com)
- [Documentación](https://github.com/TukanMx/tukan_python#readme)
- [Reportar issues](https://github.com/TukanMx/tukan_python/issues)
