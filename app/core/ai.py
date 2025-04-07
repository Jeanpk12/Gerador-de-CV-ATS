import google.generativeai as genai
import re
import json
from dotenv import load_dotenv
import os


load_dotenv()

API_KEY = os.getenv("API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")


# Configurar o cliente Gemini (faça isso uma vez)
try:
    if API_KEY:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    else:
        model = None
        print("Modelo GenerativeAI não inicializado devido à falta da API Key.")
except Exception as e:
    print(f"Erro ao configurar a API Gemini: {e}")
    model = None

def limpar_codigo_markdown(resposta: str) -> str:
    """Remove blocos de código Markdown do início e fim da string."""
    # Remove ```json ... ``` ou ``` ... ```
    cleaned = re.sub(r"^```(?:[a-zA-Z0-9]+)?\n?|\n?```$", "", resposta.strip(), flags=re.MULTILINE)
    return cleaned.strip()


async def chamar_agente_ia(prompt: str, temperatura: float = 0.6, max_tokens: int = 8000) -> str:
    """Chama a API Generative AI de forma assíncrona."""
    if not model:
        raise RuntimeError("Modelo GenerativeAI não foi inicializado corretamente. Verifique a API Key.")

    try:
        response = await model.generate_content_async( # Usar versão async
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                max_output_tokens=max_tokens,
                temperature=temperatura
            )
        )
        # Adicionar tratamento de erro para safety ratings se necessário
        if not response.parts:
             if response.prompt_feedback.block_reason:
                 raise ValueError(f"Geração bloqueada: {response.prompt_feedback.block_reason.name} - {response.prompt_feedback.block_reason_message}")
             else:
                 raise ValueError("Resposta da IA vazia ou inválida.")

        resposta_texto = limpar_codigo_markdown(response.text)
        return resposta_texto
    except Exception as e:
        # Logar o erro aqui seria bom
        print(f"Erro ao chamar a API Gemini: {e}")
        raise  # Re-lança a exceção para ser tratada no endpoint

async def analisar_vaga_ia(descricao_vaga: str) -> dict:
    """Usa a IA para extrair informações da descrição da vaga."""
    prompt = (
        "Você é um assistente especializado em análise de vagas. Extraia as seguintes informações da descrição da vaga fornecida: \n"
        "- nomeEmpresa (string)\n"
        "- nomenclaturaCargo (string)\n"
        "- nivelExperiencia (string, ex: Júnior, Pleno, Sênior, Especialista)\n"
        "- skillsTecnicas (lista de strings)\n"
        "- softSkills (lista de strings)\n"
        "- responsabilidadesDaVaga (lista de strings)\n"
        "- tomDaVaga (string, ex: Formal, Informal, Corporativo)\n"
        "- palavrasChave (lista de strings)\n\n"
        "Retorne os dados estritamente como um objeto JSON válido, sem nenhum texto adicional antes ou depois.\n\n"
        f"Descrição da vaga:\n{descricao_vaga}"
    )
    resposta_bruta = await chamar_agente_ia(prompt, temperatura=0.3, max_tokens=2048) # Temperatura baixa para mais objetividade

    try:
        # Tenta limpar especificamente para JSON antes de decodificar
        json_match = re.search(r'\{.*\}', resposta_bruta, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # Se não encontrar um JSON claro, tenta decodificar a resposta limpa
             return json.loads(resposta_bruta) # Pode falhar se não for JSON
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da análise da vaga: {e}")
        print(f"Resposta bruta recebida: {resposta_bruta}")
        # Retorna um dicionário indicando o erro e a resposta bruta
        return {"error": f"Falha ao decodificar JSON: {e}", "raw_response": resposta_bruta}
    except Exception as e:
        print(f"Erro inesperado na análise da vaga: {e}")
        return {"error": f"Erro inesperado: {e}", "raw_response": resposta_bruta}


async def gerar_texto_cv_ia(dados_usuario: dict, vaga_info: dict) -> str:
    """Usa a IA para gerar o texto do currículo adaptado à vaga."""
    if not dados_usuario or not vaga_info:
        raise ValueError("Os dados do usuário e da vaga são necessários para gerar o CV.")

    # Convertendo os dicionários Pydantic para JSON strings formatadas para o prompt
    dados_usuario_json = json.dumps(dados_usuario, indent=2, ensure_ascii=False)
    vaga_info_json = json.dumps(vaga_info, indent=2, ensure_ascii=False)

    prompt = f"""
    Gere um currículo em texto puro e formatado para ATS (sem tabelas, colunas múltiplas ou imagens), baseado nas informações do usuário abaixo e adaptado para a vaga fornecida. Use uma estrutura profissional com seções como Contato, Endereço, Objetivo, Experiência Profissional, Projetos, Formação Acadêmica e Habilidades, tudo de acordo com os dados do usuário.
    Certifique-se de utilizar os dados reais fornecidos pelo usuário (telefone, email, LinkedIn etc.) no currículo, sem substituí-los por placeholders genéricos como [Seu Email].
    O objetivo deve ser conciso e direcionado para a vaga, evitando textos genéricos.
    Na seção de Habilidades, liste as habilidades técnicas e interpessoais relevantes do usuário, priorizando aquelas mencionadas na descrição da vaga. Se a vaga pedir tecnologias que o usuário domina (conforme a lista fixa abaixo), liste-as. Se pedir outras, mencione 'Interesse em aprender [tecnologia]'.

    Tecnologias que o usuário domina: Javascript, HTML, CSS, Bootstrap, React, Vue.js, Node.js, Python, Flask, Streamlit, Java, Spring Boot, SQL. As demais tecnologias mencionadas na vaga deve constar como: Interesse em aprender [tecnologia].

    Dados do usuário:
    {dados_usuario_json}

    Informações da vaga:
    {vaga_info_json}

    Retorne apenas o texto completo do currículo, começando pelo nome do candidato, formatado de forma clara e profissional, sem explicações adicionais, introduções, despedidas ou blocos de código Markdown. Siga a estrutura padrão de currículos ATS.
    """
    # Usar temperatura um pouco maior para criatividade na escrita, mas ainda contida
    texto_cv = await chamar_agente_ia(prompt, temperatura=0.7, max_tokens=4096)
    return texto_cv
