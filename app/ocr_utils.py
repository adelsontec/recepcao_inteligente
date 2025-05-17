# Versão final do projeto CuidarBot para Imersão IA Alura+Google
import pytesseract
from PIL import Image
import re
import os
import cv2
import traceback
from datetime import datetime, date

print("====== MODULO OCR_UTILS.PY (v20 - Tentativa Final CPF CNH) CARREGADO ======")

# --- Mantenha suas listas PALAVRAS_CHAVE_IGNORAR_PARA_NOME e ROTULOS_FORTES ---
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
    print(f"====== V20: ENTROU EM PREPROCESS_IMAGE_FOR_OCR ======")
    print(f"V20_PREPROCESS: Recebido image_path: {image_path}")
    try:
        original_basename = os.path.basename(image_path)
        os.makedirs(output_folder, exist_ok=True)
        name_part, ext = os.path.splitext(original_basename)
        safe_name_part = re.sub(r'[^\w\.-]', '_', name_part)

        # Padrão: Limiar de Otsu (funcionou bem para CNH)
        processed_filename = f"temp_v20_otsu_processed_{safe_name_part}{ext if ext else '.png'}"

        img = cv2.imread(image_path)
        if img is None:
            print(f"V20_PREPROCESS_ERRO: OpenCV não conseguiu carregar a imagem: {image_path}")
            return image_path

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, processed_for_ocr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("V20_PREPROCESS: Aplicado Limiar de Otsu em 'gray'.")

        processed_path = os.path.join(output_folder, processed_filename)
        if cv2.imwrite(processed_path, processed_for_ocr):
            print(f"V20_PREPROCESS_SUCESSO: Imagem pré-processada salva em: {processed_path}")
            return processed_path
        else:
            print(f"V20_PREPROCESS_ERRO: cv2.imwrite falhou ao salvar em {processed_path}.")
            return image_path
    except Exception as e:
        print(f"V20_PREPROCESS_ERRO_GRAVE: Erro no pré-processamento com OpenCV: {e}")
        traceback.print_exc()
        return image_path

def extract_text_from_image(image_path):
    print(f"====== V20: ENTROU EM EXTRACT_TEXT_FROM_IMAGE ======")
    print(f"V20_EXTRACT: Recebido image_path original: {image_path}")
    path_para_tesseract = image_path
    try:
        print(f"V20_EXTRACT: Chamando preprocess_image_for_ocr para: {image_path}")
        path_da_imagem_processada = preprocess_image_for_ocr(image_path)
        if path_da_imagem_processada != image_path and os.path.exists(path_da_imagem_processada):
            print(f"V20_EXTRACT: Usando IMAGEM PRÉ-PROCESSADA para OCR: {path_da_imagem_processada}")
            path_para_tesseract = path_da_imagem_processada
        else:
             print(f"V20_EXTRACT: Usando ORIGINAL para OCR (pré-processamento falhou ou não alterou): {image_path}")

        img_to_ocr = Image.open(path_para_tesseract)
        custom_config = r'--oem 3 --psm 3 -l por --dpi 300 -c tessedit_do_invert=0'
        print(f"V20_EXTRACT: Tentando OCR com config: {custom_config}")
        texto = pytesseract.image_to_string(img_to_ocr, config=custom_config)
        print(f"--- V20: Texto Extraído do OCR ---\n{texto}\n---------------------------")
        return texto
    except Exception as e:
        print(f"V20_EXTRACT_ERRO_FATAL: Erro ao extrair texto: {e}")
        traceback.print_exc()
        return None

