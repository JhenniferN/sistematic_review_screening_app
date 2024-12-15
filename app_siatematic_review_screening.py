import streamlit as st
import PyPDF2
import os
import io
import zipfile
import pandas as pd

# Função para extrair texto do PDF usando PdfReader
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

# Função para buscar termos no texto
def search_term_in_text(text, search_terms, conditions):
    sentences = text.split('.')
    found_sentences = []
    term_count = {term: 0 for term in search_terms}
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        include_sentence = True

        for i, term in enumerate(search_terms):
            term_found = term.lower() in sentence_lower
            if i == 0:
                include_sentence = term_found
            else:
                condition = conditions[i-1]
                if condition == "and":
                    include_sentence = include_sentence and term_found
                elif condition == "or":
                    include_sentence = include_sentence or term_found
                elif condition == "not":
                    include_sentence = include_sentence and not term_found

        if include_sentence:
            found_sentences.append(sentence.strip())
            # Incrementa a contagem de termos baseados na presença deles em cada sentença
            for term in search_terms:
                term_count[term] += sentence_lower.count(term.lower())

    return bool(found_sentences), found_sentences, term_count

# Função para realizar a triagem
def triagem_pdfs(files, search_terms, conditions):
    results = []
    for file in files:
        text = extract_text_from_pdf(file)
        term_found, found_sentences, term_count = search_term_in_text(text, search_terms, conditions)
        if term_found:
            results.append({
                'Arquivo': file.name,
                'PDF': file,
                'Frases Encontradas': found_sentences,
                'Contagem de Termos': term_count
            })
    return results

# Função para criar um arquivo ZIP com os PDFs relevantes
def create_zip(results):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for result in results:
            pdf_data = result['PDF'].getvalue()
            zip_file.writestr(result['Arquivo'], pdf_data)
    
    zip_buffer.seek(0)
    return zip_buffer




# Configura o estado para controlar a exibição das informações e o idioma
if 'show_info' not in st.session_state:
    st.session_state.show_info = False
if 'language' not in st.session_state:
    st.session_state.language = 'English'

# Dicionário de traduções
translations = {
    'English': {
        'title': "Scientific Articles Screening",
        'upload_files': "Choose PDF files",
        'search_term': "Enter search term",
        'add_term': "+ Add search field",
        'remove_term': "Remove",
        'search_condition': "Choose the condition between terms",
        'search_button': "Search",
        'download_zip': "Download all relevant PDFs in a ZIP",
        'download_excel': "Download Excel report",
        'no_results': "No files contain the terms",
        'file_error': "Please upload PDF files and enter at least one search term.",
        'current_language': "The current language is: English",
        'info_button': "Information about the app's functionality",
        'info_text': """
        According to the PRISMA guidelines (Preferred Reporting Items for Systematic Reviews and Meta-Analyses), screening begins after the initial search for studies across multiple databases. At this stage, duplicate studies are removed, and other scientific works are excluded based on title and abstract analysis. Studies that remain after this initial filtering are fully assessed and proceed through the eligibility and inclusion phases, where relevant information is collected for final analysis.

        Our screening method involves removing duplicates, downloading the remaining articles, and excluding articles that do not contain specific keywords, which are searched directly in the PDF texts. The remaining papers proceed directly to the eligibility and inclusion phases.

        This application was developed to assist researchers in conducting the screening process for their systematic review. Perform the search for studies of interest in your preferred databases, use Zotero to batch download the identified studies. Finally, simply upload the downloaded PDFs to our app, enter the keywords of interest in the search fields, and your studies will be automatically screened, saving you time and effort.
        """
    },
    'Português (Brasil)': {
        'title': "Triagem de Artigos Científicos",
        'upload_files': "Escolha os arquivos PDF",
        'search_term': "Digite o termo de busca",
        'add_term': "+ Adicionar campo de busca",
        'remove_term': "Remover",
        'search_condition': "Escolha a condição entre os termos",
        'search_button': "Buscar",
        'download_zip': "Baixar todos os PDFs relevantes em um ZIP",
        'download_excel': "Baixar relatório em Excel",
        'no_results': "Nenhum arquivo contém os termos",
        'file_error': "Por favor, faça upload de arquivos PDF e insira ao menos um termo de busca.",
        'current_language': "O idioma atual é: Português (Brasil)",
        'info_button': "Informações sobre o funcionamento do app",
        'info_text': """
        De acordo com as diretrizes dos Itens de Relatório Preferidos para Revisões Sistemáticas e Meta-Análises (PRISMA), a triagem inicia-se após a busca inicial de estudos em diferentes bases de dados. Nesta etapa, os estudos duplicados são eliminados, e os demais trabalhos científicos são excluídos com base na análise dos títulos e resumos. Os estudos que permanecem após essa filtragem inicial são avaliados integralmente e passam pelas fases de elegibilidade e inclusão, onde são coletadas as informações relevantes para a análise final.

        Nosso método de triagem consiste na remoção de duplicatas, no download dos artigos restantes e na exclusão de artigos que não contêm termos-chave específicos, os quais são buscados diretamente no PDF dos textos. Os trabalhos que restam seguem diretamente para as fases de elegibilidade e inclusão.

        Este aplicativo foi desenvolvido para que pesquisadores realizem o processo de triagem de sua revisão sistemática. Faça a busca dos trabalhos de seu interesse nas bases de dados de sua preferência, utilize o Zotero para fazer o download em massa dos trabalhos identificados. Por fim, basta fazer o upload dos PDFs baixados em nosso app, inserir as palavras-chave de interesse nos campos de busca, e seus trabalhos serão automaticamente triados, economizando seu tempo e esforço.
        """
    },
    'Español (España)': {
        'title': "Cribado de Artículos Científicos",
        'upload_files': "Seleccione los archivos PDF",
        'search_term': "Introduzca el término de búsqueda",
        'add_term': "+ Agregar campo de búsqueda",
        'remove_term': "Eliminar",
        'search_condition': "Elija la condición entre los términos",
        'search_button': "Buscar",
        'download_zip': "Descargar todos los PDF relevantes en un ZIP",
        'download_excel': "Descargar informe en Excel",
        'no_results': "Ningún archivo contiene los términos",
        'file_error': "Por favor, suba archivos PDF e ingrese al menos un término de búsqueda.",
        'current_language': "El idioma actual es: Español (España)",
        'info_button': "Información sobre el funcionamiento de la aplicación",
        'info_text': """
        Según las directrices de PRISMA (Elementos de Informe Preferidos para Revisiones Sistemáticas y Meta-Análisis), el cribado comienza tras la búsqueda inicial de estudios en múltiples bases de datos. En esta etapa, se eliminan los estudios duplicados y otros trabajos científicos se excluyen en función del análisis de títulos y resúmenes. Los estudios que permanecen después de esta filtración inicial se evalúan por completo y pasan por las fases de elegibilidad e inclusión, donde se recopila la información relevante para el análisis final.

        Nuestro método de cribado consiste en eliminar duplicados, descargar los artículos restantes y excluir los artículos que no contienen palabras clave específicas, que se buscan directamente en los textos PDF. Los trabajos restantes pasan directamente a las fases de elegibilidad e inclusión.

        Esta aplicación fue desarrollada para ayudar a los investigadores a realizar el proceso de cribado para su revisión sistemática. Realice la búsqueda de estudios de interés en las bases de datos de su preferencia, utilice Zotero para descargar en lote los estudios identificados. Finalmente, simplemente cargue los PDFs descargados en nuestra aplicación, ingrese las palabras clave de interés en los campos de búsqueda, y sus estudios serán cribados automáticamente, ahorrándole tiempo y esfuerzo.
        """
    }
}

