Crie um projeto completo e funcional em Django chamado `ticket_triage` que demonstra a integração em nível de produção de uma LLM (usando o SDK oficial `google-genai`) para triagem automática de tickets de suporte ao cliente.

### Requisitos Técnicos e Arquitetura
1. **Ambiente e Dependências:**
   - Crie o arquivo `requirements.txt` contendo: `django`, `google-genai`, `pydantic`, `python-dotenv`.
   - Crie um arquivo `.env.example` com a variável `GEMINI_API_KEY=sua_chave_aqui` e configure `settings.py` para carregar variáveis de ambiente via `python-dotenv`.
   - Use SQLite como banco de dados padrão.

2. **Estrutura do Projeto:**
   - Projeto principal: `core`
   - App principal: `tickets`

3. **Modelagem de Dados (`tickets/models.py`):**
   - Crie o model `Ticket` com os campos:
     - `mensagem_original` (TextField)
     - `resumo` (CharField, max_length=255)
     - `categoria` (CharField, choices: `FINANCEIRO`, `TECNICO`, `COMERCIAL`, `OUTROS`)
     - `urgencia` (CharField, choices: `BAIXA`, `MEDIA`, `ALTA`)
     - `resposta_sugerida` (TextField)
     - `tokens_utilizados` (IntegerField, null=True, blank=True)
     - `criado_em` (DateTimeField, auto_now_add=True)
   - Registre o model `Ticket` no `tickets/admin.py` com list_display, list_filter e search_fields configurados.

4. **Camada de Serviço de IA (`tickets/services.py`):**
   - Isole toda a lógica de comunicação com a LLM neste arquivo.
   - Defina um schema estrito usando `pydantic.BaseModel` (`AnaliseTicketSchema`) contendo os campos `resumo`, `categoria`, `urgencia` e `resposta_sugerida` com descrições claras via `Field(description=...)`.
   - Implemente a função `processar_ticket_com_ia(texto: str) -> dict`:
     - Utilize `from google import genai` e `from google.genai import types`.
     - Use o modelo `gemini-2.5-flash`.
     - Configure `GenerateContentConfig` com `system_instruction`, `temperature=0.2`, `response_mime_type="application/json"` e `response_schema=AnaliseTicketSchema`.
     - Capture o total de tokens gastos a partir dos metadados de uso (`usage_metadata.total_token_count`) se disponível.
     - Implemente tratamento de exceções robusto (`try/except`) para falhas de API, falta de chave ou timeout, retornando um dicionário padronizado (`{"sucesso": bool, "dados": dict | None, "erro": str | None}`).

5. **Views e Rotas (`tickets/views.py` e `urls.py`):**
   - Crie uma view principal (`index`) que:
     - No `POST`: recebe a mensagem do formulário, chama `processar_ticket_com_ia()`, salva o resultado no banco de dados (`Ticket.objects.create(...)`) caso tenha sucesso, ou exibe a mensagem de erro sem quebrar a aplicação.
     - No `GET` (e após o `POST`): renderiza o formulário e lista os últimos 10 tickets analisados salvos no banco de dados, ordenados do mais recente para o mais antigo.

6. **Interface Web (`tickets/templates/tickets/index.html`):**
   - Crie um template HTML limpo, responsivo e auto-contido (CSS inline ou `<style>` no próprio arquivo, sem depender de frameworks pesados) com:
     - Formulário com `<textarea>` e botão de envio (com estado visual de carregamento via JS simples ao submeter para evitar cliques duplos).
     - Exibição de alertas de erro caso a API falhe.
     - Histórico em cards dos tickets analisados mostrando badges coloridos para `Urgência` e `Categoria`, o resumo, a resposta sugerida e a contagem de tokens consumidos.

### Execução Final
Após criar todos os arquivos:
1. Rode `python manage.py makemigrations` e `python manage.py migrate` para validar que o banco e os modelos estão sem erros.
2. Liste no final os comandos exatos que eu preciso rodar para ativar o ambiente, configurar a chave e iniciar o servidor.
