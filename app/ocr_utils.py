import pytesseract
from PIL import Image
import re
import os
import cv2
import traceback
from datetime import datetime, date

print("====== MODULO OCR_UTILS.PY (v19 - Foco Total no CPF da CNH) CARREGADO ======")

# --- Mantenha suas listas PALAVRAS_CHAVE_IGNORAR_PARA_NOME e ROTULOS_FORTES ---
PALAVRAS_CHAVE_IGNORAR_PARA_NOME = [
    "CPF", "NASCIMENTO", "DATA", "NATURALIDADE",
    "ASSINATURA", "POLEGAR", "IDENTIDADE", "SECRETARIA", "SEGURANÇA", "SEGURANCA",
    "PÚBLICA", "PUBLICA", "REPUBLICA", "FEDERATIVA", "BRASIL", "MINISTERIO", "JUSTICA", "INFRAESTRUTURA",
    "DEPARTAMENTO", "POLICIA", "REGISTRO", "GERAL", "VALIDADE", "EMISSOR",
    "DOC", "SSP", "SESP", "DETRAN", "UF", "HABILITACAO", "ACC", "CAT", "PERMISSÃO", "PERMISSAO",
    "CNH", "RENACH", "EMISSÃO", "EMISSAO", "NACIONAL", "TRANSITO", "CONSELHO", "SUS", "CARTAO",
    "BENEFICIARIO", "USUARIO", "PORTADOR", "TITULAR", "OBSERVAÇÕES", "LOCAL", "TERRITORIO", "FILHO", "FILHA",
    "SEXO", "EXPIRY"
]
ROTULOS_FORTES = [
    "NOME", "NAME", "NOME SOCIAL", "NOME DO BENEFICIARIO",
    "CPF", "REGISTRO GERAL", "DOC. IDENTIDADE", "DOC IDENTIDADE", "IDENTIDADE/ORG", "DOC.IDENTIDADE/ORG.EMISSOR/UF",
    "FILIAÇÃO", "FILIACAO", "NOME DO PAI", "NOME DA MÃE",
    "DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH", "NASC.",
    "NÚMERO DO CARTÃO", "NUMERO DO CARTAO", "Nº REGISTRO",
    "VALIDADE", "EXPIRY", "DATA DE EMISSÃO", "DATA DE EMISSAO"
]

