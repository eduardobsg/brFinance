from typing import List, Text, Dict
from dataclasses import dataclass
import ssl
import urllib.request
from io import BytesIO
from zipfile import ZipFile
from urllib.parse import urljoin
from fake_useragent import UserAgent
from logging import exception
import os
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from re import findall
from datetime import datetime, timedelta
import lxml.html as LH
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
# from anticaptchaofficial.recaptchav2proxyless import *
from selenium.webdriver.support.ui import WebDriverWait
#from sqlalchemy import create_engine
import warnings
import string
import re
from bs4 import BeautifulSoup
import requests
import glob
import time
import os
import platform
ssl._create_default_https_context = ssl._create_unverified_context
warnings.simplefilter(action='ignore', category=FutureWarning)


def getHTML(url):
    print(url)

    ua = UserAgent()
    print(str(ua.chrome))
    headers = {
        'User-Agent': str(ua.chrome)}
    html_content = ""
    while True:
        try:
            html_content = requests.get(
                url, headers=headers, timeout=5, verify=False).content.decode("utf8")
            break
        except:
            print("Tentando Novamente...")
            continue

    return html_content


# def to_alchemy(df, table, connect, chunk=True):
#     """
#     Using a dummy table to test this call library
#     """
#     if chunk:
#         try:
#             engine = create_engine(connect)
#             df.to_sql(
#                 table,
#                 con=engine,
#                 index=False,
#                 if_exists='append'
#             )
#             print(table + " inserido no banco com sucesso!")
#         except Exception as exp:
#             if "duplicate key value violates unique constraint" in str(exp):
#                 print("Entrada já existe.")
#             else:
#                 print(exp)
#     else:
#         engine = create_engine(connect)
#         for index, row in enumerate(df.index):
#             print(index)
#             try:
#                 dfAUX = df.loc[df.index == index]
#                 dfAUX.to_sql(
#                     table,
#                     con=engine,
#                     index=False,
#                     if_exists='append'
#                 )
#                 print(table + " inserido no banco com sucesso!")
#             except Exception as exp:
#                 if "duplicate key value violates unique constraint" in str(exp):
#                     print("Entrada já existe.")
#                 else:
#                     print(exp)


# def from_alchemy(table, connect):
#     """
#     Using a dummy table to test this call library
#     """
#     engine = create_engine(connect)
#     try:
#         df = pd.read_sql_table(table,
#                                con=engine)
#         print(table + " lido com sucesso!")
#         return df
#     except Exception as exp:
#         if "duplicate key value violates unique constraint" in str(exp):
#             print("Entrada já existe.")
#         else:
#             print(exp)


def iniciarChromeDriver(hidden: bool=True) -> webdriver:
    """
    Instantiate a webdriver object with different settings depending of OS you are using
    """

    os.environ['WDM_LOG_LEVEL'] = '0'
    system = str(platform.system())
    
    if system == "Windows" or system == "Darwin":
        # Options for windows
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        if hidden:
            options.add_argument("--headless")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument('user-agent={userAgent}'.format(userAgent=UserAgent().chrome))
        root = os.path.dirname(os.path.abspath(__file__))
        prefs = {"download.default_directory": root + "/downloads"}
        options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    else:
        # Options for linux
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument("--headless")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument('user-agent={userAgent}'.format(userAgent=UserAgent().chrome))

        driver = webdriver.Chrome(options=options)

    return driver


def wait_pageload(driver, tipo):
    """
    Wait page load certain elements depending on the page before continues.

    Improve!!!!
    """

    if tipo == "hash":
        timeWait = 5
        timePass = 1
        hash = driver.find_element_by_xpath(
            "//html/body/form/input[8]").get_attribute("value")
        while hash == "" and timePass <= timeWait:
            time.sleep(1)
            timePass += 1
            hash = driver.find_element_by_xpath(
                "//html/body/form/input[8]").get_attribute("value")
            if hash != "":
                return hash
        return None

    elif(tipo == "CECVM"):
        timeWait = 5
        timePass = 1
        linhasCarregadas = driver.find_element_by_xpath(
            "//html/body/form[1]/div[5]/div/div[3]").text
        while linhasCarregadas == "Mostrando de 0 até 0 de 0 registros" and timePass <= timeWait:
            time.sleep(1)
            timePass += 1
            linhasCarregadas = driver.find_element_by_xpath(
                "//html/body/form[1]/div[5]/div/div[3]").text
            if linhasCarregadas != "Mostrando de 0 até 0 de 0 registros":
                return
        return None


