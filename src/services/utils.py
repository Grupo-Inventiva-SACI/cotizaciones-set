# External import
import json
import time
import re
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import oracledb
import os
from pydantic import ValidationError
from dotenv import load_dotenv


# Local import
from ..models.base import dbModel
from .getpath import env_path

# init
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"

# Carga las variables de entorno
load_dotenv(
    dotenv_path=env_path(),
    override=True
)


def get_soup(url):
    print(f"Scraping: {url}")
    # Wait 2 seconds to avoid overloading the server
    time.sleep(2) 
    try:
        soup = BeautifulSoup(
            requests.get(
                url,
                timeout=10,
                headers={"user-agent": "Mozilla/5.0"},
                verify=True,
            ).text,
            "html.parser",
        )
        return soup
    except requests.ConnectionError as e:
        print(f"Connection Error {e}")
    except Exception as e:
        print(e)
    return None


def normalize(number):
    decimal_str = None
    thousands_separator = None
    first_character = None
    second_character = None
    for i, c in enumerate(number):
        try:
            int(c)
        except ValueError:
            if first_character is None:
                first_character = i
            else:
                if c != number[first_character]:
                    second_character = i
                    decimal_str = c
                    thousands_separator = number[first_character]
    if second_character is None:
        if first_character:
            decimal_str = number[first_character]
    normalized = number
    if thousands_separator is not None:
        normalized = normalized.replace(thousands_separator, 'T')
    if decimal_str:
        normalized = normalized.replace(decimal_str, 'D')
        normalized = normalized.replace('T', '').replace('D', '.')
    # normalized = re.findall('\d*\.?\d+', normalized) # old
    normalized = re.findall(r'\d+(?:\.\d+)?', normalized) # new - testing
    if normalized:
        normalized = normalized[0]
        if len(normalized.split('.')) > 1:
            if len(normalized.split('.')[1:][0]) > 2: 
                normalized = normalized.replace('.', '')
        return normalized
    else:
        return '0'
    
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

########################################################################################

# Database Utilities

class orcl:
    def __init__(self):
        try:
            self.db_config = dbModel(
                user=os.environ["ORAPY_PARAM1"],
                password=os.environ["ORAPY_PARAM2"],
                host=os.environ["ORAPY_PARAM3"],
                port=os.environ["ORAPY_PARAM4"],
                service_name=os.environ["ORAPY_PARAM5"]
            )
        except KeyError as e:
            raise ValueError(f"Falta la variable de entorno: {e}")
        except ValidationError as exc:
            mensajes = [
                error["msg"].removeprefix("Value error, ")
                for error in exc.errors(
                    include_input=False,
                    include_url=False,
                )
            ]
            raise ValueError(
                "Error en los parámetros de conexión: "
                + "; ".join(mensajes)
            ) from exc

        self.conn = None
        self.cursor = None

    def conectar(self):
        """
        Establece conexión con la base de datos y prepara cursor.
        """
        if self.conn and self.conn.is_healthy():
            return True  # Ya conectado

        try:
            self.conn = oracledb.connect(
                user=self.db_config.user,
                password=self.db_config.password,
                host=self.db_config.host,
                port=self.db_config.port,
                service_name=self.db_config.service_name
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            raise ValueError(f"[ERROR] No se pudo establecer la conexión con la Base de Datos. -.ERR: {e}")

    def desconectar(self):
        """
        Cierra el cursor y la conexión si existen.
        """
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
                print("Cursor cerrado.")
            if self.conn:
                self.conn.close()
                self.conn = None
                print("Conexión cerrada.")
        except Exception as e:
            print(f"[ERROR] Cerrando conexión: {e}")

    def ejecutar_funcion(self, nombre_funcion: str, tipo_retorno, parametros: tuple):
        """
        Ejecuta una función PL/SQL y retorna el resultado.
        """
        if self.conn:
            try:
                return self.cursor.callfunc(nombre_funcion, tipo_retorno, parametros)
            except oracledb.DatabaseError as dberr:
                self.conn.rollback()
                self.desconectar()
                raise ValueError(f"Error al ejecutar la función {nombre_funcion}. -.ERR: {dberr}")
            except Exception as e:
                # print(f"[ERROR] Ejecutando función {nombre_funcion}: {e}")
                self.desconectar()
                raise ValueError(f"[ERROR] No se pudo ejecutar la llamada a la funcion -.ERR: {e}")
            finally:
                self.desconectar()

    def ejecutar_procedimiento(self, nombre_proc, j_body):
        """
        Ejecuta un procedimiento almacenado.
        """

        if self.conn:
            try:
                #Init variables
                mensaje = self.cursor.var(str)

                # Exec procedure
                # self.cursor.execute(f"BEGIN {nombre_proc}(:body, :mensaje); END;", body=j_body, mensaje=mensaje)
                self.cursor.callproc(nombre_proc, [j_body, mensaje])

                # Confirmar transacción
                self.conn.commit()

                mensaje = mensaje.getvalue(0)

            except oracledb.DatabaseError as dberr:
                self.conn.rollback()
                mensaje = f"[ERROR] No se pudo ejecutar el procedimiento {nombre_proc}: {dberr}"
                raise ValueError(mensaje)
            
            except Exception as e:
                mensaje = f"[ERROR] No se pudo ejecutar el procedimiento {nombre_proc} debido a un error de la app: {e}"
                raise ValueError(mensaje)
            
            finally:
                self.desconectar()

        else:
            raise ValueError(f"[ERROR] Se perdió la conexión con la Base de Datos durante la ejecución del procedimiento.")
        
        return mensaje

    def parametros(self, modulo: str, clave: str):
        """
        Devuelve el valor del parámetro consultando W_BUSCA_PARAMETRO.
        """
        return self.ejecutar_funcion("W_BUSCA_PARAMETRO", str, (modulo, clave))

    def check_conexion(self):
        """
        Verifica si se puede conectar a la base y devuelve versión.
        """
        if not self.conectar():
            return f"[ERROR] No se pudo establecer la conexión con la Base de Datos."
        try:
            version = f"Conectado a Oracle. Versión: {self.conn.version}"
            return version
        finally:
            self.desconectar()