# --- preprocess_image_for_ocr e extract_text_from_image (da v18) ---
# Mantenha o Limiar de Otsu como padrão, pois funcionou bem para a CNH.
def preprocess_image_for_ocr(image_path, output_folder="app/static/uploads"):
    print(f"====== V19: ENTROU EM PREPROCESS_IMAGE_FOR_OCR ======")
    # ... (código da v18, com prints V19_PREPROCESS_...)
    print(f"V19_PREPROCESS: Recebido image_path: {image_path}")
    try:
        original_basename = os.path.basename(image_path)
        os.makedirs(output_folder, exist_ok=True)
        name_part, ext = os.path.splitext(original_basename)
        safe_name_part = re.sub(r'[^\w\.-]', '_', name_part)

        img = cv2.imread(image_path)
        if img is None:
            print(f"V19_PREPROCESS_ERRO: OpenCV não conseguiu carregar a imagem: {image_path}")
            return image_path
        print(f"V19_PREPROCESS: OpenCV carregou a imagem: {image_path} com dimensões {img.shape}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("V19_PREPROCESS: Imagem convertida para escala de cinza.")

        _, processed_for_ocr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("V19_PREPROCESS: Aplicado Limiar de Otsu em 'gray'.")
        processed_filename = f"temp_v19_otsu_processed_{safe_name_part}{ext if ext else '.png'}"

        processed_path = os.path.join(output_folder, processed_filename)
        print(f"V19_PREPROCESS: Caminho da imagem processada será: {processed_path}")

        if cv2.imwrite(processed_path, processed_for_ocr):
            print(f"V19_PREPROCESS_SUCESSO: Imagem pré-processada salva em: {processed_path}")
            return processed_path
        else:
            print(f"V19_PREPROCESS_ERRO: cv2.imwrite falhou ao salvar em {processed_path}.")
            return image_path
    except Exception as e:
        print(f"V19_PREPROCESS_ERRO_GRAVE: Erro no pré-processamento com OpenCV: {e}")
        traceback.print_exc()
        return image_path

def extract_text_from_image(image_path):
    print(f"====== V19: ENTROU EM EXTRACT_TEXT_FROM_IMAGE ======")
    # ... (Lógica da v18, apenas atualizando os prints para V19)
    print(f"V19_EXTRACT: Recebido image_path original: {image_path}")
    path_para_tesseract = image_path
    try:
        print(f"V19_EXTRACT: Chamando preprocess_image_for_ocr para: {image_path}")
        path_da_imagem_processada = preprocess_image_for_ocr(image_path)
        if path_da_imagem_processada != image_path and os.path.exists(path_da_imagem_processada):
            print(f"V19_EXTRACT: Usando IMAGEM PRÉ-PROCESSADA para OCR: {path_da_imagem_processada}")
            path_para_tesseract = path_da_imagem_processada
        else:
             print(f"V19_EXTRACT: Usando ORIGINAL para OCR (pré-processamento falhou ou não alterou): {image_path}")

        print(f"V19_EXTRACT: Abrindo '{path_para_tesseract}' com PIL para OCR.")
        img_to_ocr = Image.open(path_para_tesseract)
        custom_config = r'--oem 3 --psm 3 -l por --dpi 300 -c tessedit_do_invert=0'
        print(f"V19_EXTRACT: Tentando OCR com config: {custom_config}")
        texto = pytesseract.image_to_string(img_to_ocr, config=custom_config)
        print(f"--- V19: Texto Extraído do OCR ---\n{texto}\n---------------------------")
        return texto
    except Exception as e:
        print(f"V19_EXTRACT_ERRO_FATAL: Erro ao extrair texto: {e}")
        traceback.print_exc()
        return None

# --- Função parse_cpf ATUALIZADA (v19) ---
def parse_cpf(text):
    print("====== V19: ENTROU EM PARSE_CPF (Foco no Rótulo - v2) ======")

    # Regex para capturar os 11 dígitos do CPF, permitindo separadores comuns ou OCR noise
    # Padrão: xxx.xxx.xxx-xx ou xxx xxx xxx xx ou xxxxxxxxxxx
    # Esta regex tenta capturar os blocos de dígitos e o que pode estar entre eles.
    # \D*? significa "qualquer não-dígito, zero ou mais vezes, o mais curto possível"
    cpf_regex_flexible = r'(\d{3})\D*?(\d{3})\D*?(\d{3})\D*?(\d{2})'

    # Prioridade 1: Procurar perto do rótulo "CPF"
    linhas = text.split('\n')
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()
        if "CPF" in linha_upper:
            # Analisa a linha do rótulo e as próximas 2 linhas
            for j in range(i, min(i + 3, len(linhas))): # Analisa a linha atual (i) e as duas seguintes (i+1, i+2)
                linha_busca = linhas[j]

                # Se o rótulo "CPF" estiver na linha de busca, tenta pegar o que vem depois
                texto_para_buscar_cpf = linha_busca
                if "CPF" in linha_busca.upper(): # Verifica se o rótulo está nesta linha específica
                    match_label_part = re.search(r'CPF\s*[:\s-]*?(.*)', linha_busca, re.IGNORECASE)
                    if match_label_part and match_label_part.group(1):
                        texto_para_buscar_cpf = match_label_part.group(1).strip()
                    elif j == i : # Se o rótulo CPF está na linha 'i' mas não há nada depois, usa a linha seguinte
                         if i + 1 < len(linhas):
                            texto_para_buscar_cpf = linhas[i+1].strip()
                         else:
                            continue # Não há linha seguinte

                if not texto_para_buscar_cpf and j > i : # Se estamos numa linha seguinte ao rótulo e ela não foi pega acima
                    texto_para_buscar_cpf = linha_busca.strip()

                if texto_para_buscar_cpf: # Só processa se houver texto para buscar
                    match = re.search(cpf_regex_flexible, texto_para_buscar_cpf)
                    if match:
                        cpf_extraido_digitos = "".join(match.groups()) # Junta os 4 grupos de dígitos
                        if len(cpf_extraido_digitos) == 11:
                            # Formata para xxx.xxx.xxx-xx para consistência
                            cpf_formatado = f"{cpf_extraido_digitos[:3]}.{cpf_extraido_digitos[3:6]}.{cpf_extraido_digitos[6:9]}-{cpf_extraido_digitos[9:]}"
                            print(f"V19_PARSE_CPF: Encontrado por rótulo 'CPF': {cpf_formatado} (original no OCR: '{match.group(0).strip()}')")
                            return cpf_formatado

    # Prioridade 2: Busca geral pelo padrão formatado xxx.xxx.xxx-xx (se não encontrou com rótulo)
    match_formatado_geral = re.search(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b', text)
    if match_formatado_geral:
        print(f"V19_PARSE_CPF: Encontrado por regex geral (formato completo): {match_formatado_geral.group(0)}")
        return match_formatado_geral.group(0)

    # Prioridade 3: Busca geral pelo padrão com espaços xxx xxx xxx xx
    match_espacos_geral = re.search(r'\b(\d{3}\s\d{3}\s\d{3}\s\d{2})\b', text)
    if match_espacos_geral:
        print(f"V19_PARSE_CPF: Encontrado por regex geral (com espaços): {match_espacos_geral.group(0)}")
        return match_espacos_geral.group(0)

    print("V19_PARSE_CPF: Não encontrado após todas as tentativas.")
    return None

# --- Funções parse_rg, parse_nome, parse_cns, parse_data_nascimento, calcular_idade (da v18) ---
# Cole as suas versões mais recentes e funcionais destas funções aqui, com os prints V19_PARSE_...
def parse_rg(text):
    print("====== V19: ENTROU EM PARSE_RG (COMPLETO) ======")
    # ... (código da v18)
    rg_match_label = re.search(
        r'(?:DOC\.?\s*IDENTIDADE(?:/ORG\.?\s*EMISSOR(?:/UF)?)?|REGISTRO\s*GERAL|RG\s*N[ºo]?\.?)\s*[:\s-]*([0-9\.\s-]{5,15}[\dX]?)',
        text,
        re.IGNORECASE
    )
    if rg_match_label and rg_match_label.group(1):
        rg_candidate = rg_match_label.group(1).strip().splitlines()[0]
        rg_candidate = re.sub(r'\s*(?:SESP|SSP)\s*\w{2}\s*$', '', rg_candidate, flags=re.IGNORECASE).strip()
        rg_digits_only = re.sub(r'\D', '', rg_candidate)
        if not (len(rg_digits_only) == 11 and ('-' in rg_candidate or '.' in rg_candidate)):
            if rg_digits_only:
                print(f"V19_PARSE_RG: Encontrado por rótulo: {rg_candidate}")
                return rg_candidate
    matches = re.findall(r'\b(?:\d{1,2}(?:\.?\d{3}){2}-?[\dX0-9])\b|\b\d{7,9}[\dX]?\b', text)
    for rg_candidate in matches:
        rg_digits_only = re.sub(r'\D', '', rg_candidate)
        if len(rg_digits_only) == 11 and ('-' in rg_candidate or '.' in rg_candidate):
            continue
        if len(rg_digits_only) >= 7 and len(rg_digits_only) <= 10:
            is_cnh_registro_num = False
            if rg_candidate.isdigit() and len(rg_digits_only) >=9:
                try:
                    idx = text.upper().find(rg_candidate)
                    texto_anterior = text.upper()[max(0, idx - 20):idx]
                    if "REGISTRO" in texto_anterior or "RENACH" in texto_anterior:
                        is_cnh_registro_num = True
                except:
                    pass
            if not is_cnh_registro_num:
                print(f"V19_PARSE_RG: Encontrado por regex geral: {rg_candidate}")
                return rg_candidate
    print("V19_PARSE_RG: Não encontrado.")
    return None

def parse_nome(text):
    print("====== V19: ENTROU EM PARSE_NOME (COMPLETO) ======")
    # ... (código da v18)
    linhas = text.split('\n')
    melhor_candidato_nome_titular = None
    pontuacao_max_nome_titular = -1
    todos_candidatos_potenciais_fase2 = []

    for i, linha in enumerate(linhas):
        linha_limpa = linha.strip()
        if not linha_limpa or len(linha_limpa) < 3:
            continue
        linha_upper = linha_limpa.upper()
        palavras_na_linha = re.findall(r'\b\w+\b', linha_upper)
        if not palavras_na_linha: continue

        if i > 0:
            linha_anterior = linhas[i-1].strip().upper()
            if linha_anterior == "NOME" or \
               linha_anterior == "NOME / NAME" or \
               "NOME DO BENEFICIARIO" in linha_anterior or \
               (linha_anterior.startswith("NOME") and len(linha_anterior) < 10):
                if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa) and \
                   not any(rotulo_forte == linha_upper for rotulo_forte in ROTULOS_FORTES) and \
                   "FILIAÇÃO" not in linha_upper and "FILIACAO" not in linha_upper and \
                   len(palavras_na_linha) >=2 and len(palavras_na_linha) <=7:
                    pontuacao_atual = len(linha_limpa)
                    if linha_anterior == "NOME": pontuacao_atual += 10
                    if pontuacao_atual > pontuacao_max_nome_titular:
                        pontuacao_max_nome_titular = pontuacao_atual
                        melhor_candidato_nome_titular = linha_limpa
                        print(f"V19_PARSE_NOME: Forte candidato (Fase 1) encontrado abaixo do rótulo '{linha_anterior}': '{linha_limpa}'")

    if melhor_candidato_nome_titular:
        print(f"V19_PARSE_NOME: Nome do titular escolhido (Fase 1): '{melhor_candidato_nome_titular}'")
        return melhor_candidato_nome_titular

    print("V19_PARSE_NOME: Nome do titular não encontrado na Fase 1. Usando heurística geral (Fase 2)...")
    melhor_candidato_geral = None
    max_pontuacao_geral = -1

    for i, linha in enumerate(linhas):
        linha_limpa = linha.strip()
        if not linha_limpa or len(linha_limpa) < 3:
            continue
        linha_upper = linha_limpa.upper()
        if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa):
            todos_candidatos_potenciais_fase2.append(linha_limpa)
        if any(rotulo == linha_upper for rotulo in ROTULOS_FORTES):
            continue
        if "FILIAÇÃO" in linha_upper or "FILIACAO" in linha_upper:
            continue

        linha_abaixo_de_filiacao = False
        if i > 0:
            linha_anterior_upper = linhas[i-1].strip().upper()
            if "FILIAÇÃO" in linha_anterior_upper or "FILIACAO" in linha_anterior_upper:
                linha_abaixo_de_filiacao = True

        palavras_na_linha = re.findall(r'\b\w+\b', linha_upper)
        if not palavras_na_linha: continue
        count_palavras_chave = sum(1 for p in palavras_na_linha if p in PALAVRAS_CHAVE_IGNORAR_PARA_NOME)

        pontuacao = 0
        if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa) and \
           not re.match(r'^[\d\s.,/-]+$', linha_limpa):
            if len(palavras_na_linha) >= 2 and len(palavras_na_linha) <= 7:
                pontuacao += 10
            if count_palavras_chave > 0:
                pontuacao -= count_palavras_chave * 5
            if len(linha_limpa) < 10 :
                pontuacao -= 5
            pontuacao += len(palavras_na_linha)
            if any(rf in linha_upper for rf in ROTULOS_FORTES):
                pontuacao -= 20
            if linha_abaixo_de_filiacao:
                pontuacao -= 30
            if pontuacao > max_pontuacao_geral:
                max_pontuacao_geral = pontuacao
                melhor_candidato_geral = linha_limpa

    print(f"V19_PARSE_NOME: Todos os candidatos potenciais (Fase 2 - debug): {todos_candidatos_potenciais_fase2}")
    if melhor_candidato_geral and max_pontuacao_geral > 0:
        print(f"V19_PARSE_NOME: Melhor candidato (Fase 2): '{melhor_candidato_geral}' com pontuação: {max_pontuacao_geral}")
        return melhor_candidato_geral

    print(f"V19_PARSE_NOME: Nome não encontrado com pontuação suficiente (Fase 2). Melhor pontuação: {max_pontuacao_geral}")
    candidatos_fallback = []
    for linha in linhas:
        linha_limpa = linha.strip()
        linha_upper = linha_limpa.upper()
        if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa) and \
           not any(rotulo in linha_upper for rotulo in ROTULOS_FORTES) and \
           not any(kw in linha_upper for kw in PALAVRAS_CHAVE_IGNORAR_PARA_NOME) and \
           "FILIAÇÃO" not in linha_upper and "FILIACAO" not in linha_upper:
            if len(linha_limpa.split()) >=2 and len(linha_limpa.split()) <=7:
                candidatos_fallback.append(linha_limpa)
    if candidatos_fallback:
        candidatos_fallback.sort(key=len, reverse=True)
        print(f"V19_PARSE_NOME: Nome de fallback (última tentativa, mais longo): {candidatos_fallback[0]}")
        return candidatos_fallback[0]
    print("V19_PARSE_NOME: Nome não extraído.")
    return "Nome não extraído"

