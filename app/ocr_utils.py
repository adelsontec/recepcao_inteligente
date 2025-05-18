import pytesseract
from PIL import Image
import re
import os
import cv2
import traceback
from datetime import datetime, date

print("====== MODULO OCR_UTILS.PY (FINAL - Nome, CPF, DN) CARREGADO ======")

# --- Listas de Palavras-Chave e Rótulos ---
PALAVRAS_CHAVE_IGNORAR_PARA_NOME = [
    "CPF", "NASCIMENTO", "DATA", "NATURALIDADE", "RG",
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
    "CPF", "REGISTRO GERAL", "DOC. IDENTIDADE", "DOC IDENTIDADE", "IDENTIDADE/ORG", "DOC.IDENTIDADE/ORG.EMISSOR/UF", "RG",
    "FILIAÇÃO", "FILIACAO", "NOME DO PAI", "NOME DA MÃE",
    "DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH", "NASC.",
    "NÚMERO DO CARTÃO", "NUMERO DO CARTAO", "Nº REGISTRO", "CNS",
    "VALIDADE", "EXPIRY", "DATA DE EMISSÃO", "DATA DE EMISSAO"
]

def preprocess_image_for_ocr(image_path, output_folder="app/static/uploads"):
    print(f"====== FINAL_OCR: ENTROU EM PREPROCESS_IMAGE_FOR_OCR ======")
    print(f"FINAL_OCR_PREPROCESS: Recebido image_path: {image_path}")
    try:
        original_basename = os.path.basename(image_path)
        os.makedirs(output_folder, exist_ok=True)
        name_part, ext = os.path.splitext(original_basename)
        safe_name_part = re.sub(r'[^\w\.-]', '_', name_part)

        processed_filename = f"temp_final_otsu_processed_{safe_name_part}{ext if ext else '.png'}"

        img = cv2.imread(image_path)
        if img is None:
            print(f"FINAL_OCR_PREPROCESS_ERRO: OpenCV não conseguiu carregar a imagem: {image_path}")
            return image_path

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, processed_for_ocr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("FINAL_OCR_PREPROCESS: Aplicado Limiar de Otsu em 'gray'.")

        processed_path = os.path.join(output_folder, processed_filename)
        if cv2.imwrite(processed_path, processed_for_ocr):
            print(f"FINAL_OCR_PREPROCESS_SUCESSO: Imagem pré-processada salva em: {processed_path}")
            return processed_path
        else:
            print(f"FINAL_OCR_PREPROCESS_ERRO: cv2.imwrite falhou ao salvar em {processed_path}.")
            return image_path
    except Exception as e:
        print(f"FINAL_OCR_PREPROCESS_ERRO_GRAVE: Erro no pré-processamento com OpenCV: {e}")
        traceback.print_exc()
        return image_path

def extract_text_from_image(image_path):
    print(f"====== FINAL_OCR: ENTROU EM EXTRACT_TEXT_FROM_IMAGE ======")
    print(f"FINAL_OCR_EXTRACT: Recebido image_path original: {image_path}")
    path_para_tesseract = image_path
    try:
        print(f"FINAL_OCR_EXTRACT: Chamando preprocess_image_for_ocr para: {image_path}")
        path_da_imagem_processada = preprocess_image_for_ocr(image_path)
        if path_da_imagem_processada != image_path and os.path.exists(path_da_imagem_processada):
            print(f"FINAL_OCR_EXTRACT: Usando IMAGEM PRÉ-PROCESSADA para OCR: {path_da_imagem_processada}")
            path_para_tesseract = path_da_imagem_processada
        else:
             print(f"FINAL_OCR_EXTRACT: Usando ORIGINAL para OCR (pré-processamento falhou ou não alterou): {image_path}")

        img_to_ocr = Image.open(path_para_tesseract)
        custom_config = r'--oem 3 --psm 3 -l por --dpi 300 -c tessedit_do_invert=0'
        print(f"FINAL_OCR_EXTRACT: Tentando OCR com config: {custom_config}")
        texto = pytesseract.image_to_string(img_to_ocr, config=custom_config)
        print(f"--- FINAL_OCR: Texto Extraído do OCR ---\n{texto}\n---------------------------")
        return texto
    except Exception as e:
        print(f"FINAL_OCR_EXTRACT_ERRO_FATAL: Erro ao extrair texto: {e}")
        traceback.print_exc()
        return None

