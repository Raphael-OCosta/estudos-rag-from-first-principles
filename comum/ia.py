"""Atalhos para os exercícios do livro AI Engineering (Chip Huyen).

Os cadernos da pasta `praticar` fazem `from ia import *` na célula de Preparação.
Você não precisa mexer neste arquivo, mas pode lê-lo: ele também é um exemplo de
código de "engenharia de IA" de verdade.

O que ele oferece:
    cliente          -> cliente da API (compatível com OpenAI) apontando para o OpenRouter
    MODELO           -> modelo padrão dos exercícios (barato e rápido)
    perguntar(...)   -> manda um prompt e devolve só o texto da resposta
    conversar(...)   -> manda uma lista de mensagens (sistema/usuário/assistente)
    embeddings(...)  -> transforma textos em vetores (cap. 6, RAG)
    contar_tokens(..) -> quantos tokens um texto tem
    gasto()          -> quanto você já gastou nesta sessão (em dólares)
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
from pathlib import Path

import numpy as np
from openai import OpenAI

__all__ = ["cliente", "MODELO", "MODELO_FORTE", "MODELO_EMBEDDING", "perguntar",
           "conversar", "embeddings", "contar_tokens", "gasto", "similaridade"]

MODELO = "openai/gpt-4o-mini"          # padrão: barato e rápido
MODELO_FORTE = "openai/gpt-4o"         # para comparar ou usar como "juiz" (cap. 3)
MODELO_EMBEDDING = "openai/text-embedding-3-small"

_ARQ_CHAVE = Path.home() / ".secrets" / "openrouter.dpapi"
_gasto = {"usd": 0.0, "chamadas": 0, "tokens_in": 0, "tokens_out": 0}


def _ler_chave() -> str:
    """Lê a chave do OpenRouter: variável OPENROUTER_API_KEY ou o arquivo cifrado (DPAPI)."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    if not _ARQ_CHAVE.exists():
        raise RuntimeError(
            "Chave do OpenRouter não encontrada. Rode no PowerShell:\n"
            "  & \"$HOME\\.claude\\skills\\jev\\set-key.ps1\""
        )
    # Arquivo gravado por ConvertFrom-SecureString: hex de um blob DPAPI com o texto em UTF-16.
    blob = bytes.fromhex(_ARQ_CHAVE.read_text(encoding="ascii").strip())

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    entrada = DATA_BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob, len(blob)), ctypes.POINTER(ctypes.c_char)))
    saida = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)):
        raise RuntimeError("Não consegui decifrar a chave (ela só abre no seu usuário do Windows).")
    try:
        return ctypes.string_at(saida.pbData, saida.cbData).decode("utf-16-le")
    finally:
        ctypes.windll.kernel32.LocalFree(saida.pbData)


cliente = OpenAI(base_url=os.environ.get("IA_BASE_URL", "https://openrouter.ai/api/v1"), api_key=_ler_chave())


def _registrar(uso) -> None:
    if uso is None:
        return
    _gasto["chamadas"] += 1
    _gasto["tokens_in"] += getattr(uso, "prompt_tokens", 0) or 0
    _gasto["tokens_out"] += getattr(uso, "completion_tokens", 0) or 0
    custo = getattr(uso, "cost", None)
    if custo is None and isinstance(getattr(uso, "model_extra", None), dict):
        custo = uso.model_extra.get("cost")
    _gasto["usd"] += float(custo or 0)


def conversar(mensagens: list[dict], modelo: str = MODELO, **opcoes):
    """Chamada completa (devolve o objeto de resposta inteiro).

    mensagens: [{"role": "system"|"user"|"assistant", "content": "..."}]
    opcoes: temperature, top_p, max_tokens, logprobs, top_logprobs, response_format, ...
    """
    resposta = cliente.chat.completions.create(model=modelo, messages=mensagens, **opcoes)
    _registrar(resposta.usage)
    return resposta


def perguntar(prompt: str, sistema: str | None = None, modelo: str = MODELO, **opcoes) -> str:
    """Manda um prompt e devolve só o texto da resposta."""
    mensagens = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": prompt}]
    return conversar(mensagens, modelo=modelo, **opcoes).choices[0].message.content


def embeddings(textos: list[str] | str, modelo: str = MODELO_EMBEDDING) -> np.ndarray:
    """Vetores dos textos (uma linha por texto)."""
    if isinstance(textos, str):
        textos = [textos]
    resposta = cliente.embeddings.create(model=modelo, input=textos)
    _registrar(getattr(resposta, "usage", None))
    return np.array([item.embedding for item in resposta.data])


def similaridade(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Similaridade de cosseno entre vetores (1 = mesmo sentido, 0 = sem relação)."""
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return a @ b.T


def contar_tokens(texto: str, codificacao: str = "o200k_base") -> int:
    """Quantos tokens o texto tem (codificação dos modelos GPT-4o)."""
    import tiktoken
    return len(tiktoken.get_encoding(codificacao).encode(texto))


def gasto() -> str:
    """Resumo do que foi gasto nesta sessão do notebook."""
    g = _gasto
    return (f"{g['chamadas']} chamadas · {g['tokens_in']} tokens de entrada · "
            f"{g['tokens_out']} de saída · US$ {g['usd']:.5f}")