def parse_cns(text):
    print("====== V19: ENTROU EM PARSE_CNS (COMPLETO) ======")
    # ... (código da v18)
    rotulos_cns = ["NÚMERO DO CARTÃO", "NUMERO DO CARTAO", "CARTAO NACIONAL DE SAUDE", "CNS"]
    linhas_texto = text.split('\n')
    for i, linha in enumerate(linhas_texto):
        linha_upper = linha.upper().strip()
        for rotulo in rotulos_cns:
            if rotulo in linha_upper:
                texto_apos_rotulo = linha_upper.split(rotulo, 1)[-1]
                match_numeros_mesma_linha = re.search(r'\b(\d[\s\d]*\d)\b', texto_apos_rotulo)
                if match_numeros_mesma_linha:
                    cns_candidate = re.sub(r'\D', '', match_numeros_mesma_linha.group(1))
                    if len(cns_candidate) == 15:
                        print(f"V19_PARSE_CNS: Encontrado por rótulo '{rotulo}' na mesma linha: {cns_candidate}")
                        return cns_candidate
                if i + 1 < len(linhas_texto):
                    linha_seguinte = linhas_texto[i+1].strip()
                    match_numeros_linha_seguinte = re.search(r'\b(\d[\s\d]*\d)\b', linha_seguinte)
                    if match_numeros_linha_seguinte:
                        cns_candidate_seguinte = re.sub(r'\D', '', match_numeros_linha_seguinte.group(1))
                        if len(cns_candidate_seguinte) == 15:
                            print(f"V19_PARSE_CNS: Encontrado por rótulo '{rotulo}' na linha seguinte: {cns_candidate_seguinte}")
                            return cns_candidate_seguinte
    match_geral = re.search(r'\b\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\b|\b\d{15}\b', text)
    if match_geral:
        cns_limpo = re.sub(r'\D', '', match_geral.group(0))
        if len(cns_limpo) == 15:
            print(f"V19_PARSE_CNS: Encontrado por regex geral: {cns_limpo}")
            return cns_limpo
    print(f"V19_PARSE_CNS: Não encontrado.")
    return None