# def serverConn(type, server, db, user, psw):
#     """
#     Create connection to postgresql database
#     """

#     print("Conectando ao servidor...")

#     if type == 'postgresql':
#         connStr = 'postgresql://{user}:{psw}@{server}/{db}'.format(
#             user=user, psw=psw, server=server, db=db)
#         alchemyEngine = create_engine(connStr, pool_recycle=3600)
#         conn = alchemyEngine.connect()
#         print("Conectado com sucesso a: {server}".format(server=server))

#     return conn


def get_company_reports_links(cod_cvm, driver, categoria="21"):
    """
    Returns dataframe of links and other data for the anual reports of a given list CVM codes
    """
    cod_cvm = str(cod_cvm)
    retriesCount = 0
    maxRetries = 2

    dataInicial = '01012010'
    dataFinal = datetime.today().strftime('%d%m%Y')

    # ChromeDriver
    if cod_cvm == "":

        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    else:
        url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx?codigoCVM="+cod_cvm

    driver.get(url)

    if cod_cvm == "":
        wait_pageload(driver, "BuscaInicial")

    #wait_pageload(driver, "BuscaInicial")

    table_html = str(driver.find_element_by_id(
        'grdDocumentos').get_attribute("outerHTML"))

    for errors in range(10):
        try:
            driver.find_element_by_id(
                'cboCategorias_chosen').click()
            break
        except:
            print("Tentando novamente")
            time.sleep(1)

    for errors in range(10):
        try:
            driver.find_element_by_xpath(
                "//html/body/form[1]/div[3]/div/fieldset/div[5]/div[1]/div/div/ul/li[@data-option-array-index='{option_text}']".format(option_text=categoria)).click()
            break
        except:
            print("Tentando novamente (Categoria)")
            time.sleep(1)

    driver.find_element_by_xpath("//html/body/form[1]/div[3]/div/fieldset/div[4]/div[1]/label[4]").click()
    driver.find_element_by_id('txtDataIni').send_keys(dataInicial)
    driver.find_element_by_id('txtDataFim').send_keys(dataFinal)
    driver.find_element_by_id('btnConsulta').click()
    
    wait_pageload(driver, "TabelaResultados")

    table_html = str(driver.find_element_by_id(
        'grdDocumentos').get_attribute("outerHTML"))
    table = LH.fromstring(table_html)
    df = pd.read_html(table_html)

    for df_result in df:
        print("Código CVM:", cod_cvm, "Quantidade de tabelas encontradas:", len(
            df), " Linhas:", len(df_result.index))
        if len(df_result.index) > 0:
            pattern = "OpenPopUpVer(\'(.*?)\')"
            df_result['linkView'] = table.xpath(
                '//tr/td/i[1]/@onclick')
            df_result['linkDownload'] = table.xpath(
                '//tr/td/i[2]/@onclick')

            df_result['linkView'] = "https://www.rad.cvm.gov.br/ENET/" + \
                df_result['linkView'].str.extract(
                    r"(?<=\')(.*?)(?=\')", expand=False)

            df3 = df_result['linkDownload'].str.split(
                ',', expand=True)
            df3.columns = ['COD{}'.format(
                x+1) for x in df3.columns]
            df_result = df_result.join(df3)
            df_result['linkDownload'] = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&numSequencia=" + \
                df_result['COD1'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                "&numVersao=" + df_result['COD2'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                "&numProtocolo=" + df_result['COD3'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                "&descTipo=" + df_result['COD4'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                "&CodigoInstituicao=1"

            df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
                            'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
                                'linkView', 'linkDownload']]

            df_result['Data Referência'] = df_result['Data Referência'].str.split(
                ' ', 1).str[1]

            df_result['Data Referência'] = pd.to_datetime(
                df_result["Data Referência"], format="%d/%m/%Y", errors="coerce")

            df_result = df_result[df_result["Status"] == "Ativo"]
            df_result["Código CVM"] = cod_cvm
            df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
                            'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
                                'linkView', 'linkDownload']]

        df_result = df_result.reset_index(drop=True)
        break
    # while retriesCount < maxRetries:
    #     try:
    #         # Parâmetros da consulta
    #         dataInicial = '01012010'
    #         dataFinal = datetime.today().strftime('%d%m%Y')

    #         # ChromeDriver
    #         if cod_cvm == "":

    #             url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
    #         else:
    #             url = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx?codigoCVM="+cod_cvm

    #         driver.get(url)

    #         if cod_cvm == "":
    #             wait_pageload(driver, "BuscaInicial")

    #         #wait_pageload(driver, "BuscaInicial")

    #         table_html = str(driver.find_element_by_id(
    #             'grdDocumentos').get_attribute("outerHTML"))

    #         for errors in range(10):
    #             try:
    #                 driver.find_element_by_id(
    #                     'cboCategorias_chosen').click()
    #                 break
    #             except:
    #                 print("Tentando novamente")
    #                 time.sleep(1)

    #         for errors in range(10):
    #             try:
    #                 driver.find_element_by_xpath(
    #                     "//html/body/form[1]/div[3]/div/fieldset/div[5]/div[1]/div/div/ul/li[@data-option-array-index='{option_text}']".format(option_text=categoria)).click()
    #                 break
    #             except:
    #                 print("Tentando novamente (Categoria)")
    #                 time.sleep(1)

    #         driver.find_element_by_xpath("//html/body/form[1]/div[3]/div/fieldset/div[4]/div[1]/label[4]").click()
    #         driver.find_element_by_id('txtDataIni').send_keys(dataInicial)
    #         driver.find_element_by_id('txtDataFim').send_keys(dataFinal)
    #         driver.find_element_by_id('btnConsulta').click()

    #         wait_pageload(driver, "TabelaResultados")

    #         table_html = str(driver.find_element_by_id(
    #             'grdDocumentos').get_attribute("outerHTML"))
    #         table = LH.fromstring(table_html)
    #         df = pd.read_html(table_html)

    #         for df_result in df:
    #             print("Código CVM:", cod_cvm, "Quantidade de tabelas encontradas:", len(
    #                 df), " Linhas:", len(df_result.index))
    #             if len(df_result.index) > 0:
    #                 pattern = "OpenPopUpVer(\'(.*?)\')"
    #                 df_result['linkView'] = table.xpath(
    #                     '//tr/td/i[1]/@onclick')
    #                 df_result['linkDownload'] = table.xpath(
    #                     '//tr/td/i[2]/@onclick')

    #                 df_result['linkView'] = "https://www.rad.cvm.gov.br/ENET/" + \
    #                     df_result['linkView'].str.extract(
    #                         r"(?<=\')(.*?)(?=\')", expand=False)

    #                 df3 = df_result['linkDownload'].str.split(
    #                     ',', expand=True)
    #                 df3.columns = ['COD{}'.format(
    #                     x+1) for x in df3.columns]
    #                 df_result = df_result.join(df3)
    #                 df_result['linkDownload'] = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&numSequencia=" + \
    #                     df_result['COD1'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
    #                     "&numVersao=" + df_result['COD2'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
    #                     "&numProtocolo=" + df_result['COD3'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
    #                     "&descTipo=" + df_result['COD4'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
    #                     "&CodigoInstituicao=1"

    #                 df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
    #                                 'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
    #                                  'linkView', 'linkDownload']]

    #                 df_result['Data Referência'] = df_result['Data Referência'].str.split(
    #                     ' ', 1).str[1]

    #                 df_result['Data Referência'] = pd.to_datetime(
    #                     df_result["Data Referência"], format="%d/%m/%Y", errors="coerce")

    #                 df_result = df_result[df_result["Status"] == "Ativo"]
    #                 df_result["Código CVM"] = cod_cvm
    #                 df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
    #                                 'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
    #                                  'linkView', 'linkDownload']]

    #             df_result = df_result.reset_index(drop=True)
    #             break
    #         break
    #     except Exception as exp:
    #         print("Erro ao importar", str(exp))
    #         retriesCount += 1

    return df_result


