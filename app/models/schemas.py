
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

class Contato(BaseModel):
    telefone: Optional[str] = Field(None, description="Número de telefone do usuário")
    email: EmailStr = Field(..., description="Endereço de e-mail do usuário")
    linkedIn: Optional[str] = Field(None, description="URL do perfil LinkedIn")
    gitHub: Optional[str] = Field(None, description="URL do perfil GitHub")

class Endereco(BaseModel):
    cidade: str = Field(..., description="Cidade do usuário")
    estado: str = Field(..., description="Estado do usuário")

class Experiencia(BaseModel):
    cargo: str = Field(..., description="Cargo ocupado")
    empresa: str = Field(..., description="Nome da empresa")
    periodo: str = Field(..., description="Período de trabalho (ex: 'Jan 2020 - Dez 2022')")
    descricao: str = Field(..., description="Descrição das responsabilidades e conquistas")

class Projeto(BaseModel):
    titulo: str = Field(..., description="Título do projeto")
    tecnologias: List[str] = Field(default_factory=list, description="Lista de tecnologias usadas")
    descricao: str = Field(..., description="Descrição do projeto")

class Educacao(BaseModel):
    curso: str = Field(..., description="Nome do curso")
    instituicao: str = Field(..., description="Nome da instituição de ensino")
    periodo: str = Field(..., description="Período do curso (ex: '2018 - 2022' ou 'Concluído em 2022')")

class DadosUsuario(BaseModel):
    nomeCompleto: str = Field(..., description="Nome completo do usuário")
    endereco: Endereco
    contato: Contato
    experiencia: List[Experiencia] = Field(default_factory=list)
    projetos: List[Projeto] = Field(default_factory=list)
    educacao: List[Educacao] = Field(default_factory=list)
    # Adicione outros campos se necessário (ex: Habilidades, Idiomas)

class VagaDescricaoInput(BaseModel):
    descricao_vaga: str = Field(..., description="Descrição completa da vaga de emprego")

class VagaInfoOutput(BaseModel):
    # Os campos exatos podem variar dependendo do que a IA retorna
    # Defina os campos esperados com base na função agente_vaga
    nomeEmpresa: Optional[str] = None
    nomenclaturaCargo: Optional[str] = None
    nivelExperiencia: Optional[str] = None
    skillsTecnicas: Optional[List[str]] = None
    softSkills: Optional[List[str]] = None
    responsabilidadesDaVaga: Optional[List[str]] = None
    tomDaVaga: Optional[str] = None
    palavrasChave: Optional[List[str]] = None
    # Adicione um campo para o caso de a IA não retornar um JSON válido
    raw_analysis: Optional[Dict[str, Any]] = Field(None, description="Análise bruta caso o parse JSON falhe")
    error: Optional[str] = Field(None, description="Mensagem de erro se a análise falhar")


class GerarCVInput(BaseModel):
    dados_usuario: DadosUsuario = Field(..., description="Informações completas do perfil do usuário")
    vaga_info: Optional[VagaInfoOutput] = Field(None, description="Informações analisadas da vaga (opcional, pode usar descricao_vaga)")
    descricao_vaga: Optional[str] = Field(None, description="Descrição da vaga (usado se vaga_info não for fornecido)")
