import chardet
import pandas as pd
def get_encoding(uploaded_file):
    content = uploaded_file.read()               # bytes
    # Detectar la codificación del archivo
    result = chardet.detect(content)
    # Obtener la codificación
    encoding = result['encoding']
    return encoding

def txt_to_df(uploaded_file)->pd.DataFrame:
    content = uploaded_file.read()               # bytes
    encoding = chardet.detect(content)['encoding']
    if encoding is None:
        print("No se pudo detectar la codificación del archivo.")
        encoding = "latin-1"
    text = content.decode(encoding)              # str
    data = text.splitlines()                    # lista de líneas

    data = [i.split('\t') for i in data]
    # eliminar el \n del final de cada linea
    data = [[i.replace('\n','') for i in j] for j in data]
    # pasar a dataframe
    df = pd.DataFrame(data, columns = data[0])
    # eliminar la primera fila
    df = df.drop(0)
    df = df.reset_index(drop=True)

    return df