def obtemDadosCadastraisCVM(compAtivas=True, codCVM=False):
    """
    Returns a dataframe of Registration data for all Companies available at http://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv
    """
    url = "http://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    #s = requests.get(url).content
    dados_cadastrais_empresas = pd.read_csv(url, sep=";", encoding="latin")

    if compAtivas:
        dados_cadastrais_empresas = dados_cadastrais_empresas[
            dados_cadastrais_empresas["SIT"] == "ATIVO"]

    if codCVM:
        dados_cadastrais_empresas = dados_cadastrais_empresas[dados_cadastrais_empresas["CD_CVM"] == int(
            codCVM)]

    return dados_cadastrais_empresas


def composicao_capital_social(codCVM):
    """
    This metodh will be deprecated
    """

    dfQuantPapeis = pd.DataFrame()
    for cod in codCVM:
        erro = 1
        cod = str(cod)
        while erro <= 3:
            try:
                print(cod)
                url = "http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM={codCVM}".format(
                    codCVM=cod)

                #
                html_content = requests.get(url).content.decode("utf8")

                tableDados = BeautifulSoup(html_content, "lxml").find(
                    "div", attrs={"id": "accordionDados"})
                tickers = re.findall(
                    "'[a-z|A-Z|0-9][a-z|A-Z|0-9][a-z|A-Z|0-9][a-z|A-Z|0-9][0-9][0-9]?'", str(tableDados))
                tickers = [ticker.replace("'", "") for ticker in tickers]
                tickers = list(dict.fromkeys(tickers))

                tickers = pd.DataFrame(tickers, columns=['ticker'])
                tickers["codCVM"] = cod

                dicCapitalSocial = BeautifulSoup(html_content, "lxml").find(
                    "div", attrs={"id": "divComposicaoCapitalSocial"})

                dfs = pd.read_html(str(dicCapitalSocial), thousands='.')[0]

                dfs.columns = ["Tipo", "Quantidade"]

                dfs["codCVM"] = cod
                dfs["dt_load"] = datetime.now()

                dfs = tickers.merge(dfs, on="codCVM")
                print(dfs)
                dfQuantPapeis = dfQuantPapeis.append(dfs)
                break
            except Exception as exp:
                print("Tentando novamente:", cod)
                print(str(exp))
                erro += 1
        print("*"*50)

    return dfQuantPapeis


