import pytesseract
from PIL import Image
import re
import os
import cv2
import traceback

print("====== MODULO OCR_UTILS.PY (v13 - Otsu em gray como Padrão CORRIGIDO) CARREGADO ======")

# --- Mantenha suas listas PALAVRAS_CHAVE_IGNORAR_PARA_NOME e ROTULOS_FORTES ---
PALAVRAS_CHAVE_IGNORAR_PARA_NOME = [
    "CPF", "NASCIMENTO", "DATA", "NATURALIDADE",
    "ASSINATURA", "POLEGAR", "IDENTIDADE", "SECRETARIA", "SEGURANÇA", "SEGURANCA",
    "PÚBLICA", "PUBLICA", "REPUBLICA", "FEDERATIVA", "BRASIL", "MINISTERIO", "JUSTICA", "INFRAESTRUTURA",
    "DEPARTAMENTO", "POLICIA", "REGISTRO", "GERAL", "VALIDADE", "EMISSOR",
    "DOC", "SSP", "SESP", "DETRAN", "UF", "HABILITACAO", "ACC", "CAT", "PERMISSÃO", "PERMISSAO",
    "CNH", "RENACH", "EMISSÃO", "EMISSAO", "NACIONAL", "TRANSITO", "CONSELHO", "SUS", "CARTAO",
    "BENEFICIARIO", "USUARIO", "PORTADOR", "TITULAR", "OBSERVAÇÕES", "LOCAL", "TERRITORIO", "FILHO", "FILHA"
]
ROTULOS_FORTES = [
    "NOME", "NAME", "NOME SOCIAL", "NOME DO BENEFICIARIO",
    "CPF", "REGISTRO GERAL", "DOC. IDENTIDADE", "DOC IDENTIDADE", "IDENTIDADE/ORG", "DOC.IDENTIDADE/ORG.EMISSOR/UF",
    "FILIAÇÃO", "FILIACAO", "NOME DO PAI", "NOME DA MÃE",
    "DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH",
    "NÚMERO DO CARTÃO", "NUMERO DO CARTAO", "Nº REGISTRO"
]

