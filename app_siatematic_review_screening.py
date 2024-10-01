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

# Função para criar relatório em Excel com contagem de termos em uma única aba
def create_excel_report(results, search_terms):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Preparar lista para os dados do relatório
    rows = []
    
    # Preencher os dados com a contagem total de cada termo por arquivo
    for result in results:
        row = {'Arquivo': result['Arquivo']}
        # Adiciona a contagem de cada termo
        for term in search_terms:
            row[term] = result['Contagem de Termos'].get(term, 0)  # Obtém a contagem do termo ou 0 se não estiver presente
        rows.append(row)
    
    # Criar um DataFrame com todas as contagens de termos
    df_totals = pd.DataFrame(rows)
    
    # Escrever o DataFrame na primeira aba
    df_totals.to_excel(writer, sheet_name='Contagem de Termos', index=False)
    
    writer.close()
    output.seek(0)
    return output



# Dicionários de tradução para múltiplos idiomas
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
        'change_language': "Change language to:",
        'conditions': ["and", "or", "not"]
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
        'change_language': "Mudar idioma para:",
        'conditions': ["e", "ou", "não"]
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
        'change_language': "Cambiar idioma a:",
        'conditions': ["y", "o", "no"]
    }
}

# Função para mapear as condições entre inglês e o idioma atual
def map_condition_to_english(condition, language):
    condition_map = {
        'English': {"and": "and", "or": "or", "not": "not"},
        'Português (Brasil)': {"e": "and", "ou": "or", "não": "not"},
        'Español (España)': {"y": "and", "o": "or", "no": "not"}
    }
    return condition_map[language].get(condition, condition)

def map_condition_from_english(condition, language):
    condition_map = {
        'English': {"and": "and", "or": "or", "not": "not"},
        'Português (Brasil)': {"and": "e", "or": "ou", "not": "não"},
        'Español (España)': {"and": "y", "or": "o", "not": "no"}
    }
    return condition_map[language].get(condition, condition)

# Interface para seleção de idioma
if 'language' not in st.session_state:
    st.session_state.language = 'English'

# Exibir a linguagem atual e opções para mudança
current_language = st.session_state.language
t = lambda key: translations[current_language][key]

st.write(f"### {t('current_language')}")
if st.button("Português (Brasil)"):
    st.session_state.language = 'Português (Brasil)'
if st.button("Español (España)"):
    st.session_state.language = 'Español (España)'
if st.button("English"):
    st.session_state.language = 'English'

# Configurações principais da interface
st.title(t('title'))

# Upload de arquivos PDF
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
    cols = st.columns([4, 1])  # Dividimos a linha em duas colunas para termo e botão de remoção
    st.session_state.search_terms[i] = cols[0].text_input(f"{t('search_term')} {i+1}", value=st.session_state.search_terms[i], key=f"search_term_{i}")
    
    # Exibe o botão de remover ao lado do campo de busca
    if i > 0:  # Não mostramos o botão de remover para o primeiro campo
        condition = st.session_state.conditions[i-1]
        # Converter a condição do inglês para o idioma atual
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
if len(uploaded_files) > 100:  # Limite aumentado para 100 PDFs
    st.error(t('file_error'))
else:
    if st.button(t('search_button')):
        if uploaded_files and any(st.session_state.search_terms):
            # Realizando a triagem
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

                # Criar e oferecer o download do relatório em Excel
                excel_file = create_excel_report(results, st.session_state.search_terms)  # Corrigido aqui
                st.download_button(
                    label=t('download_excel'),
                    data=excel_file,
                    file_name="relatorio_triangem.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write(t('no_results'))
        else:
            st.error(t('file_error'))