def obter_dados_negociacao(dateToday=datetime.now().strftime("%Y-%m-%d")):

    print(dateToday)
    url = f"https://arquivos.b3.com.br/api/download/requestname?fileName=InstrumentsConsolidated&date={dateToday}"

    payload = {}
    ua = UserAgent()

    headers = {
        'User-Agent': str(ua.chrome)}

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.ok:
        token = response.json().get('token')
        baseURL = f"https://arquivos.b3.com.br/api/download/?token={token}"
        data = pd.read_csv(baseURL,
                           sep=";",
                           encoding='latin-1',
                           error_bad_lines=True)
        data["data_load"] = datetime.now()

        print("Baixando arquivo!")
        r = urllib.request.urlopen(
            "https://sistemaswebb3-listados.b3.com.br/isinProxy/IsinCall/GetFileDownload/NDY0ODk=").read()

        print("Descompactando arquivo!")
        file = ZipFile(BytesIO(r))
        dfEmissor = file.open("EMISSOR.TXT")

        print("Abrindo arquivo CSV!")
        dfEmissor = pd.read_csv(dfEmissor, header=None, names=[
                                "CODIGO DO EMISSOR", "NOME DO EMISSOR", "CNPJ", "DATA CRIAÇÃO EMISSOR"])

        data = data.merge(dfEmissor, left_on="AsstDesc",
                          right_on="CODIGO DO EMISSOR", how="left")

        data.reset_index(drop=True, inplace=True)

    else:
        data = None

    return data