def parse_data_nascimento(text):
    print("====== V19: ENTROU EM PARSE_DATA_NASCIMENTO (Refinada) ======")
    # ... (código da v18)
    regex_data = r'\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b'
    linhas = text.split('\n')
    candidatos_data_nasc = []
    datas_a_ignorar = []

    for linha_idx, linha_content in enumerate(linhas):
        linha_upper_content = linha_content.upper().strip()
        if any(rot_ignorar in linha_upper_content for rot_ignorar in ["VALIDADE", "EXPIRY", "EMISSÃO", "EMISSAO", "HABILITAÇÃO"]):
            matches_outras = re.findall(regex_data, linha_content)
            for data_outra in matches_outras:
                print(f"V19_PARSE_DN: Data a IGNORAR (mesma linha do rótulo de validade/emissão/habilitação): {data_outra}")
                datas_a_ignorar.append(data_outra)
            if linha_idx + 1 < len(linhas):
                matches_outras_seguinte = re.findall(regex_data, linhas[linha_idx+1])
                for data_outra_seg in matches_outras_seguinte:
                    print(f"V19_PARSE_DN: Data a IGNORAR (linha seguinte ao rótulo de validade/emissão/habilitação): {data_outra_seg}")
                    datas_a_ignorar.append(data_outra_seg)

    datas_a_ignorar = list(set(datas_a_ignorar))
    print(f"V19_PARSE_DN: Datas de Validade/Emissão/Habilitação identificadas para exclusão: {datas_a_ignorar}")

    for i, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()

        if any(rot_nasc in linha_upper for rot_nasc in ["DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH", "NASC."]):
            texto_apos_rotulo = re.sub(r'.*(?:DATA\sNASCIMENTO|DATA\sNASC\.|DATE\sOF\sBIRTH|NASC\.)\s*[:\s-]*', '', linha, flags=re.IGNORECASE).strip()
            match_data_mesma_linha = re.search(regex_data, texto_apos_rotulo)
            if match_data_mesma_linha:
                data_str = match_data_mesma_linha.group(1)
                if data_str not in datas_a_ignorar:
                    print(f"V19_PARSE_DN: Candidato DN (mesma linha, após rótulo): {data_str}")
                    candidatos_data_nasc.append({"data": data_str, "prioridade": 10})

            if (not match_data_mesma_linha or (match_data_mesma_linha and match_data_mesma_linha.group(1) in datas_a_ignorar)) and i + 1 < len(linhas):
                match_data_linha_seguinte = re.search(regex_data, linhas[i+1])
                if match_data_linha_seguinte:
                    data_str = match_data_linha_seguinte.group(1)
                    if data_str not in datas_a_ignorar:
                        print(f"V19_PARSE_DN: Candidato DN (linha seguinte, após rótulo): {data_str}")
                        candidatos_data_nasc.append({"data": data_str, "prioridade": 9})

    if not candidatos_data_nasc:
        print("V19_PARSE_DN: Nenhuma data encontrada perto de rótulos de nascimento. Tentando busca geral.")
        for linha in linhas:
            linha_upper = linha.upper().strip()
            if not any(rot_ignorar in linha_upper for rot_ignorar in ROTULOS_FORTES):
                matches_gerais = re.findall(regex_data, linha)
                for data_str in matches_gerais:
                    if data_str not in datas_a_ignorar and not any(item["data"] == data_str for item in candidatos_data_nasc):
                        print(f"V19_PARSE_DN: Candidato DN (busca geral): {data_str}")
                        candidatos_data_nasc.append({"data": data_str, "prioridade": 5})

    print(f"V19_PARSE_DN: Candidatos Data Nasc (com prioridade, antes de filtrar): {candidatos_data_nasc}")

    candidatos_unicos_dict = {}
    for item in candidatos_data_nasc:
        if item["data"] not in candidatos_unicos_dict or item["prioridade"] > candidatos_unicos_dict[item["data"]]["prioridade"]:
            candidatos_unicos_dict[item["data"]] = item
    candidatos_data_nasc_filtrados = sorted(candidatos_unicos_dict.values(), key=lambda x: x["prioridade"], reverse=True)
    print(f"V19_PARSE_DN: Candidatos Data Nasc (filtrados e ordenados): {candidatos_data_nasc_filtrados}")

    if candidatos_data_nasc_filtrados:
        ano_atual = date.today().year
        for item_cand in candidatos_data_nasc_filtrados:
            data_str_cand = item_cand["data"]
            try:
                data_normalizada = data_str_cand.replace('.', '/').replace('-', '/')
                partes_data = re.split(r'[/]', data_normalizada)
                if len(partes_data) != 3: continue
                dia, mes, ano_str_val = map(int, partes_data)

                ano = 0
                if len(str(ano_str_val)) == 2:
                    if ano_str_val > (ano_atual % 100) + 5 :
                        ano = int(f"19{ano_str_val}")
                    else:
                        ano = int(f"20{ano_str_val:02d}")
                elif len(str(ano_str_val)) == 4:
                    ano = ano_str_val
                else:
                    continue

                if 1900 < ano <= ano_atual :
                    data_nasc_obj = date(ano, mes, dia)
                    if data_nasc_obj < date.today() and (ano_atual - ano) <= 120 :
                        print(f"V19_PARSE_DN: Data de Nascimento VÁLIDA escolhida: {data_nasc_obj.strftime('%d/%m/%Y')}")
                        return data_nasc_obj.strftime('%d/%m/%Y')
            except:
                print(f"V19_PARSE_DN: Erro ao processar/validar candidato de data '{data_str_cand}'")
                continue

        if candidatos_data_nasc_filtrados:
             print(f"V19_PARSE_DN: Nenhuma data 100% validada, retornando o candidato de maior prioridade da lista: {candidatos_data_nasc_filtrados[0]['data']}")
             return candidatos_data_nasc_filtrados[0]['data']

    print("V19_PARSE_DN: Data de Nascimento não encontrada após todas as tentativas.")
    return None

