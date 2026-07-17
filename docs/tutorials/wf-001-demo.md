# Tutorial — WF-001 em modo demo

Este tutorial usa exclusivamente o perfil experimental e o ambiente descritos em [suporte e limitações](../project/support-and-limitations.md).

Este tutorial acompanha uma run fictícia do requisito “somar dois inteiros”. O objetivo é entender como contexto, análise, artifact, execução e report se conectam — não avaliar um modelo online.

## Fronteira da demonstração

O comando público atual usa:

- contexto, SUT e cassettes fictícios empacotados;
- análise e artifact previamente gravados;
- skill `unit` e perfil experimental `python-pytest`;
- execução local pelo daemon Docker;
- container sem rede, com filesystem e recursos limitados;
- avaliação funcional determinística da execução gerada.

Ele não chama provider, não usa `OPENAI_API_KEY` e não executa o fluxo combinado com oracle curado do incremento 5.3. No report deste caminho, `oracle_execution_id` pode ser `null`.

## 1. Diagnóstico e execução

Depois de seguir o [quickstart](../getting-started/quickstart.md):

```powershell
.\.venv\Scripts\asef.exe doctor --mode demo --output .asef/doctor
.\.venv\Scripts\asef.exe run --title "Sum two integers" --requirement "Return the arithmetic sum of two signed integers"
```

Guarde `run_id`, `run_dir`, `report_json` e `report_markdown` retornados no stdout.

## 2. Contexto congelado

Antes da chamada agêntica, o ASEF resolve o `QualityContext` e grava `context-snapshot.json`. O snapshot fixa sistema, repositório, skill, perfil, modo, provider/modelo declarados, scopes e imagem por digest.

O snapshot não contém a chave do host. Mudanças posteriores no arquivo de contexto não reescrevem retroativamente a run.

## 3. Análise, riscos e cenários

A cassette de análise fornece listas estruturadas de behaviors, risks e scenarios. O state registra esses fatos; o report cria IDs contíguos:

- `REQ-001` para o requisito;
- `BEH-001...` para behaviors;
- `RSK-001...` para risks;
- `SCN-001...` para scenarios.

Cada item deriva do requisito. O report deliberadamente não cria relação risco→cenário, pois essa causalidade não foi observada no contrato atual.

## 4. Artifact e static validation

A cassette de geração propõe um único arquivo Python sob `tests_generated/`. A skill valida path, extensão, tamanho, conteúdo e correspondência exata dos scenario IDs antes de criar o workspace.

O artifact persistido recebe identidade `ART-ATTEMPT-001`, path relativo, SHA-256 e links `COVERS_SCENARIO`. O source não é copiado para o corpo do report; apenas metadata e evidence ref aparecem ali.

## 5. Execução isolada

O adapter executa o teste dentro da imagem fixada pelo snapshot. O container usa controles de rede, filesystem, memória, PIDs e timeout. Stdout/stderr permanecem como arquivos de evidência; o report não os reflete como texto público.

O resultado normalizado registra contagens, exit code, duração, ferramenta e outcome. A cadeia pública é:

```text
SCN-NNN <- ART-ATTEMPT-001 <- EXEC-ATTEMPT-001-generated
```

Essa direção representa links tipados do contrato, não execução automática de uma recomendação.

## 6. Avaliação funcional

Para `ACCEPTED`, a execução precisa ter ao menos um teste, todos aprovados e zero failures, errors ou skips. Timeout, falha do engine ou erro de ferramenta não viram falha funcional silenciosamente; recebem classificação própria.

O report separa:

- facts — valores observados, como status e acceptance;
- inference — conclusão derivada desses facts;
- recommendation — próxima ação determinística e não executável;
- limitation — fronteira ou ausência de evidência.

## 7. Quality não altera acceptance

O comando `asef run` deste tutorial não solicita coverage ou mutation. O report registra quality como `NOT_REQUESTED` e inclui a limitação correspondente.

Quando quality é executada pelo fluxo Alpha que a suporta, suas observations enriquecem o report sem mudar retroativamente a classificação funcional. Coverage e mutation são evidências, não thresholds universais de qualidade.

## 8. Conferir o audit trail

Dentro de `run_dir`, confira:

- `state.json` — estado tipado e facts da run;
- `events.jsonl` — eventos novos em ordem de persistência;
- `manifest.json` — identidade da run e hashes dos reports;
- `artifacts/` e `results/` — evidências controladas;
- `report.json` — representação normativa;
- `report.md` — view derivada do contrato validado.

No manifest, `reports.json.sha256` e `reports.markdown.sha256` devem reconciliar com os arquivos. Reemissão não encobre tamper prévio.

## 9. Interpretar sem overclaim

`SUCCEEDED` + `ACCEPTED` responde apenas: “a execução registrada satisfez a regra funcional determinística deste perfil e desta run”. Ainda permanecem as limitações do perfil experimental, da cassette, do SUT fictício, do daemon local e da ausência de avaliação humana externa.

Continue em [interpretação do report](../guides/report-interpretation.md). Para um resultado inesperado, use [troubleshooting](../guides/troubleshooting.md).