def parse_nome(text):
    print("====== FINAL_OCR: ENTROU EM PARSE_NOME ======")
    linhas = text.split('\n')
    melhor_candidato_nome_titular = None
    pontuacao_max_nome_titular = -1
    for i, linha in enumerate(linhas):
        linha_limpa = linha.strip(); linha_upper = linha_limpa.upper()
        if not linha_limpa or len(linha_limpa) < 3: continue
        palavras_na_linha = re.findall(r'\b\w+\b', linha_upper)
        if not palavras_na_linha: continue
        if i > 0:
            linha_anterior = linhas[i-1].strip().upper()
            if any(rot_nome == linha_anterior for rot_nome in ["NOME", "NOME / NAME", "NOME DO BENEFICIARIO"]) or \
               (linha_anterior.startswith("NOME") and len(linha_anterior) < 10):
                if re.match(r'^([A-ZÀ-Ú][a-zà-ú\']+\s?){2,}|([A-ZÀ-Ú\s]{5,})$', linha_limpa) and \
                   not any(rf == linha_upper for rf in ROTULOS_FORTES) and \
                   "FILIAÇÃO" not in linha_upper and "FILIACAO" not in linha_upper and \
                   2 <= len(palavras_na_linha) <= 7:
                    pontuacao_atual = len(linha_limpa) + (10 if linha_anterior == "NOME" else 0)
                    if pontuacao_atual > pontuacao_max_nome_titular:
                        pontuacao_max_nome_titular = pontuacao_atual; melhor_candidato_nome_titular = linha_limpa
    if melhor_candidato_nome_titular:
        print(f"FINAL_OCR_PARSE_NOME: Nome do titular (Fase 1): '{melhor_candidato_nome_titular}'")
        return melhor_candidato_nome_titular
    # Fallback muito simples se a Fase 1 falhar
    for linha in linhas:
        linha_limpa = linha.strip()
        if len(linha_limpa.split()) >= 2 and len(linha_limpa.split()) <= 5: # Nomes com 2 a 5 palavras
            if re.match(r'^[A-ZÀ-Ú\s]+$', linha_limpa) or re.match(r'^([A-ZÀ-Ú][a-zà-ú]+\s?)+$', linha_limpa):
                if not any(kw.upper() in linha_limpa.upper() for kw in PALAVRAS_CHAVE_IGNORAR_PARA_NOME[:10]): # Evita alguns rótulos comuns
                    print(f"FINAL_OCR_PARSE_NOME: Nome de fallback: {linha_limpa}")
                    return linha_limpa
    print("FINAL_OCR_PARSE_NOME: Nome não extraído.")
    return None # Retorna None se não encontrar

def parse_cpf(text):
    print("====== FINAL_OCR: ENTROU EM PARSE_CPF ======")
    cpf_formatado_regex = r'(\d{3}\.\d{3}\.\d{3}-\d{2})'
    linhas = text.split('\n')
    for i, linha_original in enumerate(linhas):
        linha = linha_original.strip(); linha_upper = linha.upper()
        if "CPF" in linha_upper:
            texto_apos_rotulo_cpf = re.sub(r'.*CPF\s*[^0-9a-zA-Z]*', '', linha, flags=re.IGNORECASE).strip()
            match_mesma_linha = re.search(cpf_formatado_regex, texto_apos_rotulo_cpf)
            if match_mesma_linha:
                print(f"FINAL_OCR_PARSE_CPF: Encontrado por rótulo na mesma linha: {match_mesma_linha.group(1)}")
                return match_mesma_linha.group(1)
            for j in range(1, 2): # Verifica apenas a próxima linha
                if i + j < len(linhas):
                    match_linha_seguinte = re.search(r'\b' + cpf_formatado_regex + r'\b', linhas[i+j].strip())
                    if match_linha_seguinte:
                        print(f"FINAL_OCR_PARSE_CPF: Encontrado por rótulo na linha seguinte: {match_linha_seguinte.group(1)}")
                        return match_linha_seguinte.group(1)
    match_geral_formatado = re.search(r'\b' + cpf_formatado_regex + r'\b', text)
    if match_geral_formatado:
        print(f"FINAL_OCR_PARSE_CPF: Encontrado por regex geral (formato completo): {match_geral_formatado.group(0)}")
        return match_geral_formatado.group(0)
    print("FINAL_OCR_PARSE_CPF: Não encontrado.")
    return None # Retorna None se não encontrar

