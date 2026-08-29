from ingest import save_bronze
import os
import json

def test_save_bronze_crea_archivo(tmp_path, monkeypatch):
    """save_bronce crea un archivo .json con los datos que recibio"""
    #monkeypatch.chdir cambia el directorio de trabajo solo en esta prueba,
    # a una carpeta de prueba temporal que crea pytest y luego borra automaticamente (tep_path)
    # para no danar la carpeta real /bronze

    monkeypatch.chdir(tmp_path)
    os.makedirs("bronze")

    datos_prueba = [{"id": 121, "price": 100000}]
    path = save_bronze(datos_prueba, "30311")

    # Valida que el archivo realmente se creo.
    assert os.path.exists(path)

    # Valida que el contenido es lo mismo que pasamos en la funcion.
    with open(path, encoding="utf-8") as f:
        contenido = json.load(f)
    assert contenido == datos_prueba

def test_bronze_nombre_incluye_zip(tmp_path, monkeypatch):
    """ El nombre del archivo debe incluir el zip code para ser trazabel. """
    monkeypatch.chdir(tmp_path)
    os.makedirs("bronze")

    path = save_bronze([{"id": 1}], "78732")
    assert "78732" in path
