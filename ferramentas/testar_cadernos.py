"""Roda os cadernos de uma pasta e lista erros que NÃO são de conexão com o modelo.

Uso offline (sem chave e sem internet):
  set OPENROUTER_API_KEY=teste & set IA_BASE_URL=http://127.0.0.1:9/v1
  .venv\\Scripts\\python.exe ferramentas\\testar_cadernos.py resolvidos
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ERROS_DE_REDE = ("APIConnectionError", "AuthenticationError", "APITimeoutError")
pasta = Path(sys.argv[1]).resolve()
total_rede = 0
for f in sorted(pasta.glob("cap*.ipynb")):
    nb = nbformat.read(f, as_version=4)
    NotebookClient(nb, timeout=120, kernel_name="python3", allow_errors=True,
                   resources={"metadata": {"path": str(pasta)}}).execute()
    rede, outros = 0, []
    for i, c in enumerate(nb.cells):
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                if o["ename"] in ERROS_DE_REDE:
                    rede += 1
                else:
                    outros.append(f"   célula {i}: {o['ename']}: {o['evalue'][:150]}")
    total_rede += rede
    print(f"{f.name}: {len(outros)} erro(s) de código, {rede} célula(s) dependem do modelo")
    print("\n".join(outros)) if outros else None
print("Total de células que só rodam com a chave:", total_rede)
