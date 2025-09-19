# Processo Seletivo (Saúde) - Ilhéus

Esta é uma aplicação web construída com **Streamlit** para gerenciar o formulário de inscrição de um processo seletivo na área da saúde. O sistema coleta informações de candidatos, valida dados e documentos, e armazena as inscrições de forma segura.

## Funcionalidades
- **Formulário de Inscrição:** Interface web para preenchimento de dados pessoais e de cargo.
- **Validação de Dados:** Verificação de campos obrigatórios e formato de CPF.
- **Anexo de Documentos:** Upload de arquivos PDF com validação de tipo e obrigatoriedade.
- **Armazenamento de Dados:** Salva os dados do formulário em um banco de dados **PostgreSQL**.
- **Organização de Arquivos:** Os documentos anexados são salvos em uma estrutura de pastas organizada por CPF.

## Instalação e Execução
### Pré-requisitos
Certifique-se de ter o Python instalado.

### 1. Clonar o repositório
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd <nome_do_seu_repositorio>