def obtemCodCVM():

    url = "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome=&TipoConsult=C"
    print(url)
    tableDados = pd.read_html(url, header=0)[0]
    tableDados = tableDados[~tableDados['SITUAÇÃO REGISTRO'].str.contains(
        "Cancelado")]
    tableDados["CÓDIGO CVM"] = pd.to_numeric(
        tableDados["CÓDIGO CVM"], errors="coerce")
    tableDados = tableDados.drop_duplicates()
    tableDados = tableDados.reset_index(drop=True)

    return tableDados


def download_wait(path_to_downloads):
    """
    Waits all Chrome download files (.crdownload) in a folder be done before continues
    """
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < 20:
        time.sleep(1)
        dl_wait = False
        for fname in os.listdir(path_to_downloads):
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1
    return seconds


# Obtem indices IMA da ambima em um intervalo definido
def obter_indices_anbima(dataIni, dataFim):
    link = "https://www.anbima.com.br/informacoes/ima/ima-sh.asp"
    driver = iniciarChromeDriver(system="Windows")
    #dataIni = datetime.now().strftime("%d%m%Y")
    dataIni = datetime.strptime(dataIni, '%d/%m/%Y')
    dataFim = datetime.strptime(dataFim, '%d/%m/%Y')
    root = os.getcwd() + "/downloads"
    try:
        os.makedirs(root)
    except FileExistsError:
        # directory already exists
        pass

    # Remover arquivos da pasta de destino do download antes de iniciar novo scrapping
    files = glob.glob(root)
    f = []
    for (dirpath, dirnames, filenames) in os.walk(root):
        for file in filenames:
            if file.endswith(".csv"):
                os.remove(root + "/" + file)

    while dataFim >= dataIni:
        try:
            dateAux = dataFim.strftime("%d%m%Y")
            driver.get(link)
            driver.find_element_by_xpath(
                "//input[@name='escolha'][@value='2']").click()
            driver.find_element_by_xpath(
                "//input[@name='saida'][@value='csv']").click()
            dateInput = driver.find_element_by_xpath("//input[@name='Dt_Ref']")
            dateInput.click()
            dateInput.clear()
            dateInput.send_keys(dateAux)
            driver.find_element_by_xpath("//img[@name='Consultar']").click()
            dataFim -= timedelta(days=1)
        except Exception as excep:
            print(str(excep))

    f = []
    dfAmbima = pd.DataFrame()
    for (dirpath, dirnames, filenames) in os.walk(root):
        for file in filenames:
            try:
                df = pd.read_csv(root + "/" + file, header=1,
                                 sep=";", encoding="latin", thousands=".")
                os.remove(root + "/" + file)
                dfAmbima = dfAmbima.append(df)
            except:
                continue

    # Tipos de dados
    dfAmbima = dfAmbima.replace("--", "")
    dfAmbima["Data de Referência"] = pd.to_datetime(
        dfAmbima["Data de Referência"], format='%d/%m/%Y', errors='coerce')
    for column in dfAmbima.columns:
        if column != "Data de Referência" and column != "Índice":
            print(column)
            dfAmbima[column] = dfAmbima[column].astype(
                str).str.replace('.', '')
            dfAmbima[column] = dfAmbima[column].astype(
                str).str.replace(',', '.')
            dfAmbima[column] = pd.to_numeric(dfAmbima[column])
    driver.quit()

    return dfAmbima.reset_index(drop=True)


def obter_cotacao_moeda(startDate, endDate, codMoeda="61"):
    urlDolar = f'https://ptax.bcb.gov.br/ptax_internet/consultaBoletim.do?method=gerarCSVFechamentoMoedaNoPeriodo&ChkMoeda={codMoeda}&DATAINI={startDate}&DATAFIM={endDate}'
    columnNames = ["Date", "Tipo", "Moeda", "Compra", "Venda"]
    dfMoeda = pd.read_csv(urlDolar,
                          sep=";",
                          encoding="latin",
                          decimal=",",
                          index_col=0,
                          names=columnNames,
                          usecols=[0, 2, 3, 4, 5]
                          )

    dfMoeda.index = pd.to_datetime(
        [str(x).zfill(8) for x in dfMoeda.index], format="%d%m%Y", errors='coerce')

    dfMoeda["Compra"] = pd.to_numeric(
        dfMoeda["Compra"].astype(str).str.replace(',', '.'))
    dfMoeda["Venda"] = pd.to_numeric(
        dfMoeda["Venda"].astype(str).str.replace(',', '.'))

    return dfMoeda.sort_index()


