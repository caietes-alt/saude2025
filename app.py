# app.py
import streamlit as st
import pandas as pd
import os, io, re, datetime
import slugify from slugify 
import psycopg2

st.set_page_config(page_title="Processo Seletivo - Saúde", page_icon="🩺", layout="centered")
st.title("Formulário de Inscrição – Processo Seletivo (Saúde) - Município de Ilhéus")

st.markdown("""
**Instruções**  
- Preencha **todos** os campos obrigatórios.  
- Anexe os **PDFs** solicitados (alguns podem ser um único PDF consolidado).  
- Seus dados serão usados **exclusivamente** neste processo seletivo.
""")

# --------------------------
# Catálogos (cargos / locais)
# --------------------------
cargos_superior = [
    "Enfermeiro Generalista","Enfermeiro Emergencista","Enfermeiro Saúde Mental","Psicólogo",
    "Biomédico (30h)","Biomédico (40h)","Médico Veterinário","Nutricionista","Assistente Social",
    "Fisioterapeuta","Educador Físico","Pedagogo","Terapeuta Ocupacional","Fonoaudiólogo",
    "Farmacêutico","Engenheiro Civil","Gerente de Unidade"
]
cargos_tecnico = [
    "Técnico de Enfermagem","Técnico em Análise Clínica","Técnico de Saúde Bucal",
    "Técnico em Radiologia"
]
cargos_medio = [
    "TARM","Auxiliar Administrativo","Auxiliar Veterinário","Artesão Oficineiro",
    "Intérprete de Libras","Condutor de Ambulância","Condutor de Motolância",
    "Rádio Operador (TARM)","Auxiliar de Farmácia","Almoxarife"
]
cargos_fundamental = [
    "Auxiliar de Serviços Gerais","Motorista","Vaqueiro"
]
cargos_all = (["— Selecione —"] + cargos_superior + cargos_tecnico + cargos_medio + cargos_fundamental)

# --------------------------
# Formulário
# --------------------------
with st.form("inscricao_form"):
    st.header("Informações Pessoais")
    nome = st.text_input("Nome completo *")
    data_nasc = st.date_input("Data de nascimento *")
    rg = st.text_input("RG (com órgão emissor) *")
    cpf = st.text_input("CPF *")
    endereco = st.text_input("Endereço completo *")
    telefone = st.text_input("Telefone (WhatsApp) *")
    email = st.text_input("E-mail *")

    st.header("Declarações (marque se aplicável)")
    pcd = st.radio("Pessoa com deficiência (PCD)? *", ["Não","Sim"], horizontal=True)
    indigena = st.radio("Indígena? *", ["Não","Sim"], horizontal=True)

    st.header("Informações sobre o Cargo e Vaga")
    cargo = st.selectbox("Cargo pretendido *", cargos_all, index=0)
    localidade = st.text_input("Unidade/Localidade de interesse (se aplicável)")
    experiencia = st.radio("Possui experiência na área? *", ["Não","Sim"], horizontal=True)

    st.header("Documentação Obrigatória (PDF)")
    st.caption("Quando indicado “em arquivo único”, consolide os comprovantes em um único PDF.")

    doc_rg = st.file_uploader("RG (frente e verso) – PDF *", type=["pdf"])
    doc_cpf = st.file_uploader("CPF – PDF *", type=["pdf"])
    doc_militar = st.file_uploader("Quitação militar (apenas sexo masculino, se aplicável) – PDF", type=["pdf"])
    doc_resid = st.file_uploader("Comprovante de residência (até 3 meses) – PDF *", type=["pdf"])
    doc_titulo = st.file_uploader("Título de eleitor + quitação eleitoral – PDF *", type=["pdf"])
    doc_ctps = st.file_uploader("CTPS – PDF *", type=["pdf"])
    doc_pis = st.file_uploader("Documento com nº PIS/PASEP – PDF *", type=["pdf"])

    doc_curriculo = st.file_uploader("Currículo atualizado **comprobatório** (arquivo único) – PDF *", type=["pdf"])
    doc_escolaridade = st.file_uploader("Escolaridade exigida (médio/técnico/fundamental) (arquivo único) – PDF (se aplicável)", type=["pdf"])
    doc_diploma_sup = st.file_uploader("Diploma/Certificado de Curso Superior – PDF (se aplicável)", type=["pdf"])
    doc_pos = st.file_uploader("Pós-graduação na área (se houver) – PDF", type=["pdf"])
    doc_exper = st.file_uploader("Comprovação de tempo de experiência – PDF", type=["pdf"])

    doc_laudo_pcd = None
    if pcd == "Sim":
        doc_laudo_pcd = st.file_uploader("Laudo médico (CID-10), emitido nos últimos 6 meses – PDF *", type=["pdf"])

    doc_funai = None
    if indigena == "Sim":
        doc_funai = st.file_uploader("Declaração da FUNAI e/ou do Cacique do povo – PDF *", type=["pdf"])

    doc_antecedentes = st.file_uploader("Atestados de Antecedentes Criminais (TJ Estadual/Federal) e SSP/BA – PDF *", type=["pdf"])

    st.header("Termos")
    declara = st.checkbox("Declaro que as informações são verdadeiras. *")
    autoriza = st.checkbox("Autorizo o uso dos dados pessoais neste processo seletivo. *")

    enviado = st.form_submit_button("Enviar inscrição")

