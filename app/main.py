from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
import json
from typing import Annotated

# Importações dos módulos locais
from .models.schemas import (
    DadosUsuario, VagaDescricaoInput, VagaInfoOutput, GerarCVInput
)
from .core.ai import analisar_vaga_ia, gerar_texto_cv_ia
from .services.cv_generator import criar_pdf_ats_formatado

# Descrição da API para Swagger
description = """
API Geradora de Currículos ATS com IA 🚀

Esta API permite:
1.  Analisar uma descrição de vaga para extrair informações chave.
2.  Gerar um currículo em formato PDF otimizado para ATS, combinando dados do usuário e informações da vaga.

Utiliza Google Gemini para processamento de linguagem natural e ReportLab para geração de PDF.
"""

app = FastAPI(
    title="Gerador de Currículo ATS API",
    description=description,
    version="1.0.0",
    contact={
        "name": "Jean Oliveira",
        "email": "jeanolivera123@gmail.com",
    },
)


# --- Endpoints da API ---

@app.post(
    "/analisar-vaga",
    response_model=VagaInfoOutput,
    tags=["Análise de Vaga"],
    summary="Extrai informações chave de uma descrição de vaga",
    description="Recebe a descrição de uma vaga e utiliza IA para extrair dados estruturados como nome da empresa, cargo, skills, etc.",
)
async def analisar_vaga_endpoint(
    vaga_input: VagaDescricaoInput = Body(..., embed=True, description="Objeto contendo a descrição da vaga a ser analisada.")
):
    """
    Endpoint para analisar a descrição de uma vaga.

    - **descricao_vaga**: O texto completo da descrição da vaga.
    """
    if not vaga_input.descricao_vaga.strip():
        raise HTTPException(status_code=400, detail="A descrição da vaga não pode estar vazia.")

    try:
        resultado_analise = await analisar_vaga_ia(vaga_input.descricao_vaga)

        # Se a IA retornou um erro estruturado
        if isinstance(resultado_analise, dict) and resultado_analise.get("error"):
             # Tentar parsear como VagaInfoOutput mesmo com erro para retornar estrutura esperada
             return VagaInfoOutput(
                 error=resultado_analise.get("error"),
                 raw_analysis=resultado_analise # Inclui raw_response se existir
             )

        # Tentar validar o resultado com o modelo Pydantic
        try:
            # Passa o dicionário diretamente
            vaga_info = VagaInfoOutput(**resultado_analise)
            return vaga_info
        except ValidationError as e:
            print(f"Erro de validação Pydantic após análise IA: {e}")
            # Retorna a estrutura esperada, mas com erro e os dados brutos
            return VagaInfoOutput(
                 error=f"IA retornou dados em formato inesperado: {e}",
                 raw_analysis=resultado_analise
             )

    except Exception as e:
        # Logar o erro 'e' aqui
        print(f"Erro interno ao analisar vaga: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao analisar a vaga: {str(e)}")


