# Requisitos e atributos de qualidade — v0.1

## Convenções

- **MUST:** obrigatório para a v0.1.
- **SHOULD:** esperado, mas pode ser classificado como experimental com justificativa.
- **MAY:** opcional e dependente de experimento.

## Requisitos funcionais

### Intake e workflow

- **FR-001 — MUST:** receber uma especificação estruturada e referência para um SUT permitido.
- **FR-002 — MUST:** validar schemas antes de iniciar chamadas de modelo ou execução.
- **FR-003 — MUST:** atribuir identificador único e versão a cada run.
- **FR-004 — MUST:** representar estados, transições, tentativas e encerramento de forma explícita.
- **FR-005 — MUST:** interromper execução ao atingir qualquer budget configurado.
- **FR-006 — MUST:** solicitar aprovação humana nos pontos classificados como sensíveis.

### Análise e design

- **FR-010 — MUST:** extrair comportamentos, restrições e ambiguidades do requisito.
- **FR-011 — MUST:** produzir riscos priorizados com justificativa.
- **FR-012 — MUST:** gerar cenários positivos, negativos e de fronteira rastreáveis.
- **FR-013 — MUST:** distinguir ausência de informação de decisão inferida.

### Geração de testes

- **FR-020 — MUST:** selecionar um `LanguageProfile` compatível com o SUT.
- **FR-021 — MUST:** gerar testes no workspace autorizado sem alterar o SUT original.
- **FR-022 — MUST:** validar estrutura, sintaxe e políticas antes da execução.
- **FR-023 — MUST:** limitar arquivos, dependências e tamanho dos artefatos.
- **FR-024 — MUST:** permitir correção de teste dentro do limite de tentativas.
- **FR-025 — MUST:** manter rastreabilidade entre requisito, risco, cenário e teste.

### Execução e segurança

- **FR-030 — MUST:** executar código não confiável em container efêmero no Docker Desktop.
- **FR-031 — MUST:** desabilitar rede por padrão na execução do SUT e dos testes.
- **FR-032 — MUST:** aplicar limites de CPU, memória, processos, duração e filesystem.
- **FR-033 — MUST:** impedir acesso da sandbox às credenciais do provider.
- **FR-034 — MUST:** capturar código de saída, stdout e stderr dentro de limites.
- **FR-035 — MUST:** descartar container e workspace conforme a política de retenção.

### Avaliação e falhas

- **FR-040 — MUST:** classificar falhas como teste, SUT, geração, política, infraestrutura ou inconclusiva.
- **FR-041 — MUST:** executar testes de referência ou oracles independentes quando disponíveis.
- **FR-042 — MUST:** coletar coverage nas linguagens classificadas como suportadas.
- **FR-043 — MUST:** executar mutation testing nas linguagens classificadas como suportadas.
- **FR-044 — SHOULD:** aplicar teste metamórfico quando houver relação válida registrada.
- **FR-045 — MUST:** registrar intervenções humanas e violações de política.

### Evidências e relatórios

- **FR-050 — MUST:** emitir eventos JSONL correlacionáveis.
- **FR-051 — MUST:** produzir manifest com hashes, versões, ambiente, modelo e budgets.
- **FR-052 — MUST:** produzir relatório estruturado e Markdown.
- **FR-053 — MUST:** relacionar conclusões às evidências correspondentes.
- **FR-054 — MUST:** sanitizar dados sensíveis antes de publicação.
- **FR-055 — MUST:** diferenciar fato, inferência e recomendação no relatório.

### Modos e experiência

- **FR-060 — MUST:** oferecer modo demo sem credencial por respostas gravadas.
- **FR-061 — MUST:** oferecer modo live configurável pelo usuário.
- **FR-062 — MUST:** diagnosticar Docker Desktop, provider, configuração e ambiente.
- **FR-063 — MUST:** explicar limitações e nível de suporte do perfil selecionado.

### Extensibilidade

- **FR-070 — MUST:** compor perfis a partir de adaptadores de capacidade.
- **FR-071 — MUST:** validar perfis por conformance suite.
- **FR-072 — MUST:** suportar Python e TypeScript end-to-end.
- **FR-073 — MUST:** fornecer um perfil Java experimental executável.
- **FR-074 — SHOULD:** permitir substituição do provider sem alteração das regras do workflow.
- **FR-075 — MAY:** expor integração por MCP após experimento aprovado.

## Atributos de qualidade

### Segurança

- **QA-SEC-001:** nenhuma credencial do provider deve estar acessível no container do SUT.
- **QA-SEC-002:** tentativas de rede devem falhar de forma observável quando a política estiver desabilitada.
- **QA-SEC-003:** mounts devem ser mínimos e explicitamente autorizados.
- **QA-SEC-004:** cenários adversariais críticos devem terminar em falha segura.

### Auditabilidade

- **QA-AUD-001:** toda transição deve produzir evento correlacionável.
- **QA-AUD-002:** uma conclusão deve apontar para artefato ou decisão humana.
- **QA-AUD-003:** o manifest deve permitir reconstruir configuração e versões da run.

### Reprodutibilidade

- **QA-REP-001:** o modo demo deve produzir resultado estável no ambiente suportado.
- **QA-REP-002:** execuções live devem registrar parâmetros necessários para comparação, sem prometer determinismo absoluto.
- **QA-REP-003:** datasets, prompts e workflows devem ser versionados por hash.

### Extensibilidade

- **QA-EXT-001:** adicionar uma capacidade de tooling não deve exigir alterar o runtime.
- **QA-EXT-002:** adicionar um perfil deve reutilizar contratos e normalização existentes.
- **QA-EXT-003:** incompatibilidades devem aparecer como capability matrix, não como falha silenciosa.

### Usabilidade

- **QA-USA-001:** uma pessoa deve compreender propósito e status em até cinco minutos.
- **QA-USA-002:** o diagnóstico deve indicar pré-requisito ausente e ação recomendada.
- **QA-USA-003:** o relatório deve ser compreendido pelos participantes da developer preview sem explicação individual do autor.

### Manutenibilidade

- **QA-MAN-001:** regras de domínio não devem depender diretamente de SDK de provider ou comandos de linguagem.
- **QA-MAN-002:** componentes críticos devem possuir testes unitários, de contrato ou de transição.
- **QA-MAN-003:** decisões arquiteturais aceitas devem possuir ADR.

### Eficiência e controle

- **QA-EFF-001:** toda run deve possuir limites de duração, tentativas, tokens e custo.
- **QA-EFF-002:** stdout, stderr, contexto e artefatos devem possuir tamanho máximo.
- **QA-EFF-003:** o relatório deve mostrar consumo medido ou estimado.

### Portabilidade

- **QA-PORT-001:** Windows com Docker Desktop/WSL2 será o ambiente de referência obrigatório.
- **QA-PORT-002:** outros ambientes só poderão ser anunciados após execução da matriz de compatibilidade.

## Rastreabilidade inicial

| Objetivo | Requisitos relacionados |
|---|---|
| Workflow controlado | FR-003 a FR-006 |
| Test design assistido | FR-010 a FR-013 |
| Automação multilíngue | FR-020 a FR-025, FR-070 a FR-074 |
| Execução segura | FR-030 a FR-035, QA-SEC-* |
| Qualidade demonstrável | FR-040 a FR-045 |
| Evidência auditável | FR-050 a FR-055, QA-AUD-* |
| Uso educacional | FR-060 a FR-063, QA-USA-* |

Os valores quantitativos de budgets e limites serão definidos na Etapa 2 por contratos e políticas, e validados nos spikes.