def get_closer_quarter_date(date: datetime) -> datetime:
    from datetime import datetime
    import math
    from dateutil.relativedelta import relativedelta # requires python-dateutil

    start_of_quarter = datetime(year=datetime.now().year, month=((math.floor(((datetime.now().month - 1) / 3) + 1) - 1) * 3) + 1, day=1)

    end_of_quarter = start_of_quarter + relativedelta(months=3, seconds=-1)

    return end_of_quarter

@dataclass
class SearchENET:
    """
    Perform webscraping on the page https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx according to the input parameters
    """

    def __init__(self, cod_cvm: int, category: int, driver: webdriver = None):
        self.driver = driver
        
        # self.cod_cvm_dataframe = self.cod_cvm_list()
        
        self.cod_cvm = cod_cvm
        self.check_cod_cvm_exist(self.cod_cvm)
        
        self.category = category
        self.check_category_exist(self.category)


    def cod_cvm_list(self) -> pd.DataFrame:
        """
        Returns a dataframe of all CVM codes and Company names availble at https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx
        """
        if self.driver is None:
            driver = iniciarChromeDriver()
        else:
            driver=self.driver
        driver.get(f"https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx")

        #wait_pageload()
        for retrie in range(50):
            try:
                html = str(driver.find_element_by_id('hdnEmpresas').get_attribute("value"))
                listCodCVM = re.findall("(?<=\_)(.*?)(?=\')", html)
                listNomeEmp = re.findall("(?<=\-)(.*?)(?=\')", html)
                codigos_cvm = pd.DataFrame(list(zip(listCodCVM, listNomeEmp)),
                                columns=['codCVM', 'nome_empresa'])
                codigos_cvm['codCVM'] = pd.to_numeric(codigos_cvm['codCVM'])
                if len(codigos_cvm.index) > 0:
                    break
                else:
                    time.sleep(1)
            except:
                time.sleep(1)

        if self.driver is None:
            driver.quit()

        return codigos_cvm
    

    def check_cod_cvm_exist(self, cod_cvm) -> bool:
        codigos_cvm_available = self.cod_cvm_list()
        print(codigos_cvm_available['codCVM'].values)
        cod_cvm_exists = str(cod_cvm) in [str(cod_cvm_aux) for cod_cvm_aux in codigos_cvm_available['codCVM'].values]
        if cod_cvm_exists:
            return True
        else:
            raise ValueError('Código CVM informado não encontrado.')
            

    def check_category_exist(self, category) -> bool:
        search_categories_list = [21, 39]
        if category in search_categories_list:
            return True
        else:
            raise ValueError('Invalid category value. Available categories are:', search_categories_list)


    @property
    def search(self) -> pd.DataFrame:
        """
        Returns dataframe of search results including cod_cvm, report's url, etc.
        """

        dataInicial = '01012010'
        dataFinal = datetime.today().strftime('%d%m%Y')
        option_text = str(self.category)
        
        if self.driver is None:
            driver = iniciarChromeDriver()
        else:
            driver=self.driver
        
        driver.get(f"https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx?codigoCVM={str(self.cod_cvm)}")

        # Wait and click cboCategorias_chosen
        for errors in range(10):
            try:
                driver.find_element_by_id('cboCategorias_chosen').click()
                break
            except:
                time.sleep(1)

        # Wait and click
        for errors in range(10):
            try:
                driver.find_element_by_xpath(
                    f"//html/body/form[1]/div[3]/div/fieldset/div[5]/div[1]/div/div/ul/li[@data-option-array-index='{option_text}']").click()
                break
            except:
                time.sleep(1)

        # Wait and click
        for errors in range(10):
            try:
                driver.find_element_by_xpath("//html/body/form[1]/div[3]/div/fieldset/div[4]/div[1]/label[4]").click()
                break
            except:
                time.sleep(1)
        
        # Wait and send keys txtDataIni
        for errors in range(10):
            try:
                driver.find_element_by_id('txtDataIni').send_keys(dataInicial)
                break
            except:
                time.sleep(1)

        # Wait and send keys txtDataFim
        for errors in range(10):
            try:
                driver.find_element_by_id('txtDataFim').send_keys(dataFinal)
                break
            except:
                time.sleep(1)
        
        # Wait and click btnConsulta
        for errors in range(10):
            try:
                driver.find_element_by_id('btnConsulta').click()
                break
            except:
                time.sleep(1)

        # Wait html table load the results (grdDocumentos)
        for errors in range(10):
            try:
                table_html = pd.read_html(str(driver.find_element_by_id('grdDocumentos').get_attribute("outerHTML")))[-1]
                if len(table_html.index) > 0:
                    break
                else:
                    time.sleep(1)
            except:
                time.sleep(1)

        table_html = str(driver.find_element_by_id('grdDocumentos').get_attribute("outerHTML"))
        table = LH.fromstring(table_html)
        results = pd.read_html(table_html)

        for df_result in results:
            if len(df_result.index) > 0:
                pattern = "OpenPopUpVer(\'(.*?)\')"
                df_result['linkView'] = table.xpath('//tr/td/i[1]/@onclick')
                df_result['linkDownload'] = table.xpath('//tr/td/i[2]/@onclick')

                df_result['linkView'] = "https://www.rad.cvm.gov.br/ENET/" + \
                    df_result['linkView'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False)

                df3 = df_result['linkDownload'].str.split(',', expand=True)
                df3.columns = ['COD{}'.format(x+1) for x in df3.columns]
                df_result = df_result.join(df3)
                df_result['linkDownload'] = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&numSequencia=" + \
                    df_result['COD1'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                    "&numVersao=" + df_result['COD2'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                    "&numProtocolo=" + df_result['COD3'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                    "&descTipo=" + df_result['COD4'].str.extract(r"(?<=\')(.*?)(?=\')", expand=False) + \
                    "&CodigoInstituicao=1"

                df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
                                'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
                                    'linkView', 'linkDownload']]

                df_result['Data Referência'] = df_result['Data Referência'].str.split(
                    ' ', 1).str[1]

                df_result['Data Referência'] = pd.to_datetime(
                    df_result["Data Referência"], format="%d/%m/%Y", errors="coerce")

                df_result = df_result[df_result["Status"] == "Ativo"]
                df_result["Código CVM"] = self.cod_cvm
                df_result = df_result[['Código CVM', 'Empresa', 'Categoria', 'Tipo', 'Espécie',
                                'Data Referência', 'Data Entrega', 'Status', 'V', 'Modalidade',
                                    'linkView', 'linkDownload']]

            df_result = df_result.reset_index(drop=True)
            break

        if self.driver is None:
            driver.quit()

        print(f"Resultados da busca ENET: {len(df_result.index)}")
        return df_result


