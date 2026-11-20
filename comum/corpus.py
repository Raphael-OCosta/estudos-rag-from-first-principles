"""Base de conhecimento inventada (Biblioteca Municipal Aurora), usada nos exercícios de RAG.

Cada documento tem id, título, data de atualização e texto. Nada aqui é real: dá para mandar ao modelo sem risco.
"""

DOCS = [
    {"id": "d01", "titulo": "Horário de funcionamento", "data": "2025-01-10",
     "texto": "A Biblioteca Municipal Aurora abre de terça a sábado, das 9h às 20h. Aos domingos funciona das 10h às 14h. "
              "Às segundas-feiras fica fechada para manutenção do acervo."},
    {"id": "d02", "titulo": "Cadastro de leitores", "data": "2024-11-02",
     "texto": "Para fazer o cartão de leitor é preciso apresentar documento com foto e comprovante de endereço. "
              "Menores de 16 anos precisam de autorização de um responsável. O cartão é gratuito e vale por dois anos."},
    {"id": "d03", "titulo": "Empréstimo de livros", "data": "2025-03-15",
     "texto": "Cada leitor pode emprestar até 5 livros por vez, pelo prazo de 14 dias. A renovação pode ser feita duas vezes "
              "pelo site, desde que o livro não esteja reservado por outra pessoa."},
    {"id": "d04", "titulo": "Multas por atraso", "data": "2025-03-15",
     "texto": "A devolução com atraso gera multa de R$ 1,00 por dia e por livro. Leitores com multa acima de R$ 20,00 ficam "
              "bloqueados para novos empréstimos até a quitação."},
    {"id": "d05", "titulo": "Multas por atraso (versão antiga)", "data": "2022-06-01",
     "texto": "A devolução com atraso gera multa de R$ 0,50 por dia e por livro. Não há bloqueio por valor de multa."},
    {"id": "d06", "titulo": "Sala de estudos", "data": "2024-08-20",
     "texto": "A sala de estudos tem 40 lugares, tomadas em todas as mesas e Wi-Fi gratuito. A reserva de mesa é feita no "
              "balcão e vale por 3 horas. É proibido comer na sala, mas garrafas de água são permitidas."},
    {"id": "d07", "titulo": "Acervo digital", "data": "2025-02-01",
     "texto": "Leitores cadastrados têm acesso a mais de 12 mil e-books pelo aplicativo Aurora Digital. O empréstimo digital "
              "dura 21 dias e o livro some do aplicativo automaticamente no fim do prazo, sem multa."},
    {"id": "d08", "titulo": "Eventos e clube de leitura", "data": "2025-04-05",
     "texto": "O clube de leitura se reúne na primeira quinta-feira de cada mês, às 19h. A participação é gratuita e as "
              "inscrições abrem dez dias antes no site. Também há contação de histórias para crianças aos sábados às 10h."},
    {"id": "d09", "titulo": "Doação de livros", "data": "2023-09-12",
     "texto": "A biblioteca aceita doações de livros em bom estado, publicados nos últimos 15 anos. Enciclopédias, revistas "
              "e livros didáticos não são aceitos. As doações são recebidas às quartas e sextas."},
    {"id": "d10", "titulo": "Acessibilidade", "data": "2024-05-30",
     "texto": "O prédio tem rampas, elevador e banheiros adaptados. Há computadores com leitor de tela, livros em braile e "
              "audiolivros. Cães-guia são bem-vindos em todos os ambientes."},
    {"id": "d11", "titulo": "Impressão e cópias", "data": "2024-10-10",
     "texto": "A impressão em preto e branco custa R$ 0,30 por página e a colorida R$ 1,50. O pagamento é feito no balcão, "
              "em dinheiro ou Pix. Cópias de obras raras não são permitidas."},
    {"id": "d12", "titulo": "Obras raras", "data": "2023-01-20",
     "texto": "O setor de obras raras atende apenas com agendamento, de terça a sexta. As obras são consultadas na sala "
              "própria, com luvas fornecidas pela biblioteca. Fotografias sem flash são permitidas."},
]