def preprocess_image_for_ocr(image_path, output_folder="app/static/uploads"):
    print(f"====== V13: ENTROU EM PREPROCESS_IMAGE_FOR_OCR ======")
    print(f"V13_PREPROCESS: Recebido image_path: {image_path}")
    try:
        original_basename = os.path.basename(image_path)
        os.makedirs(output_folder, exist_ok=True)
        name_part, ext = os.path.splitext(original_basename)
        safe_name_part = re.sub(r'[^\w\.-]', '_', name_part)

        # Define o nome do arquivo processado com base na técnica PADRÃO (Otsu em gray)
        processed_filename = f"temp_v13_otsu_gray_processed_{safe_name_part}{ext if ext else '.png'}"
        processed_path = os.path.join(output_folder, processed_filename)
        print(f"V13_PREPROCESS: Caminho da imagem processada será: {processed_path}")

        img = cv2.imread(image_path)
        if img is None:
            print(f"V13_PREPROCESS_ERRO: OpenCV não conseguiu carregar a imagem: {image_path}")
            return image_path # Retorna original se não puder carregar
        print(f"V13_PREPROCESS: OpenCV carregou a imagem: {image_path} com dimensões {img.shape}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("V13_PREPROCESS: Imagem convertida para escala de cinza.")

        # --- TÉCNICA PADRÃO: LIMIAR DE OTSU APLICADO DIRETAMENTE EM 'gray' ---
        # Esta funcionou bem para a CNH.
        _, processed_for_ocr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("V13_PREPROCESS: Aplicado Limiar de Otsu em 'gray'.")

        # --- OPÇÕES PARA EXPERIMENTAR DEPOIS (MANTENHA COMENTADAS INICIALMENTE) ---
        # Para testar uma opção, comente a linha do Otsu acima e descomente a opção desejada.
        # Lembre-se de ajustar 'processed_filename' e 'processed_path' se mudar a técnica,
        # para que o nome do arquivo salvo reflita o método usado.

        # Opção 1: Limiar Adaptativo Gaussiano
        # processed_for_ocr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                                           cv2.THRESH_BINARY, 11, 2) # blockSize=11, C=2
        # print("V13_PREPROCESS: Aplicado Limiar Adaptativo Gaussiano.")
        # processed_filename = f"temp_v13_adaptive_processed_{safe_name_part}{ext if ext else '.png'}"
        # processed_path = os.path.join(output_folder, processed_filename)

        # Opção 2: Desfoque Mediano ANTES do Limiar de Otsu
        # gray_blurred = cv2.medianBlur(gray, 3)
        # print("V13_PREPROCESS: Aplicado Desfoque Mediano.")
        # _, processed_for_ocr = cv2.threshold(gray_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) # Usa gray_blurred
        # print("V13_PREPROCESS: Aplicado Limiar de Otsu APÓS Desfoque Mediano.")
        # processed_filename = f"temp_v13_median_otsu_processed_{safe_name_part}{ext if ext else '.png'}"
        # processed_path = os.path.join(output_folder, processed_filename)

        if cv2.imwrite(processed_path, processed_for_ocr):
            print(f"V13_PREPROCESS_SUCESSO: Imagem pré-processada salva em: {processed_path}")
            return processed_path # Retorna o caminho da imagem PROCESSADA
        else:
            print(f"V13_PREPROCESS_ERRO: cv2.imwrite falhou ao salvar em {processed_path}.")
            return image_path # Retorna original se não conseguiu salvar
    except Exception as e:
        print(f"V13_PREPROCESS_ERRO_GRAVE: Erro no pré-processamento com OpenCV: {e}")
        traceback.print_exc()
        return image_path # Retorna original em caso de erro grave

# --- extract_text_from_image e as funções de PARSING (parse_cpf, parse_rg, parse_nome, parse_cns) ---
# Use as mesmas da v12 anterior (que eram baseadas na v10/v6 com correção da regex do CPF)
# Apenas atualize os prints internos para "V13_..." para consistência no log.

def extract_text_from_image(image_path):
    print(f"====== V13: ENTROU EM EXTRACT_TEXT_FROM_IMAGE ======")
    print(f"V13_EXTRACT: Recebido image_path original: {image_path}")
    path_para_tesseract = image_path
    try:
        print(f"V13_EXTRACT: Chamando preprocess_image_for_ocr para: {image_path}")
        path_da_imagem_processada = preprocess_image_for_ocr(image_path)
        if path_da_imagem_processada != image_path and os.path.exists(path_da_imagem_processada):
            print(f"V13_EXTRACT: Usando IMAGEM PRÉ-PROCESSADA para OCR: {path_da_imagem_processada}")
            path_para_tesseract = path_da_imagem_processada
        elif path_da_imagem_processada == image_path:
            print(f"V13_EXTRACT: Pré-processamento retornou o caminho original. Usando ORIGINAL para OCR: {image_path}")
        else:
             print(f"V13_EXTRACT_ERRO: Imagem pré-processada '{path_da_imagem_processada}' não encontrada. Usando ORIGINAL: {image_path}")

        print(f"V13_EXTRACT: Abrindo '{path_para_tesseract}' com PIL para OCR.")
        img_to_ocr = Image.open(path_para_tesseract)
        custom_config = r'--oem 3 --psm 3 -l por --dpi 300 -c tessedit_do_invert=0'
        print(f"V13_EXTRACT: Tentando OCR com config: {custom_config}")
        texto = pytesseract.image_to_string(img_to_ocr, config=custom_config)
        print(f"--- V13: Texto Extraído do OCR ---\n{texto}\n---------------------------")
        return texto
    except Exception as e:
        print(f"V13_EXTRACT_ERRO_FATAL: Erro ao extrair texto: {e}")
        traceback.print_exc()
        return None

def parse_cpf(text):
    print("====== V13: ENTROU EM PARSE_CPF (COMPLETO) ======")
    cpf_match_label = re.search(r'(?:CPF)\s*[:\s-]*\s*([0-9\.\s-]{11,14})', text, re.IGNORECASE)
    if cpf_match_label and cpf_match_label.group(1):
        cpf_candidate = cpf_match_label.group(1).strip()
        cpf_cleaned = re.sub(r'\D', '', cpf_candidate)
        if len(cpf_cleaned) == 11:
            print(f"V13_PARSE_CPF: Encontrado por rótulo: {cpf_candidate}")
            return cpf_candidate
    match_format_completo = re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text)
    if match_format_completo:
        print(f"V13_PARSE_CPF: Encontrado por regex geral (formato completo): {match_format_completo.group(0)}")
        return match_format_completo.group(0)
    match_com_espacos = re.search(r'\b\d{3}\s\d{3}\s\d{3}\s\d{2}\b', text)
    if match_com_espacos:
        print(f"V13_PARSE_CPF: Encontrado por regex geral (com espaços): {match_com_espacos.group(0)}")
        return match_com_espacos.group(0)
    all_11_digits = re.findall(r'\b\d{11}\b', text)
    for num_11 in all_11_digits:
        try:
            idx = text.find(num_11)
            texto_anterior = text[max(0, idx - 20):idx].upper()
            if "REGISTRO" not in texto_anterior and "RENACH" not in texto_anterior:
                print(f"V13_PARSE_CPF: Encontrado por regex geral (11 dígitos): {num_11}")
                return num_11
        except:
            pass
    print("V13_PARSE_CPF: Não encontrado.")
    return None