def parse_data_nascimento(text):
    print("====== FINAL_OCR: ENTROU EM PARSE_DATA_NASCIMENTO ======")
    regex_data = r'\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b'; linhas = text.split('\n')
    candidatos_data_nasc = []; datas_a_ignorar = []
    for linha_idx, linha_content in enumerate(linhas):
        linha_upper_content = linha_content.upper().strip()
        if any(rot_ignorar in linha_upper_content for rot_ignorar in ["VALIDADE", "EXPIRY", "EMISSÃO", "EMISSAO", "HABILITAÇÃO"]):
            for data_outra in re.findall(regex_data, linha_content): datas_a_ignorar.append(data_outra)
            if linha_idx + 1 < len(linhas):
                for data_outra_seg in re.findall(regex_data, linhas[linha_idx+1]): datas_a_ignorar.append(data_outra_seg)
    datas_a_ignorar = list(set(datas_a_ignorar)); print(f"FINAL_OCR_PARSE_DN: Datas a ignorar: {datas_a_ignorar}")
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()
        if any(rot_nasc in linha_upper for rot_nasc in ["DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH", "NASC."]):
            texto_apos_rotulo = re.sub(r'.*(?:DATA\sNASCIMENTO|DATA\sNASC\.|DATE\sOF\sBIRTH|NASC\.)\s*[:\s-]*', '', linha, flags=re.IGNORECASE).strip()
            match_data_mesma_linha = re.search(regex_data, texto_apos_rotulo)
            if match_data_mesma_linha and match_data_mesma_linha.group(1) not in datas_a_ignorar:
                candidatos_data_nasc.append({"data": match_data_mesma_linha.group(1), "prioridade": 10})
            elif i + 1 < len(linhas):
                match_data_linha_seguinte = re.search(regex_data, linhas[i+1])
                if match_data_linha_seguinte and match_data_linha_seguinte.group(1) not in datas_a_ignorar:
                    candidatos_data_nasc.append({"data": match_data_linha_seguinte.group(1), "prioridade": 9})
    if not candidatos_data_nasc:
        for linha in linhas:
            if not any(rot_ignorar in linha.upper() for rot_ignorar in ROTULOS_FORTES):
                for data_str in re.findall(regex_data, linha):
                    if data_str not in datas_a_ignorar and not any(item["data"] == data_str for item in candidatos_data_nasc):
                        candidatos_data_nasc.append({"data": data_str, "prioridade": 5})
    candidatos_unicos_dict = {}; [candidatos_unicos_dict.update({item["data"]: item}) for item in sorted(candidatos_data_nasc, key=lambda x: x["prioridade"]) if item["data"] not in candidatos_unicos_dict or item["prioridade"] > candidatos_unicos_dict[item["data"]]["prioridade"]]
    candidatos_data_nasc_filtrados = sorted(candidatos_unicos_dict.values(), key=lambda x: x["prioridade"], reverse=True)
    print(f"FINAL_OCR_PARSE_DN: Candidatos filtrados: {candidatos_data_nasc_filtrados}")
    if candidatos_data_nasc_filtrados:
        ano_atual = date.today().year
        for item_cand in candidatos_data_nasc_filtrados:
            data_str_cand = item_cand["data"]
            try:
                data_normalizada = data_str_cand.replace('.', '/').replace('-', '/'); partes_data = re.split(r'[/]', data_normalizada)
                if len(partes_data) != 3: continue
                dia, mes, ano_str_val = map(int, partes_data)
                ano = int(f"19{ano_str_val}" if len(str(ano_str_val)) == 2 and ano_str_val > (ano_atual % 100) + 5 else f"20{ano_str_val:02d}") if len(str(ano_str_val)) == 2 else ano_str_val
                if 1900 < ano <= ano_atual :
                    data_nasc_obj = date(ano, mes, dia)
                    if data_nasc_obj < date.today() and (ano_atual - ano) <= 120 :
                        print(f"FINAL_OCR_PARSE_DN: Data de Nascimento VÁLIDA: {data_nasc_obj.strftime('%d/%m/%Y')}")
                        return data_nasc_obj.strftime('%d/%m/%Y')
            except: continue
        if candidatos_data_nasc_filtrados: return candidatos_data_nasc_filtrados[0]['data']
    print("FINAL_OCR_PARSE_DN: Não encontrada.")
    return None # Retorna None se não encontrar

def calcular_idade(data_nascimento_str):
    if not data_nascimento_str: return None
    print(f"FINAL_OCR_CALC_IDADE: Calculando para: {data_nascimento_str}")
    try:
        data_nasc_normalizada = data_nascimento_str.replace('.', '/').replace('-', '/'); formatos_data = ["%d/%m/%Y", "%d/%m/%y"]
        data_nasc_obj = None
        for fmt in formatos_data:
            try: data_nasc_obj = datetime.strptime(data_nasc_normalizada, fmt).date(); break
            except ValueError: continue
        if not data_nasc_obj: print(f"FINAL_OCR_CALC_IDADE_ERRO: Formato não reconhecido: {data_nasc_normalizada}"); return None
        hoje = date.today(); idade = hoje.year - data_nasc_obj.year - ((hoje.month, hoje.day) < (data_nasc_obj.month, data_nasc_obj.day))
        if idade < 0 or idade > 120: print(f"FINAL_OCR_CALC_IDADE_ERRO: Idade implausível ({idade})."); return None
        print(f"FINAL_OCR_CALC_IDADE: Idade calculada: {idade}"); return idade
    except Exception as e: print(f"FINAL_OCR_CALC_IDADE_ERRO: Erro: {e}"); return None

# Funções parse_rg e parse_cns removidas