@app.post(
    "/gerar-curriculo-pdf",
    tags=["Geração de Currículo"],
    summary="Gera um currículo em PDF otimizado para ATS",
    description="Recebe os dados do usuário e a descrição da vaga (ou análise prévia), gera o texto do CV com IA e o converte para PDF.",
    response_class=StreamingResponse, # Indica que a resposta é um stream (para o PDF)
    # dependencies=[Depends(check_api_key)], # Verifica a chave
    responses={
        200: {
            "description": "Currículo em PDF gerado com sucesso.",
            "content": {"application/pdf": {}},
        },
        400: {"description": "Dados de entrada inválidos."},
        500: {"description": "Erro interno do servidor durante a geração."},
    }
)
async def gerar_curriculo_pdf_endpoint(
     # Usando Annotated para melhor documentação no Swagger
    payload: Annotated[GerarCVInput, Body(
        description="Dados do usuário e informações da vaga para gerar o currículo.",
        examples=[ # Exemplo para Swagger UI
            {
                "dados_usuario": {
                    "nomeCompleto": "João da Silva",
                    "endereco": {"cidade": "São Paulo", "estado": "SP"},
                    "contato": {
                        "telefone": "11999998888",
                        "email": "joao.silva@email.com",
                        "linkedIn": "https://linkedin.com/in/joaosilva",
                         "gitHub": "https://github.com/joaosilva"
                    },
                    "experiencia": [
                        {
                            "cargo": "Desenvolvedor Full Stack",
                            "empresa": "Tech Solutions",
                            "periodo": "Jan 2020 - Atual",
                            "descricao": "Desenvolvimento e manutenção de aplicações web usando React, Node.js e PostgreSQL. Liderança técnica em projetos."
                        }
                    ],
                    "projetos": [
                        {
                            "titulo": "Sistema de E-commerce",
                            "tecnologias": ["React", "Node.js", "MongoDB"],
                            "descricao": "Plataforma completa de e-commerce com carrinho, pagamento e área administrativa."
                        }
                    ],
                    "educacao": [
                        {
                            "curso": "Ciência da Computação",
                            "instituicao": "Universidade Exemplo",
                            "periodo": "2016 - 2020"
                        }
                    ]
                },
                "descricao_vaga": "Procuramos Desenvolvedor Python Pleno com experiência em FastAPI e AWS..."
            }
        ]
    )]
):
    """
    Endpoint para gerar o currículo em formato PDF.

    Forneça os `dados_usuario` completos e a `descricao_vaga`.
    Opcionalmente, pode fornecer `vaga_info` (resultado de `/analisar-vaga`) em vez de `descricao_vaga`.
    """
    dados_usuario_dict = payload.dados_usuario.model_dump() # Converte Pydantic model para dict

    if not payload.descricao_vaga and not payload.vaga_info:
         raise HTTPException(status_code=400, detail="É necessário fornecer 'descricao_vaga' ou 'vaga_info'.")

    vaga_info_dict = {}
    try:
        # Se a informação da vaga não foi fornecida pré-analisada, analisa agora
        if payload.descricao_vaga and not payload.vaga_info:
            print("Analisando descrição da vaga para gerar CV...")
            vaga_info_dict = await analisar_vaga_ia(payload.descricao_vaga)
             # Verifica se a análise teve erro
            if isinstance(vaga_info_dict, dict) and vaga_info_dict.get("error"):
                 raise HTTPException(status_code=400, detail=f"Erro ao analisar a vaga antes de gerar o CV: {vaga_info_dict['error']}")
        elif payload.vaga_info:
            print("Usando vaga_info pré-fornecido para gerar CV...")
            vaga_info_dict = payload.vaga_info.model_dump(exclude_none=True) # Converte Pydantic para dict
        else:
             # Caso redundante devido à validação anterior, mas para segurança
             raise HTTPException(status_code=400, detail="Faltam informações da vaga.")


        # 1. Gerar o texto do CV usando a IA
        print("Gerando texto do CV com IA...")
        texto_cv = await gerar_texto_cv_ia(dados_usuario_dict, vaga_info_dict)

        if not texto_cv or not texto_cv.strip():
             raise HTTPException(status_code=500, detail="A IA não retornou conteúdo para o currículo.")

        # 2. Criar o PDF a partir do texto
        print("Gerando arquivo PDF...")
        nome_candidato = dados_usuario_dict.get("nomeCompleto", "Candidato")
        pdf_buffer = criar_pdf_ats_formatado(texto_cv, nome_candidato)

        # 3. Retornar o PDF como um stream
        filename = f"CV_{nome_candidato.replace(' ', '_')}_ATS.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException as http_exc:
        # Re-lança exceções HTTP que já foram tratadas (como erros 400 ou da análise)
        raise http_exc
    except Exception as e:
        # Logar o erro 'e' aqui
        print(f"Erro interno ao gerar currículo PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao gerar o currículo: {str(e)}")


# --- Ponto de Entrada para Uvicorn (se executar `python app/main.py`) ---
# Normalmente, você usará `uvicorn app.main:app --reload` no terminal
if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor Uvicorn para desenvolvimento...")
    print("Acesse a documentação interativa em http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
