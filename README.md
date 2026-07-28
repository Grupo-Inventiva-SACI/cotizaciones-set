# Cotizaciones SET/DNIT

Aplicación en Python que obtiene de la página de cotizaciones de la DNIT los tipos de cambio históricos, los normaliza y los guarda en archivos JSON. Para el mes actual también envía la última cotización al procedimiento Oracle `WSP_TIPOS_CAMBIOS_SET`.

Las monedas procesadas son dólar estadounidense (USD), real brasileño (BRL), peso argentino (ARP), yen japonés (JPY), euro (EUR) y libra esterlina (GBP), con sus valores de compra y venta.

### Acerca del procedimiento WSP_TIPOS_CAMBIOS_SET.
Se espera que el procedimiento reciba los siguientes parámetros, por ejemplo:
```SQL

PROCEDURE WSP_TIPOS_CAMBIOS_SET(
    p_body    IN  CLOB,
    p_mensaje OUT VARCHAR2
) IS...

```
El objetivo de almacenar en la DB es contar con un histórico de estas tasas de cambios, por lo que se recomienda volcar estos datos en una tabla de historicos o en una temporal.

Se comparte un script PL/SQL de ejemplo para enfocar el desarrollo del procedimiento [WSP_TIPOS_CAMBIOS_SET](scripts/oracle/WSP_TIPOS_CAMBIOS_SET.pls) .



## Requisitos

- Python 3.9 o superior (se recomienda Python 3.12).
- Acceso HTTPS a `https://www.dnit.gov.py`.
- Acceso a la base de datos Oracle cuando se procese el mes actual.

## Configuración

Crear un archivo `.env` en la raíz del proyecto con los datos de conexión a Oracle:

```dotenv
ORAPY_PARAM1=usuario
ORAPY_PARAM2=contraseña
ORAPY_PARAM3=host
ORAPY_PARAM4=puerto
ORAPY_PARAM5=nombre_del_servicio
```

El archivo `.env` contiene información sensible y no debe incorporarse al repositorio.

## Ejecución desde Python

Ejecutar desde la raíz del proyecto:

```bash
python main.py
```

La aplicación **no recibe argumentos adicionales**: toda la configuración se obtiene del archivo `.env` y el proceso se ejecuta automáticamente.

Durante la ejecución se actualizan:

- `source.json`, con los años y meses detectados como procesados.
- `data/<año>/<mes>/rates.json`, con las cotizaciones mensuales.
- `data/<año>/rates.json`, con las cotizaciones anuales.
- `data/<año>/<mes>/<día>/rates.json`, con la cotización diaria.
- `data/latest.json`, con la última cotización obtenida.

## Build con PyInstaller

PyInstaller está incluido en `requirements.in`. La build debe realizarse desde la raíz del proyecto y en el mismo sistema operativo en el que se utilizará el ejecutable:

Build Normal

```bash
pyinstaller main.py --clean --onefile -n cotizaciones-set
```

Se puede agregar el argumento "--collect-all cryptography" si ocurre el error de compilación provocado por la librería oracledb o el error tras la conexión "No module named 'cryptography'". [Más imformación](https://github.com/oracle/python-oracledb/issues/100)

Build Linux:
```
pyinstaller main.py --onefile --clean --name cotizaciones-set --collect-all cryptography
```

El ejecutable se genera en `dist/`:

- Windows: `dist/cotizaciones-set.exe`
- Linux: `dist/cotizaciones-set`

Para desplegarlo, colocar junto al ejecutable:

- `.env`, con la configuración de Oracle.
- `source.json`, para conservar el historial de meses procesados.
- El directorio `data/`, si se desea conservar los JSON ya generados. Si no existe, la aplicación lo creará al guardar nuevas cotizaciones.

Ejemplo de distribución:

```text
cotizaciones-set/
├── cotizaciones-set.exe  # En Linux, sin extensión
├── .env
├── source.json
└── data/
```

## Ejecución del binario

En Windows:

```powershell
.\cotizaciones-set.exe
```

En Linux:

```bash
./cotizaciones-set
```

El binario tampoco utiliza argumentos de línea de comandos; debe ejecutarse sin parámetros adicionales.

## Autores

- [@Ramphire](https://github.com/Ramphire)