# --- Função parse_cpf ATUALIZADA (v20) ---
def parse_cpf(text):
    print("====== V20: ENTROU EM PARSE_CPF (Foco no Rótulo CNH v3) ======")

    # Regex para o formato de CPF: xxx.xxx.xxx-xx
    cpf_formatado_regex = r'(\d{3}\.\d{3}\.\d{3}-\d{2})'
    # Regex para CPF apenas com números: xxxxxxxxxxx
    cpf_numeros_regex = r'(\b\d{11}\b)'
    linhas = text.split('\n')

    for i, linha_original in enumerate(linhas):
        linha = linha_original.strip()
        linha_upper = linha.upper()

        # Procura pelo rótulo "CPF"
        if "CPF" in linha_upper:
            print(f"V20_PARSE_CPF: Rótulo 'CPF' encontrado na linha: '{linha}'")

            # Tenta encontrar o CPF formatado na mesma linha, APÓS o rótulo "CPF"
            texto_apos_rotulo_cpf = re.sub(r'.*CPF\s*[^0-9a-zA-Z]*', '', linha, flags=re.IGNORECASE).strip()
            match_mesma_linha = re.search(cpf_formatado_regex, texto_apos_rotulo_cpf)
            if match_mesma_linha:
                cpf_candidate = match_mesma_linha.group(1)
                print(f"V20_PARSE_CPF: Encontrado por rótulo 'CPF' na mesma linha (após limpeza): {cpf_candidate}")
                return cpf_candidate

            # Se não encontrou na mesma linha, verifica as próximas 1 ou 2 linhas
            for j in range(1, 3):
                if i + j < len(linhas):
                    linha_seguinte = linhas[i+j].strip()
                    print(f"V20_PARSE_CPF: Verificando linha seguinte ({j}): '{linha_seguinte}' para CPF")
                    # Procura o CPF formatado no início da linha seguinte ou em qualquer parte dela
                    match_linha_seguinte = re.search(r'\b' + cpf_formatado_regex + r'\b', linha_seguinte)
                    if match_linha_seguinte:
                        cpf_candidate = match_linha_seguinte.group(1)
                        # Verifica se não é um número de registro (heurística simples)
                        if "REGISTRO" not in linhas[i].upper() and "RENACH" not in linhas[i].upper():
                            print(f"V20_PARSE_CPF: Encontrado por rótulo 'CPF' na LINHA SEGUINTE ({j}): {cpf_candidate}")
                            return cpf_candidate
            # Se encontrou "CPF" mas não um número formatado próximo, continua.

    # Se não encontrou com rótulo, tenta busca geral por CPF formatado
    match_geral_formatado = re.search(r'\b' + cpf_formatado_regex + r'\b', text)
    if match_geral_formatado:
        # Verifica se não é o número de registro da CNH (que pode ter 11 dígitos mas não é CPF)
        # Esta é uma heurística e pode precisar de ajuste
        cpf_cand = match_geral_formatado.group(0)
        try:
            idx_cand = text.find(cpf_cand)
            texto_anterior_cand = text.upper()[max(0, idx_cand - 40) : idx_cand] # Aumenta janela anterior
            if not ("REGISTRO" in texto_anterior_cand or "RENACH" in texto_anterior_cand or "HABILITAÇÃO" in texto_anterior_cand):
                print(f"V20_PARSE_CPF: Encontrado por regex geral (formato completo, sem rótulos de CNH próximos): {cpf_cand}")
                return cpf_cand
        except: pass

    print("V20_PARSE_CPF: Não encontrado após todas as tentativas.")
    return None

# --- Funções parse_nome, parse_data_nascimento, calcular_idade (da v18/v19) ---
# Cole as suas versões mais recentes e funcionais destas funções aqui, com os prints V20_PARSE_...
def parse_nome(text):
    print("====== V20: ENTROU EM PARSE_NOME (COMPLETO) ======")
    # ... (código da v19)
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
                        print(f"V20_PARSE_NOME: Forte candidato (Fase 1) encontrado abaixo do rótulo '{linha_anterior}': '{linha_limpa}'")

    if melhor_candidato_nome_titular:
        print(f"V20_PARSE_NOME: Nome do titular escolhido (Fase 1): '{melhor_candidato_nome_titular}'")
        return melhor_candidato_nome_titular

    print("V20_PARSE_NOME: Nome do titular não encontrado na Fase 1. Usando heurística geral (Fase 2)...")
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

    print(f"V20_PARSE_NOME: Todos os candidatos potenciais (Fase 2 - debug): {todos_candidatos_potenciais_fase2}")
    if melhor_candidato_geral and max_pontuacao_geral > 0:
        print(f"V20_PARSE_NOME: Melhor candidato (Fase 2): '{melhor_candidato_geral}' com pontuação: {max_pontuacao_geral}")
        return melhor_candidato_geral

    print(f"V20_PARSE_NOME: Nome não encontrado com pontuação suficiente (Fase 2). Melhor pontuação: {max_pontuacao_geral}")
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
        print(f"V20_PARSE_NOME: Nome de fallback (última tentativa, mais longo): {candidatos_fallback[0]}")
        return candidatos_fallback[0]
    print("V20_PARSE_NOME: Nome não extraído.")
    return "Nome não extraído"