@dataclass
class FinancialReport:
    def __init__(self, link: str, driver: webdriver = None):
        self.link = link
        self.driver = driver


    @property
    def financial_reports(self) -> Dict:
        """
        Returns a dictionary with financial reports available in a page such as 
        Reports currently available:
        - 
        """
        link = self.link

        if self.driver is None:
            driver = iniciarChromeDriver()
        else:
            driver=self.driver

        erros = 0
        max_retries = 10
        
        dictDemonstrativos = None

        while erros < max_retries:
            try:
                print("Coletando dados do link:", link)
                driver.get(link)

                # Wait page load the reports
                for retrie in range(max_retries):
                    # Quando o captcha é que quebrado, options_text trás as opções de demonstrativos
                    options_text = [x.get_attribute("text") for x in driver.find_element_by_name(
                        "cmbQuadro").find_elements_by_tag_name("option")]

                    if len(options_text) > 0:
                        break
                    else:
                        time.sleep(1)

                # Navega nos demonstrativos e salva o dataframe no dicionario
                refDate = driver.find_element_by_id('lblDataDocumento').text
                versaoDoc = driver.find_element_by_id(
                    'lblDescricaoCategoria').text.split(" - ")[-1].replace("V", "")
                
                report = {"ref_date": refDate,
                          "versao": int(versaoDoc),
                          "cod_cvm": int(driver.find_element_by_id('hdnCodigoCvm').get_attribute("value"))
                          }

                dictDemonstrativos = {}
                for demonstrativo in options_text:
                    print(demonstrativo)

                    driver.find_element_by_xpath("//select[@name='cmbQuadro']/option[text()='{option_text}']".format(option_text=demonstrativo)).click()

                    iframe = driver.find_element_by_xpath(
                        "//iframe[@id='iFrameFormulariosFilho']")
                    driver.switch_to.frame(iframe)
                    html = driver.page_source

                    if demonstrativo == "Demonstração do Fluxo de Caixa":
                        index_moeda = -2
                    else:
                        index_moeda = -1

                    moedaUnidade = driver.find_element_by_id(
                        'TituloTabelaSemBorda').text.split(" - ")[index_moeda].replace("(", "").replace(")", "")

                    if demonstrativo == "Demonstração das Mutações do Patrimônio Líquido":
                        df = pd.read_html(html, header=0, decimal=',')[1]
                        converters = {c: lambda x: str(x) for c in df.columns}
                        df = pd.read_html(html, header=0, decimal=',',
                                        converters=converters)[1]

                    else:
                        df = pd.read_html(html, header=0, decimal=',')[0]
                        converters = {c: lambda x: str(x) for c in df.columns}
                        df = pd.read_html(html, header=0, decimal=',',
                                        converters=converters)[0]

                    for ind, column in enumerate(df.columns):
                        if column.strip() != "Conta" and column.strip() != "Descrição":
                            df[column] = df[column].astype(
                                str).str.strip().str.replace(".", "")
                            df[column] = pd.to_numeric(df[column], errors='coerce')
                        else:
                            df[column] = df[column].astype(
                                'str').str.strip().astype('str')

                    # Pega apenas a primeira coluna de valores, correspondente ao demonstrativo mais atual, e renomeia para "Valor"
                    if demonstrativo != "Demonstração das Mutações do Patrimônio Líquido":
                        df = df.iloc[:, 0:3]
                        df.set_axis([*df.columns[:-1], 'Valor'],
                                    axis=1, inplace=True)

                    # Add data de referencia e versão aos Dataframes
                    df["refDate"] = refDate
                    df["versaoDoc"] = versaoDoc
                    df["moedaUnidade"] = moedaUnidade

                    df["refDate"] = pd.to_datetime(df["refDate"], errors="coerce")

                    # Add ao dicionario de demonstrativos
                    dictDemonstrativos[demonstrativo] = df

                    driver.switch_to.default_content()

                print("-"*60)

                # Add data de referencia ao ditc de demonstrativos
                report["reports"] = dictDemonstrativos
                break
            except Exception as exp:
                print("Erro ao carregar demonstrativo. Tentando novamente...")
                print(str(exp))
                erros += 1
                continue
        
        if self.driver is None:
            driver.quit()

        return report


@dataclass
class Company:
    def __init__(self, cod_cvm: int):
        self.cod_cvm = cod_cvm
        self.reports = self.get_reports()


    def obtemCompCapitalSocial(self):
        self.ComposicaoCapitalSocial = composicao_capital_social(self._codCVM)


    def obterDadosCadastrais(self):
        listaCodCVM = obtemDadosCadastraisCVM(self._codCVM)
        listaCodCVM = listaCodCVM[listaCodCVM["CD_CVM"] == self._codCVM]
        self.dadosCadastrais = listaCodCVM.to_dict('r')


    def get_reports(self) -> Dict:
        driver = iniciarChromeDriver()
        search_anual_reports = SearchENET(cod_cvm=21610, category=21, driver=driver).search
        search_quarter_reports = SearchENET(cod_cvm=21610, category=39, driver=driver).search
        search_reports_result = search_anual_reports.append(search_quarter_reports)

        reports = []
        for index, report_info in search_reports_result.iterrows():
            reports.append(FinancialReport(link=report_info["linkView"], driver=driver).financial_reports)
        
        driver.quit()

        return reports