def parse_rg(text):
    print("====== V13: ENTROU EM PARSE_RG (COMPLETO) ======")
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
                print(f"V13_PARSE_RG: Encontrado por rótulo: {rg_candidate}")
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
                print(f"V13_PARSE_RG: Encontrado por regex geral: {rg_candidate}")
                return rg_candidate
    print("V13_PARSE_RG: Não encontrado.")
    return None

def parse_nome(text):
    print("====== V13: ENTROU EM PARSE_NOME (COMPLETO) ======")
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
               "NOME / NAME" in linha_anterior or \
               "NOME DO BENEFICIARIO" in linha_anterior or \
               (linha_anterior.startswith("NOME") and len(linha_anterior) < 10):
                if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa) and \
                   not any(rotulo_forte == linha_upper for rotulo_forte in ROTULOS_FORTES) and \
                   "FILIAÇÃO" not in linha_upper and "FILIACAO" not in linha_upper and \
                   len(palavras_na_linha) >=2 and len(palavras_na_linha) <=7:
                    pontuacao_atual = len(linha_limpa)
                    if pontuacao_atual > pontuacao_max_nome_titular:
                        pontuacao_max_nome_titular = pontuacao_atual
                        melhor_candidato_nome_titular = linha_limpa
                        print(f"V13_PARSE_NOME: Forte candidato (Fase 1) encontrado abaixo do rótulo '{linha_anterior}': '{linha_limpa}'")

    if melhor_candidato_nome_titular:
        print(f"V13_PARSE_NOME: Nome do titular escolhido (Fase 1): '{melhor_candidato_nome_titular}'")
        return melhor_candidato_nome_titular

    print("V13_PARSE_NOME: Nome do titular não encontrado na Fase 1. Usando heurística geral (Fase 2)...")
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

    print(f"V13_PARSE_NOME: Todos os candidatos potenciais (Fase 2 - debug): {todos_candidatos_potenciais_fase2}")
    if melhor_candidato_geral and max_pontuacao_geral > 0:
        print(f"V13_PARSE_NOME: Melhor candidato (Fase 2): '{melhor_candidato_geral}' com pontuação: {max_pontuacao_geral}")
        return melhor_candidato_geral

    print(f"V13_PARSE_NOME: Nome não encontrado com pontuação suficiente (Fase 2). Melhor pontuação: {max_pontuacao_geral}")
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
        print(f"V13_PARSE_NOME: Nome de fallback (última tentativa, mais longo): {candidatos_fallback[0]}")
        return candidatos_fallback[0]
    print("V13_PARSE_NOME: Nome não extraído.")
    return "Nome não extraído"

def parse_cns(text):
    print("====== V13: ENTROU EM PARSE_CNS (COMPLETO) ======")
    rotulos_cns = ["NÚMERO DO CARTÃO", "NUMERO DO CARTAO", "CARTAO NACIONAL DE SAUDE", "CNS"]
    for linha in text.split('\n'):
        linha_upper = linha.upper()
        for rotulo in rotulos_cns:
            if rotulo in linha_upper:
                texto_apos_rotulo = linha_upper.split(rotulo, 1)[-1]
                match_numeros = re.search(r'\b(\d[\s\d]*\d)\b', texto_apos_rotulo)
                if match_numeros:
                    cns_candidate = re.sub(r'\D', '', match_numeros.group(1))
                    if len(cns_candidate) == 15:
                        print(f"V13_PARSE_CNS: Encontrado por rótulo '{rotulo}': {cns_candidate}")
                        return cns_candidate
    match = re.search(r'\b\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\b|\b\d{15}\b', text)
    if match:
        cns_limpo = re.sub(r'\D', '', match.group(0))
        if len(cns_limpo) == 15:
            print(f"V13_PARSE_CNS: Encontrado por regex geral: {cns_limpo}")
            return cns_limpo
    print("V13_PARSE_CNS: Não encontrado.")
    return None