# --------------------------
# Validação e salvamento
# --------------------------
def apenas_digitos(s):
    return re.sub(r"\D", "", s or "")

def validar_pdf_up(file, obrigatorio=False):
    if obrigatorio and file is None:
        return False, "Documento obrigatório ausente."
    if file is not None and file.type != "application/pdf":
        return False, "Arquivo deve ser PDF."
    return True, None

# Função para conectar e criar a tabela no banco de dados
def conectar_db_e_criar_tabela():
    try:
        conn = psycopg2.connect(**st.secrets["postgres"])
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inscricoes (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                nome VARCHAR(255),
                data_nascimento DATE,
                rg VARCHAR(255),
                cpf VARCHAR(11) UNIQUE,
                endereco TEXT,
                telefone VARCHAR(255),
                email VARCHAR(255),
                pcd VARCHAR(5),
                indigena VARCHAR(5),
                cargo VARCHAR(255),
                localidade VARCHAR(255),
                experiencia VARCHAR(5),
                declara BOOLEAN,
                autoriza BOOLEAN
            );
        """)
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ou criar a tabela no banco de dados: {e}")
        return None

if enviado:
    erros = []

    # Campos
    cpf_limpo = apenas_digitos(cpf)
    
    obrigatorios = {
        "Nome completo": bool(nome.strip()),
        "CPF": bool(cpf_limpo) and len(cpf_limpo) == 11,
        "RG": bool(rg.strip()),
        "Endereço": bool(endereco.strip()),
        "Telefone": bool(telefone.strip()),
        "E-mail": bool(email.strip()),
        "Cargo": (cargo != "— Selecione —"),
        "Declaração de veracidade": declara,
        "Autorização de uso dos dados": autoriza
    }
    for k,v in obrigatorios.items():
        if not v: erros.append(f"{k} é obrigatório.")

    # Docs obrigatórios
    checks = [
        validar_pdf_up(doc_rg, True),
        validar_pdf_up(doc_cpf, True),
        validar_pdf_up(doc_resid, True),
        validar_pdf_up(doc_titulo, True),
        validar_pdf_up(doc_ctps, True),
        validar_pdf_up(doc_pis, True),
        validar_pdf_up(doc_curriculo, True),
        validar_pdf_up(doc_antecedentes, True),
    ]
    for ok,msg in checks:
        if not ok: erros.append(msg)
    
    # Docs condicionados ao cargo
    if cargo in cargos_superior:
        ok, msg = validar_pdf_up(doc_diploma_sup, True)
        if not ok: erros.append("Diploma/Certificado de Curso Superior é obrigatório para cargos de nível superior.")
    
    elif cargo in cargos_tecnico or cargo in cargos_medio or cargo in cargos_fundamental:
        ok, msg = validar_pdf_up(doc_escolaridade, True)
        if not ok: erros.append("Escolaridade exigida é obrigatória para este cargo.")

    # Docs condicionados a declarações
    if pcd == "Sim":
        ok,msg = validar_pdf_up(doc_laudo_pcd, True)
        if not ok: erros.append("Laudo PCD obrigatório.")

    if indigena == "Sim":
        ok,msg = validar_pdf_up(doc_funai, True)
        if not ok: erros.append("Declaração FUNAI/Cacique obrigatória.")

    if erros:
        st.error("⚠️ Corrija os itens abaixo antes de enviar:")
        for e in sorted(set(erros)):
            st.write("-", e)
    else:
        # Tenta salvar no banco de dados
        try:
            conn = conectar_db_e_criar_tabela()
            if conn:
                cursor = conn.cursor()
                # Insere dados na tabela
                sql = """
                    INSERT INTO inscricoes (
                        timestamp, nome, data_nascimento, rg, cpf, endereco, telefone, email,
                        pcd, indigena, cargo, localidade, experiencia, declara, autoriza
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                dados_inscricao = (
                    datetime.datetime.now(), nome, data_nasc, rg, cpf_limpo, endereco, telefone, email,
                    pcd, indigena, cargo, localidade, experiencia, declara, autoriza
                )
                cursor.execute(sql, dados_inscricao)
                conn.commit()
                st.success("✅ Dados salvos com sucesso no banco de dados!")
                cursor.close()
                conn.close()

        except psycopg2.errors.UniqueViolation:
            st.error("⚠️ Erro: Já existe uma inscrição com este CPF. Por favor, verifique os dados.")
            conn.rollback() # Desfaz a transação em caso de erro
        except Exception as e:
            st.error(f"⚠️ Erro ao salvar os dados no banco: {e}")

        # Salva arquivos localmente (como no código original)
        cpf_key = apenas_digitos(cpf)
        base_dir = os.path.join("inscricoes", cpf_key)
        os.makedirs(base_dir, exist_ok=True)

        def salvar(pdf, nome_arquivo):
            if pdf is None: return None
            path = os.path.join(base_dir, nome_arquivo)
            with open(path, "wb") as f: f.write(pdf.getbuffer())
            return path

        saved = {
            "rg": salvar(doc_rg, "RG.pdf"),
            "cpf": salvar(doc_cpf, "CPF.pdf"),
            "resid": salvar(doc_resid, "Comprovante_Residencia.pdf"),
            "titulo": salvar(doc_titulo, "Titulo_Eleitor_Quitacao.pdf"),
            "ctps": salvar(doc_ctps, "CTPS.pdf"),
            "pis": salvar(doc_pis, "PIS_PASEP.pdf"),
            "curriculo": salvar(doc_curriculo, "Curriculo_Comprovado.pdf"),
            "escolaridade": salvar(doc_escolaridade, "Escolaridade.pdf") if doc_escolaridade else None,
            "diploma_sup": salvar(doc_diploma_sup, "Diploma_Superior.pdf") if doc_diploma_sup else None,
            "pos": salvar(doc_pos, "Pos_Graduacao.pdf") if doc_pos else None,
            "exper": salvar(doc_exper, "Experiencia.pdf") if doc_exper else None,
            "militar": salvar(doc_militar, "Quitacao_Militar.pdf") if doc_militar else None,
            "laudo_pcd": salvar(doc_laudo_pcd, "Laudo_PCD.pdf") if doc_laudo_pcd else None,
            "funai": salvar(doc_funai, "Declaracao_FUNAI_Cacique.pdf") if doc_funai else None,
            "antecedentes": salvar(doc_antecedentes, "Antecedentes_Criminais.pdf"),
        }
        
        protocolo = f"ILH-Saude-{cpf_key}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.success("✅ Inscrição enviada com sucesso!")
        st.info(f"Protocolo: **{protocolo}**")
        st.write("Guarde seu protocolo. Você receberá comunicações pelo e-mail/telefone informados.")