# Função de tradução
current_language = st.session_state.language
t = lambda key: translations[current_language][key]

# Interface para seleção de idioma
st.write(f"### {t('current_language')}")
if st.button("Português (Brasil)", key="pt_button"):
    st.session_state.language = 'Português (Brasil)'
if st.button("Español (España)", key="es_button"):
    st.session_state.language = 'Español (España)'
if st.button("English", key="en_button"):
    st.session_state.language = 'English'

# Título principal da interface
st.title(t('title'))

# Botão para exibir as informações de funcionamento no idioma selecionado
if st.button(t('info_button'), key="info_button"):
    st.session_state.show_info = not st.session_state.show_info

# Exibe o texto informativo no idioma atual
if st.session_state.show_info:
    st.write(t('info_text'))

# Seção de upload de arquivos PDF
uploaded_files = st.file_uploader(t('upload_files'), accept_multiple_files=True, type="pdf")

# Inicializar sessão para os termos de busca e condições
if 'search_terms' not in st.session_state:
    st.session_state.search_terms = ['']
if 'conditions' not in st.session_state:
    st.session_state.conditions = []

# Função para adicionar campos de busca
def add_term():
    st.session_state.search_terms.append('')
    st.session_state.conditions.append('and')  # Define uma condição padrão entre os termos

# Função para remover campos de busca
def remove_term(index):
    st.session_state.search_terms.pop(index)
    if index > 0:  # Remover também a condição anterior, já que ela fica entre os termos
        st.session_state.conditions.pop(index - 1)

# Exibir campos de busca
for i in range(len(st.session_state.search_terms)):
    cols = st.columns([4, 1])
    st.session_state.search_terms[i] = cols[0].text_input(f"{t('search_term')} {i+1}", value=st.session_state.search_terms[i], key=f"search_term_{i}")
    
    # Exibe o botão de remover ao lado do campo de busca
    if i > 0:
        condition = st.session_state.conditions[i-1]
        translated_condition = map_condition_from_english(condition, current_language)
        
        st.session_state.conditions[i-1] = map_condition_to_english(
            st.selectbox(t('search_condition'), t('conditions'), index=t('conditions').index(translated_condition), key=f"condition_{i-1}"),
            current_language
        )
        if cols[1].button(t('remove_term'), key=f"remove_term_{i}"):
            remove_term(i)

# Botão para adicionar mais termos
if st.button(t('add_term')):
    add_term()

# Limitar o número de arquivos PDF a serem carregados
if len(uploaded_files) > 100:
    st.error(t('file_error'))
else:
    if st.button(t('search_button')):
        if uploaded_files and any(st.session_state.search_terms):
            results = triagem_pdfs(uploaded_files, st.session_state.search_terms, st.session_state.conditions)
            
            if len(results) > 0:
                st.write(f"Foram encontrados {len(results)} arquivos com os termos '{', '.join(st.session_state.search_terms)}'.")
                
                # Exibir a lista dos arquivos relevantes
                for result in results:
                    st.write(f"- {result['Arquivo']}")
                
                # Criar o arquivo ZIP se houver resultados
                zip_file = create_zip(results)
                
                # Botão para download do arquivo ZIP
                st.download_button(
                    label=t('download_zip'),
                    data=zip_file,
                    file_name="pdfs_relevantes.zip",
                    mime="application/zip"
                )

            else:
                st.write(t('no_results'))
        else:
            st.error(t('file_error'))