def calcular_idade(data_nascimento_str):
    if not data_nascimento_str:
        return None
    print(f"V19_CALC_IDADE: Tentando calcular idade para: {data_nascimento_str}")
    # ... (código da v18)
    try:
        data_nasc_normalizada = data_nascimento_str.replace('.', '/').replace('-', '/')
        formatos_data = ["%d/%m/%Y", "%d/%m/%y"]
        data_nasc_obj = None
        for fmt in formatos_data:
            try:
                data_nasc_obj = datetime.strptime(data_nasc_normalizada, fmt).date()
                break
            except ValueError:
                continue

        if not data_nasc_obj:
            print(f"V19_CALC_IDADE_ERRO: Formato de data não reconhecido após tentativas: {data_nasc_normalizada}")
            return None

        hoje = date.today()
        idade = hoje.year - data_nasc_obj.year - ((hoje.month, hoje.day) < (data_nasc_obj.month, data_nasc_obj.day))

        if idade < 0 or idade > 120:
            print(f"V19_CALC_IDADE_ERRO: Idade calculada ({idade}) implausível para data de nascimento {data_nasc_obj}.")
            return None

        print(f"V19_CALC_IDADE: Idade calculada: {idade}")
        return idade
    except Exception as e:
        print(f"V19_CALC_IDADE_ERRO: Erro ao calcular idade para '{data_nascimento_str}': {e}")
        return None

