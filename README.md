# 💸 Assistente de Gastos pelo WhatsApp

[![tests](https://github.com/SEU-USUARIO/gastos-whatsapp/actions/workflows/tests.yml/badge.svg)](https://github.com/SEU-USUARIO/gastos-whatsapp/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![WhatsApp Cloud API](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp&logoColor=white)

Um bot que transforma o WhatsApp em um controle de gastos pessoais. Você manda **"almoço 32"** e ele registra, categoriza e responde. Depois é só perguntar **"total"** ou **"resumo"**.

---

## 🤔 Que problema isso resolve?

Quase todo mundo já tentou anotar os gastos em planilha ou aplicativo e desistiu depois de uma semana. Abrir um app, escolher categoria, digitar valor e salvar dá trabalho demais para um cafezinho.

Já o WhatsApp está aberto o dia inteiro. A ideia aqui é **registrar um gasto do mesmo jeito que você mandaria uma mensagem para um amigo**: "uber 18,50", "mercado 120,90 ontem". O bot entende, coloca na categoria certa e, quando você quiser, mostra quanto gastou no mês, em cada categoria e se a semana está melhor ou pior que a anterior.

Sem instalar nada, sem cadastro, sem planilha.

---

## 🎬 Demonstração

<!-- Grave a tela do celular conversando com o bot e salve em docs/demo.gif -->
<!-- ![Demonstração](docs/demo.gif) -->

```text
você > almoço 32
bot  > ✅ R$ 32,00 em Alimentação (hoje)

você > uber 18,50 ontem
bot  > ✅ R$ 18,50 em Transporte (ontem)

você > farmácia 40 12/10
bot  > ✅ R$ 40,00 em Saúde (12/10)

você > total
bot  > 💰 Total de outubro: R$ 90,50

você > resumo
bot  > 📊 Resumo da semana (13/10 a 16/10)
       Total: R$ 90,50

       Por categoria:
       • Saúde: R$ 40,00
       • Alimentação: R$ 32,00
       • Transporte: R$ 18,50

       📉 25% a menos que no mesmo período da semana passada (R$ 120,00).
```

> 💡 Dá para testar sem configurar nada na Meta: `python -m scripts.chat_local` abre essa mesma conversa no terminal.

---

## ✨ Funcionalidades

| Mensagem | O que faz |
|---|---|
| `almoço 32` · `32 almoço` · `uber 18,50` · `aluguel 1.500,00` | Registra um gasto (vírgula ou ponto, com ou sem `R$`) |
| `uber 18,50 ontem` · `cinema 60 anteontem` · `farmácia 40 12/10` | Registra com data (sem data = hoje) |
| `total` | Total do mês atual |
| `total alimentação` | Total de uma categoria no mês |
| `resumo` | Semana atual por categoria, comparada com o mesmo período da semana anterior |
| `últimos` | Os 5 últimos gastos registrados |
| `apagar último` | Desfaz o último registro |
| `categorias` | Lista as categorias e exemplos de palavras-chave |
| `ajuda` | Mostra os comandos com exemplos |

Mais alguns detalhes:

- **Sem acento e sem diferença de maiúsculas:** `ALMOCO 32`, `Almoço 32` e `almoço 32` dão no mesmo.
- **Categorias por palavra-chave** em [`config/categorias.json`](config/categorias.json). É só editar o arquivo, sem mexer em código.
- **Cada número de telefone tem seus próprios dados**, totalmente isolados.
- **Valores em centavos inteiros** (nada de `float` com dinheiro) e fuso `America/Sao_Paulo`.
- **Data no futuro vira ano passado:** em outubro, `20/12` é entendido como 20/12 do ano anterior.

---

## 🏗️ Arquitetura

O projeto é dividido em camadas que só se conhecem por **interfaces**. A regra de negócio não sabe que o WhatsApp existe nem que os gastos são interpretados por regex.

```mermaid
flowchart LR
    U(["👤 Usuário"]) -->|mensagem| META["Meta<br/>WhatsApp Cloud API"]
    META -->|"webhook (POST assinado)"| ROUTER

    subgraph APP["Aplicação FastAPI"]
        direction LR
        ROUTER["Router<br/>valida assinatura HMAC"] --> CH["WhatsAppChannel<br/><i>MessageChannel</i>"]
        CH --> CONV["ConversationService<br/>deduplicação + janela 24h"]
        CONV --> HANDLER["MessageHandler"]
        HANDLER --> INTERP["RuleBasedInterpreter<br/><i>MessageInterpreter</i>"]
        INTERP --> CAT["Categorizer<br/>categorias.json"]
        HANDLER --> SVC["ExpenseService<br/>regras de negócio"]
        SVC --> REPO["SqlAlchemyExpenseRepository<br/><i>ExpenseRepository</i>"]
        REPO --> DB[("SQLite / PostgreSQL")]
    end

    CONV -.->|resposta| CH
    CH -.->|Graph API| META
    META -.-> U
```

### O caminho de uma mensagem

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant M as Meta (Cloud API)
    participant W as Webhook (FastAPI)
    participant C as ConversationService
    participant I as RuleBasedInterpreter
    participant S as ExpenseService
    participant DB as Banco

    U->>M: "uber 18,50 ontem"
    M->>W: POST /webhooks/whatsapp + X-Hub-Signature-256
    W->>W: valida assinatura (HMAC-SHA256)
    W->>C: IncomingMessage
    C->>DB: já processei este wamid?
    C->>I: interpret("uber 18,50 ontem")
    I-->>C: RegisterExpense(uber, 1850, 15/10, Transporte)
    C->>S: register(...)
    S->>DB: INSERT
    C->>M: POST /messages "✅ R$ 18,50 em Transporte (ontem)"
    M->>U: resposta
    W-->>M: 200 OK
```

### Camadas e pastas

```
app/
├── channels/          # ENTRADA/SAÍDA: MessageChannel + implementação WhatsApp (webhook, HMAC)
├── interpretation/    # TEXTO → INTENÇÃO: MessageInterpreter + RuleBasedInterpreter
├── services/          # REGRAS: ExpenseService, MessageHandler, ConversationService, respostas
├── repositories/      # BANCO: ExpenseRepository + implementação SQLAlchemy
├── db/                # engine, sessão e tabelas
├── dependencies.py    # o único lugar que decide quais implementações usar
└── main.py            # app FastAPI
config/categorias.json # categorias e palavras-chave
scripts/chat_local.py  # chat no terminal, sem WhatsApp
tests/                 # 177 testes (pytest)
```

### Decisões de projeto

| Decisão | Por quê |
|---|---|
| `MessageChannel` abstrato | Adicionar Telegram é criar `TelegramChannel` + uma rota. `ConversationService` e o resto continuam iguais |
| `MessageInterpreter` abstrato | Um futuro `AIInterpreter` só precisa devolver as mesmas *intents*. A troca é uma linha em `dependencies.py` |
| *Intents* como dataclasses | O interpretador diz **o que** o usuário quer; o `MessageHandler` decide **como** atender (com `match`/`case`) |
| Valores em centavos (`int`) | Evita erros de arredondamento de `float` com dinheiro |
| `Clock` injetável | "Hoje", "ontem" e "semana" ficam determinísticos nos testes |
| Deduplicação por `wamid` | A Meta reenvia o webhook quando há falha; sem isso, o mesmo gasto seria registrado duas vezes |
| Resposta só dentro de 24h | Se um reenvio chegar depois da janela de atendimento, o gasto é salvo mas nenhuma mensagem é enviada |
| Resumo compara o **mesmo trecho** da semana anterior | Numa quinta, comparar seg–qui com seg–qui é justo; comparar com a semana inteira não seria |
| Comandos antes de gastos | `total alimentação` nunca vira um gasto chamado "total" |
| `99 25` | Quando os dois lados são números, vale a leitura em que a descrição é palavra-chave (`99` → Transporte) |

---

## 🚀 Rodando localmente

### 1. Instalação

Requer Python 3.12 ou mais recente.

```bash
git clone https://github.com/SEU-USUARIO/gastos-whatsapp.git
cd gastos-whatsapp

python -m venv .venv
# Windows:      .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env        # no Windows: copy .env.example .env
```

### 2. Teste rápido, sem WhatsApp

```bash
python -m scripts.chat_local            # dados salvos em chat_local.db
python -m scripts.chat_local --memoria  # dados somem ao sair
```

### 3. Testes automatizados

```bash
pytest           # 177 testes
ruff check .     # lint
```

### 4. Subindo a API

```bash
uvicorn app.main:app --reload
```

Confira em <http://localhost:8000/health> (deve responder `{"status":"ok"}`). A documentação automática fica em <http://localhost:8000/docs>.

### 5. Expondo para a internet com ngrok

A Meta precisa alcançar seu webhook por uma URL HTTPS pública. O [ngrok](https://ngrok.com/) cria esse túnel de graça:

```bash
# instale e faça login no ngrok uma vez:  ngrok config add-authtoken SEU_TOKEN
ngrok http 8000
```

Ele mostra uma URL como `https://abcd-1234.ngrok-free.app`. A URL do webhook será:

```
https://abcd-1234.ngrok-free.app/webhooks/whatsapp
```

> ⚠️ No plano gratuito do ngrok, a URL muda sempre que você reinicia o túnel. Quando isso acontecer, atualize o webhook na Meta.

---

## 📱 Configurando o app na Meta (WhatsApp Cloud API)

Tudo abaixo é gratuito: a Meta fornece um **número de teste** que pode conversar com até 5 números cadastrados por você.

> Os nomes dos menus podem mudar um pouco conforme a Meta atualiza o painel.

### Passo 1: criar o app

1. Acesse [developers.facebook.com](https://developers.facebook.com/) e entre com sua conta do Facebook. Se for a primeira vez, cadastre-se como desenvolvedor.
2. Vá em **Meus apps → Criar app**.
3. No caso de uso, escolha **"Conectar-se com clientes pelo WhatsApp"** e avance.
4. Dê um nome ao app e selecione (ou crie) um **portfólio empresarial**.

### Passo 2: pegar as credenciais

No painel do app, abra **WhatsApp → Configuração da API** (*API Setup*):

| Na tela da Meta | Variável no `.env` |
|---|---|
| **Token de acesso temporário** (botão *Gerar token*) | `WHATSAPP_ACCESS_TOKEN` |
| **Identificação do número de telefone** (*Phone number ID*) do número de teste | `WHATSAPP_PHONE_NUMBER_ID` |

Depois, em **Configurações do app → Básico**, clique em *Mostrar* na **Chave secreta do app** (*App Secret*):

| Na tela da Meta | Variável no `.env` |
|---|---|
| **Chave secreta do app** | `WHATSAPP_APP_SECRET` |

Por fim, invente uma senha qualquer para `WHATSAPP_VERIFY_TOKEN` (ex.: `meu-token-123`). Ela serve só para a Meta confirmar que o webhook é seu.

> ⏳ O token temporário expira em **24 horas**. Para algo duradouro, crie um **usuário do sistema** em *Configurações do negócio → Usuários do sistema* e gere um token com as permissões `whatsapp_business_messaging` e `whatsapp_business_management`.

### Passo 3: cadastrar seu número como destinatário

Ainda em **Configuração da API**, no campo **Para** (*To*), adicione o seu número de WhatsApp e confirme com o código recebido. O número de teste só conversa com números cadastrados ali.

### Passo 4: configurar o webhook

1. Com `uvicorn` e `ngrok` rodando, vá em **WhatsApp → Configuração** (*Configuration*).
2. Em **Webhook**, clique em *Editar*:
   - **URL de callback:** `https://SEU-NGROK.ngrok-free.app/webhooks/whatsapp`
   - **Token de verificação:** o mesmo valor de `WHATSAPP_VERIFY_TOKEN`
3. Clique em **Verificar e salvar**. A Meta chama `GET /webhooks/whatsapp` e o app devolve o *challenge*.
4. Em **Campos do webhook**, clique em **Gerenciar** e assine o campo **`messages`**.

### Passo 5: conversar

Mande `oi` do seu WhatsApp para o número de teste. O bot deve responder com a ajuda. Depois experimente `almoço 32`. 🎉

### Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Verificar e salvar" falha | `uvicorn` ou `ngrok` parados, URL sem `/webhooks/whatsapp`, ou token de verificação diferente do `.env` |
| Webhook chega mas o log mostra `assinatura inválida` (403) | `WHATSAPP_APP_SECRET` errado (é a chave secreta do **app**, não o token de acesso) |
| Mensagem chega, mas a resposta não; erro `131030` no log | Seu número não está na lista de destinatários do número de teste |
| Erro `131030` mesmo com o número cadastrado (Brasil) | A Meta às vezes entrega números brasileiros **sem o 9** extra (`55 11 8888-7777`). Cadastre também essa versão do número em **Para** |
| Erro `401` ao responder | O token temporário expirou (24h). Gere outro |

---

## 💰 Custo zero

- **WhatsApp:** o número de teste é gratuito, e o bot **só responde** a mensagens enviadas pelo usuário, dentro da janela de atendimento de 24h. Respostas de texto livre nessa janela não são cobradas pela Meta, e não há mensagens automáticas nem agendadas.
- **Hospedagem local:** FastAPI + SQLite no seu computador, mais ngrok gratuito.
- **Banco:** para produção, basta apontar `DATABASE_URL` para um PostgreSQL gratuito (Neon, Supabase etc.):

```bash
pip install "psycopg[binary]"
# .env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/gastos
```

---

## 🛠️ Personalizando as categorias

Edite [`config/categorias.json`](config/categorias.json) e reinicie a aplicação:

```json
{
  "fallback": "Outros",
  "categorias": {
    "Pets": ["ração", "veterinário", "petshop"],
    "Alimentação": ["almoço", "janta", "ifood"]
  }
}
```

As palavras são comparadas sem acento e sem diferença de maiúsculas, sempre como **palavra inteira** ("bar" não confunde com "barbearia"). Palavras compostas como `"plano de saúde"` também funcionam.

---

## 🧪 Testes

São 177 testes que rodam em cerca de 2 segundos, sem internet:

| Arquivo | O que cobre |
|---|---|
| `test_rule_based_interpreter.py` | Dezenas de formatos de mensagem: valores, datas, comandos, mensagens inválidas |
| `test_dates.py`, `test_text_and_amounts.py`, `test_categorizer.py` | Datas relativas e `dd/mm`, valores brasileiros, normalização, palavras-chave |
| `test_repository.py` | Consultas no banco e **isolamento entre usuários** |
| `test_expense_service.py` | Mês, semana, comparação semanal, ano bissexto, apagar último |
| `test_message_handler.py` | Os 8 comandos de ponta a ponta, texto exato das respostas |
| `test_whatsapp_webhook.py` | Assinatura HMAC, verify token, deduplicação, janela de 24h, falha da Graph API (mockada com `respx`) |

---

## 🗺️ Próximos passos

- [ ] **IA para linguagem natural:** um `AIInterpreter` que entenda "gastei uns 30 reais no almoço com o pessoal ontem". A interface já está pronta.
- [ ] **Áudio com Whisper:** transcrever mensagens de voz e mandar o texto para o interpretador.
- [ ] **Foto do cupom fiscal:** OCR/visão para extrair valor e estabelecimento.
- [ ] **Dashboard web:** gráficos de gastos por mês e categoria.
- [ ] **Limites por categoria:** "você já usou 80% do limite de Lazer este mês", sempre como resposta a uma mensagem do usuário.
- [ ] **Telegram:** um segundo `MessageChannel`, reaproveitando todo o resto.
- [ ] **Migrações com Alembic** e deploy em nuvem gratuita.

---

## 🧰 Stack

Python 3.12+ · FastAPI · SQLAlchemy 2 · SQLite/PostgreSQL · httpx · WhatsApp Cloud API · pytest · respx · ruff · GitHub Actions