def parse_data_nascimento(text):
    print("====== V20: ENTROU EM PARSE_DATA_NASCIMENTO (Refinada) ======")
    # ... (código da v19)
    regex_data = r'\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b'
    linhas = text.split('\n')
    candidatos_data_nasc = []
    datas_a_ignorar = []

    for linha_idx, linha_content in enumerate(linhas):
        linha_upper_content = linha_content.upper().strip()
        if any(rot_ignorar in linha_upper_content for rot_ignorar in ["VALIDADE", "EXPIRY", "EMISSÃO", "EMISSAO", "HABILITAÇÃO"]):
            matches_outras = re.findall(regex_data, linha_content)
            for data_outra in matches_outras:
                print(f"V20_PARSE_DN: Data a IGNORAR (mesma linha do rótulo de validade/emissão/habilitação): {data_outra}")
                datas_a_ignorar.append(data_outra)
            if linha_idx + 1 < len(linhas):
                matches_outras_seguinte = re.findall(regex_data, linhas[linha_idx+1])
                for data_outra_seg in matches_outras_seguinte:
                    print(f"V20_PARSE_DN: Data a IGNORAR (linha seguinte ao rótulo de validade/emissão/habilitação): {data_outra_seg}")
                    datas_a_ignorar.append(data_outra_seg)

    datas_a_ignorar = list(set(datas_a_ignorar))
    print(f"V20_PARSE_DN: Datas de Validade/Emissão/Habilitação identificadas para exclusão: {datas_a_ignorar}")

    for i, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()

        if any(rot_nasc in linha_upper for rot_nasc in ["DATA NASCIMENTO", "DATA NASC.", "DATE OF BIRTH", "NASC."]):
            texto_apos_rotulo = re.sub(r'.*(?:DATA\sNASCIMENTO|DATA\sNASC\.|DATE\sOF\sBIRTH|NASC\.)\s*[:\s-]*', '', linha, flags=re.IGNORECASE).strip()
            match_data_mesma_linha = re.search(regex_data, texto_apos_rotulo)
            if match_data_mesma_linha:
                data_str = match_data_mesma_linha.group(1)
                if data_str not in datas_a_ignorar:
                    print(f"V20_PARSE_DN: Candidato DN (mesma linha, após rótulo): {data_str}")
                    candidatos_data_nasc.append({"data": data_str, "prioridade": 10})

            if (not match_data_mesma_linha or (match_data_mesma_linha and match_data_mesma_linha.group(1) in datas_a_ignorar)) and i + 1 < len(linhas):
                match_data_linha_seguinte = re.search(regex_data, linhas[i+1])
                if match_data_linha_seguinte:
                    data_str = match_data_linha_seguinte.group(1)
                    if data_str not in datas_a_ignorar:
                        print(f"V20_PARSE_DN: Candidato DN (linha seguinte, após rótulo): {data_str}")
                        candidatos_data_nasc.append({"data": data_str, "prioridade": 9})

    if not candidatos_data_nasc:
        print("V20_PARSE_DN: Nenhuma data encontrada perto de rótulos de nascimento. Tentando busca geral.")
        for linha in linhas:
            linha_upper = linha.upper().strip()
            if not any(rot_ignorar in linha_upper for rot_ignorar in ROTULOS_FORTES):
                matches_gerais = re.findall(regex_data, linha)
                for data_str in matches_gerais:
                    if data_str not in datas_a_ignorar and not any(item["data"] == data_str for item in candidatos_data_nasc):
                        print(f"V20_PARSE_DN: Candidato DN (busca geral): {data_str}")
                        candidatos_data_nasc.append({"data": data_str, "prioridade": 5})

    print(f"V20_PARSE_DN: Candidatos Data Nasc (com prioridade, antes de filtrar): {candidatos_data_nasc}")

    candidatos_unicos_dict = {}
    for item in candidatos_data_nasc:
        if item["data"] not in candidatos_unicos_dict or item["prioridade"] > candidatos_unicos_dict[item["data"]]["prioridade"]:
            candidatos_unicos_dict[item["data"]] = item
    candidatos_data_nasc_filtrados = sorted(candidatos_unicos_dict.values(), key=lambda x: x["prioridade"], reverse=True)
    print(f"V20_PARSE_DN: Candidatos Data Nasc (filtrados e ordenados): {candidatos_data_nasc_filtrados}")

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
                        print(f"V20_PARSE_DN: Data de Nascimento VÁLIDA escolhida: {data_nasc_obj.strftime('%d/%m/%Y')}")
                        return data_nasc_obj.strftime('%d/%m/%Y')
            except:
                print(f"V20_PARSE_DN: Erro ao processar/validar candidato de data '{data_str_cand}'")
                continue

        if candidatos_data_nasc_filtrados:
             print(f"V20_PARSE_DN: Nenhuma data 100% validada, retornando o candidato de maior prioridade da lista: {candidatos_data_nasc_filtrados[0]['data']}")
             return candidatos_data_nasc_filtrados[0]['data']

    print("V20_PARSE_DN: Data de Nascimento não encontrada após todas as tentativas.")
    return None

def calcular_idade(data_nascimento_str):
    if not data_nascimento_str: return None
    print(f"V20_CALC_IDADE: Calculando para: {data_nascimento_str}")
    # ... (Use a lógica da v19 para calcular_idade)
    try:
        data_nasc_normalizada = data_nascimento_str.replace('.', '/').replace('-', '/'); formatos_data = ["%d/%m/%Y", "%d/%m/%y"]
        data_nasc_obj = None
        for fmt in formatos_data:
            try: data_nasc_obj = datetime.strptime(data_nasc_normalizada, fmt).date(); break
            except ValueError: continue
        if not data_nasc_obj: print(f"V20_CALC_IDADE_ERRO: Formato não reconhecido: {data_nasc_normalizada}"); return None
        hoje = date.today(); idade = hoje.year - data_nasc_obj.year - ((hoje.month, hoje.day) < (data_nasc_obj.month, data_nasc_obj.day))
        if idade < 0 or idade > 120: print(f"V20_CALC_IDADE_ERRO: Idade implausível ({idade})."); return None
        print(f"V20_CALC_IDADE: Idade calculada: {idade}"); return idade
    except Exception as e: print(f"V20_CALC_IDADE_ERRO: Erro: {e}"); return None

# Removidas as funções parse_rg e parse_cns do fluxo principal de extração
# Se precisar delas no futuro, pode descomentar ou readicionar.
