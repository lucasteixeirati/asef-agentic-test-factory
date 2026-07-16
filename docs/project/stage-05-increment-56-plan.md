# Incremento 5.6 — Coverage e mutation do SUT

- **Data:** 2026-07-15
- **Estado:** implementação e revisão concluídas; candidata `0.1.0a4` aprovada nos cinco jobs da CI; publicação pendente
- **Dependências:** incrementos 5.1 a 5.5 concluídos; Smoke Dataset 20/20 aprovado na CI
- **Gate relacionado:** G5-12 e G5-13, com evidência complementar para G5-05, G5-09, G5-15, G5-17 e G5-20
- **Decisão para implementar:** aprovada explicitamente em 2026-07-15

## 1. Objetivo

Implementar as capabilities Python de coverage e mutation sobre um SUT e uma suíte de testes aceitos, normalizar seus resultados em contratos neutros e anexar as evidências ao report da run sem alterar o SUT original. A execução deve ser isolada, sem rede, limitada por budgets e explícita quando a ferramenta estiver ausente, falhar ou produzir resultado parcial.

Coverage e mutation são sinais distintos. Coverage informa quais linhas e branches foram exercitados; mutation observa se alterações artificiais foram detectadas pelos testes. Nenhum dos dois será tratado isoladamente como prova de qualidade, como diagnóstico de defeito ou como threshold universal para projetos externos.

## 2. Escopo

### Incluído

- portas neutras para solicitar e observar capabilities de qualidade;
- adapter Python de coverage com saída JSON nativa e linhas/branches separados;
- adapter Python de mutation com estados nativos preservados e normalização verificável;
- budgets independentes de duração e quantidade de mutantes admitidos;
- imagem Docker de qualidade separada, pinada por versões e hashes;
- workspace descartável para tooling, mantendo o SUT original somente leitura;
- fixture sintética de conformance com totais conhecidos;
- baseline pequena sobre o SUT Python de referência e um teste aceito;
- persistência de outputs nativos, resultados normalizados e limitações;
- integração tipada com JSON/Markdown da run;
- job de CI `quality-capabilities` sem provider, chave ou rede no container;
- atualização do perfil `python-pytest` somente após as provas de conformance.

### Não incluído

- impor score mínimo de coverage ou mutation a projetos externos;
- avaliar repositórios arbitrários ou instalar dependências do SUT;
- usar coverage/mutation para decidir `SUT_DEFECT_SUSPECTED`;
- executar mutation em todos os dez casos Smoke ou em toda PR do core;
- substituir o mutation pilot periódico do próprio ASEF;
- generalizar adapters para Node/TypeScript ou Java, pertencente à Etapa 6;
- Security Dataset, `asef doctor` e retenção final, pertencentes ao 5.7;
- consolidar toda a experiência pública e os reports do Alpha, pertencente ao 5.8;
- atualizar versão, criar tag ou publicar release.

## 3. Findings da baseline

1. `CoverageResult` e `MutationResult` já existem e validam totais, escopo, versão, duração, budget e referência para o output bruto, mas não há portas ou adapters que os produzam.
2. O perfil `python-pytest` ainda declara coverage e mutation como `planned`.
3. `DockerRunner` já oferece rede bloqueada, root filesystem read-only, fonte read-only, tmpfs e output mount separado. Essa fronteira pode ser reutilizada sem tornar o SUT gravável.
4. A imagem `asef/python-pytest:8.3.3` contém apenas o runner validado. Adicionar ferramentas pesadas nela aumentaria a superfície e invalidaria uma baseline já estável.
5. Coverage do próprio ASEF e mutation pilot do core medem o produto, não comprovam capabilities aplicadas ao SUT.
6. O fluxo Alpha remove workspaces de tentativa no encerramento. A avaliação de qualidade precisará remontar o artifact aceito em um workspace próprio e descartável.
7. O report atual recebe uma avaliação genérica, mas ainda não possui seção tipada para disponibilidade, resultado parcial e limitações de quality capabilities.
8. Coverage.py possui JSON estruturado com totais separados de linhas e branches. O adapter não precisa inferir métricas de tabelas humanas.
9. Mutmut 3 exige suporte a `fork`; no ambiente de referência Windows ele deve executar exclusivamente no container Linux.
10. Mutmut não documenta um contrato JSON público equivalente ao coverage. A primeira fatia deve caracterizar a versão pinada e provar uma extração estável antes de implementar o normalizador.

## 4. Decisões de desenho

### 4.1 Contrato de observação da capability

Será criado um envelope neutro `QualityCapabilityObservation`, separado do resultado métrico, com:

- `capability_id`: `coverage` ou `mutation`;
- estado `COMPLETED`, `PARTIAL`, `UNAVAILABLE`, `FAILED` ou `BUDGET_EXHAUSTED`;
- ferramenta, versão, escopo solicitado e duração;
- resultado normalizado opcional;
- referências para output nativo, stdout e stderr sanitizados;
- código de diagnóstico estável e mensagem limitada;
- limitações explícitas.

`COMPLETED` exige um `CoverageResult` ou `MutationResult` válido. Os demais estados não inventam zeros nem scores. Ausência de imagem, ferramenta, branch data ou suporte a `fork` será visível e testável.

Um `QualityEvaluationReport` agregará as observações solicitadas. A avaliação funcional da run e a avaliação de qualidade permanecerão campos irmãos: falha de tooling não reclassifica teste nem SUT, mas torna a avaliação de qualidade incompleta.

### 4.2 Requests, policy e budgets

As portas receberão requests tipados com:

- perfil e capability explícitos;
- paths POSIX relativos e canônicos para fonte e testes;
- escopo não vazio e contido no workspace autorizado;
- timeout positivo, limitado pela policy do host;
- para mutation, `max_mutants` positivo e limite superior da policy;
- versão esperada da ferramenta e referência da imagem.

Defaults do Alpha: até 180 segundos para coverage e 600 segundos para mutation. A fixture de conformance usará budgets menores. O host aplica o hard timeout e remove o container. O budget de mutantes deve ser aplicado antes ou durante a admissão dos mutantes, nunca apenas conferido depois de executar todos.

Se a versão pinada do mutmut não oferecer uma forma estável de descobrir e limitar mutantes, a implementação deverá parar para escolher entre um exporter controlado sobre o estado nativo pinado ou outra ferramenta. Não será aceito simular o limite truncando somente o report após trabalho ilimitado.

### 4.3 Imagem de qualidade separada

Será criada `tooling/python-quality/`, sem substituir a imagem pytest. A imagem conterá:

- base Python fixada por digest;
- pytest `8.3.3`, coverage `7.10.7` e mutmut `3.6.0` inicialmente, preservando os pins já usados pelo projeto;
- dependências transitivas com hashes obrigatórios;
- driver não interativo de versão fixa para produzir artifacts estruturados;
- verificações de versão no build.

O adapter resolve a tag local para image ID antes de executar. O container continua sem rede, capabilities Linux, privilégios, Docker socket ou secrets.

### 4.4 Filesystem e imutabilidade

O workspace com SUT e testes será montado em `/workspace` como read-only. Coverage gravará o arquivo de dados em `/tmp` e o JSON nativo em `/asef-output`.

Mutation copiará apenas os paths autorizados para uma área descartável no tmpfs do container e executará mutmut nessa cópia. `mutants/`, cache e bancos nativos nunca serão criados no SUT original. Somente resultados limitados serão exportados para `/asef-output`.

Antes e depois da execução, hashes do fixture manifest e dos arquivos autorizados serão comparados. Outputs possuem limite de bytes, nomes fixos e leitura defensiva; symlinks, traversal e arquivos inesperados são rejeitados.

### 4.5 Coverage

O driver executará os testes com branch coverage habilitada e `source` restrito aos paths solicitados. O output canônico será o JSON nativo do coverage.py. O normalizador conciliará:

- `covered_lines` e `num_statements`;
- `covered_branches` e `num_branches`;
- exclusões declaradas;
- versão, escopo e duração;
- ausência real de branches, sem copiar o percentual combinado da ferramenta.

Falha dos testes, falha do collector, JSON ausente/malformado e timeout serão distinguidos. O adapter nunca reconstruirá totais a partir do percentual arredondado.

### 4.6 Mutation

A fatia inicial caracterizará mutmut `3.6.0` em uma fixture mínima, incluindo os estados efetivamente produzidos, armazenamento nativo, comandos não interativos, efeito do timeout e possibilidade de admissão limitada.

O mapeamento será publicado em uma tabela de conformance. Estados sem equivalente neutro fiel não serão fundidos silenciosamente. Se `suspicious` ou outro estado inconclusivo for observável, o contrato receberá evolução aditiva ou a observation ficará `PARTIAL`; ele não será chamado de `killed`, `survived` ou `invalid` sem justificativa.

O resultado deve reconciliar mortos, sobreviventes, inválidos, timeout e não executados. `mutation_score` continuará calculado apenas sobre mortos mais sobreviventes; incompletos não melhoram nem pioram artificialmente o score.

### 4.7 Integração com a run

Após um artifact ser aceito pela matriz determinística, um application service opcional:

1. remonta SUT e artifact em workspace efêmero próprio;
2. resolve as capabilities declaradas pelo perfil e autorizadas pelo contexto;
3. executa coverage e, quando solicitado, mutation com budgets independentes;
4. persiste outputs nativos e resultados normalizados antes do cleanup;
5. adiciona evidence refs e `facts["quality"]` ao estado;
6. inclui a seção `quality` nos reports JSON e Markdown;
7. remove workspaces e outputs operacionais não retidos.

Essa integração não será ligada automaticamente aos dez casos Smoke. A conformance e uma run Alpha dedicada provarão o caminho sem multiplicar o custo de mutation.

## 5. Fixtures e baseline

### Fixture de conformance

Criar uma fixture mínima, independente do SUT principal, contendo:

- funções com linhas e branches deliberadamente exercitados e não exercitados;
- testes que passam e produzem totais coverage conhecidos;
- mutantes conhecidos que incluam ao menos um morto e um sobrevivente;
- configuração de ferramenta versionada;
- manifest com hashes e expectativas nativas/normalizadas;
- variante de timeout e outputs nativos inválidos para testes do normalizador.

Os valores esperados serão derivados uma vez da ferramenta pinada, revisados contra fonte/testes e então congelados no manifest. Uma mudança de versão exige atualizar deliberadamente a baseline; não haverá autoaceite de novos totais.

### Baseline do SUT de referência

Uma run dedicada usará `examples/python-alpha/reference_sut` e um artifact aceito. O report publicará números observados, duração, budgets, versão e limitações. Essa amostra demonstra a capability; não será chamada de benchmark ou garantia sobre suites externas.

## 6. Persistência e reports

Artifacts propostos por run:

```text
quality/
  quality-evaluation.json
  coverage/
    native-coverage.json
    result.json
    stdout.txt
    stderr.txt
  mutation/
    native-result.json
    result.json
    stdout.txt
    stderr.txt
```

Arquivos são gravados atomicamente e nunca sobrescritos. O JSON da run referencia cada artifact por `EvidenceRef`; o Markdown mostra estado, ferramenta, escopo, linhas, branches, mutantes, score quando conclusivo, duração, budgets e limitações.

Paths absolutos, conteúdo do SUT, banco interno integral da ferramenta e stdout ilimitado não entram no report público. Facts, inferências e recomendações continuam separados: os totais são fatos; interpretar lacunas é inferência; sugerir novos testes é recomendação posterior.

## 7. Estratégia de testes

### Unitários e contratos

- requests rejeitam capability, path, versão e budget inválidos;
- observations não permitem `COMPLETED` sem resultado válido;
- estados incompletos não fabricam métricas;
- coverage JSON válido reconcilia linhas e branches exatos;
- percentuais combinados ou arredondados não substituem totais;
- JSON ausente, extra fields críticos, números negativos e totais incoerentes falham tipadamente;
- mutation reconcilia todos os estados nativos conhecidos;
- limite de mutantes e timeout produzem resultado parcial explícito;
- report JSON/Markdown concilia resultados e evidence refs;
- capability ausente aparece como `UNAVAILABLE`;
- core não importa coverage, mutmut, pytest ou adapters Python.

### Integração Docker

- imagem de qualidade é construída por lock com hashes;
- imagem é executada pelo image ID resolvido;
- coverage da fixture produz os totais congelados;
- mutation produz a matriz congelada dentro do budget;
- timeout remove o container e preserva evidência parcial válida;
- fonte original e fixture manifest mantêm hashes antes/depois;
- nenhum arquivo é criado no workspace read-only;
- container permanece sem rede, secrets, privilégios e Docker socket;
- output excessivo, traversal, symlink e artifact inesperado são bloqueados;
- mutmut funciona no container Linux sem depender de `fork` no host Windows.

### Regressão

- core mantém branch coverage mínima de 85%;
- Smoke Dataset permanece 20/20 sem executar mutation dez vezes;
- jobs existentes continuam verdes;
- mutation pilot do core continua independente;
- wheel sem extras continua instalável e demo continua keyless;
- source, wheel e reports passam no secret scan.

## 8. CI e evidência

Adicionar job `quality-capabilities`:

1. instalar o package e dependências de teste;
2. construir a imagem de qualidade pinada;
3. remover `OPENAI_API_KEY` do ambiente;
4. executar conformance de coverage;
5. executar a fixture mutation pequena com budget conhecido;
6. validar outputs nativos e normalizados;
7. comparar hashes do SUT/fixture antes e depois;
8. executar testes de timeout e capability ausente por doubles quando a prova real for excessivamente lenta;
9. passar secret scan nos reports;
10. publicar somente reports sanitizados com retenção curta.

O job não chama provider, não instala dependências durante o container e não aprova o Gate 5 automaticamente. O mutation pilot do core permanece agendado em workflow separado.

## 9. Fatias de implementação

1. **5.6.1 — Caracterização e contratos de execução:** observar mutmut pinado, documentar estados/comandos, definir requests/observations/budgets e decidir a extração estruturada. Parar se o limite de mutantes não puder ser aplicado honestamente.
2. **5.6.2 — Imagem e driver de qualidade:** lock com hashes, driver não interativo, resolução por image ID e hardening Docker.
3. **5.6.3 — Coverage:** adapter, JSON nativo, normalizador, fixture e testes de erro/timeout.
4. **5.6.4 — Mutation:** cópia descartável, admissão limitada, normalizador, estados parciais e fixture conhecida.
5. **5.6.5 — Orquestração e reports:** serviço de quality evaluation, persistência atômica, evidence refs, integração JSON/Markdown e perfil Python.
6. **5.6.6 — CI e revisão:** job próprio, baseline do SUT, regressão completa, wheel isolado, secret scan, documentação e parecer.

Cada fatia termina com testes próprios. Coverage deve ficar aprovado antes de mutation; falha na ferramenta mutation não bloqueia a entrega já correta de coverage, mas impede concluir G5-13 e o incremento 5.6 como um todo.

## 10. Critérios de aceite

O incremento somente pode ser aprovado quando:

1. coverage e mutation possuem portas neutras e adapters fora do core;
2. a imagem de qualidade usa base por digest, versões e hashes pinados;
3. coverage concilia exatamente linhas e branches com o JSON nativo;
4. mutation concilia todos os estados executados com a evidência nativa;
5. max mutants e timeout interrompem trabalho, não apenas o report;
6. timeout, inválido, parcial, falha e indisponibilidade são distinguíveis;
7. nenhum estado nativo é mapeado para categoria semanticamente falsa;
8. SUT e artifact originais mantêm hashes e permanecem read-only;
9. outputs nativos e normalizados possuem `EvidenceRef` verificável;
10. report JSON/Markdown apresenta métricas e limitações sem threshold universal;
11. falha de quality tooling não vira defeito do SUT nem reclassifica a execução funcional;
12. capability ausente é `UNAVAILABLE`, nunca zero ou sucesso silencioso;
13. perfil Python só declara `available` após conformance e integração aprovadas;
14. core continua sem imports de pytest, coverage, mutmut ou adapters Python;
15. Smoke permanece 20/20 e branch coverage do core permanece ao menos 85%;
16. CI `quality-capabilities` e jobs anteriores ficam verdes;
17. source, package e reports passam no secret scan;
18. baseline publica ferramenta, versão, scope, budgets, duração e limitações;
19. G5-12 e G5-13 recebem links para evidências reproduzíveis;
20. Lucas revisa o parecer e aprova a conclusão.

## 11. Critérios de parada

Interromper e revisar o desenho se:

- o SUT original precisar ficar gravável;
- mutation depender de `fork` ou tooling instalado no host Windows;
- o limite de mutantes só puder ser aplicado depois de executar todos;
- o normalizador depender apenas de texto humano instável sem conformance pinada;
- um estado nativo precisar ser rotulado falsamente para caber no contrato;
- coverage combinar linha e branch em um único número;
- ausência de capability virar zero, sucesso ou fallback no host;
- quality tooling alterar classificação funcional ou alegar defeito;
- o container precisar de rede, secret, privilégio ou Docker socket;
- o core passar a importar conceitos Python;
- o trabalho expandir para Security Dataset, outras linguagens ou threshold universal.

## 12. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Mutmut não oferece JSON público estável | caracterização pinada, exporter controlado e raw evidence; parar antes de parser frágil |
| Budget de mutantes não é aplicável | admission control comprovado; não aceitar truncamento pós-execução |
| Estado nativo não cabe no contrato | evolução aditiva ou observation `PARTIAL`, nunca mapeamento falso |
| Mutation deixa a CI lenta | fixture mínima, job próprio e budgets; pilot do core separado |
| Tooling modifica o SUT | mount read-only, cópia em tmpfs e hashes antes/depois |
| Imagem pytest fica pesada | imagem de qualidade separada |
| Coverage é interpretada como qualidade | linhas/branches separados e limitações obrigatórias |
| Score parcial parece completo | status, `not_run`, budget e limitações no mesmo report |
| Resultado muda com upgrade | versões pinadas e baseline congelada com revisão explícita |
| Adapter Python contamina o core | portas/resultados neutros e teste de import boundary |

## 13. Evidência esperada ao final

- tabela de caracterização do mutmut pinado;
- requests, observations e budgets versionados;
- imagem `python-quality` e lock com hashes;
- fixture de conformance e manifest de expectativas;
- outputs nativos e normalizados de coverage/mutation;
- baseline pequena do SUT de referência;
- report JSON/Markdown integrado;
- hashes antes/depois provando imutabilidade;
- prova de timeout, limite e capability ausente;
- job `quality-capabilities` verde;
- regressão completa, wheel isolado e secret scan;
- atualização de README, progresso, Gate 5, journal e notas editoriais quando houver material narrativo;
- revisão final do incremento 5.6.

## 14. Base técnica verificada no planejamento

O desenho usa o JSON oficial do coverage.py, que expõe totais separados para linhas e branches e permite escolher arquivo de saída. A documentação oficial também deixa claro que branch coverage amplia o denominador total, razão pela qual o adapter publicará os dois sinais separadamente.

Para mutmut, a documentação vigente confirma execução por `mutmut run`, configuração de `source_paths`/seleção pytest, filtro por linhas cobertas, armazenamento em `mutants/` e requisito de sistema com `fork`. Ela também marca os controles internos de timeout como instáveis. Por isso, o hard timeout pertence à policy do host e a extração/limitação da versão pinada será provada na fatia 5.6.1 antes do adapter definitivo.

Fontes oficiais consultadas no planejamento:

- [coverage.py — JSON reporting](https://coverage.readthedocs.io/en/latest/commands/cmd_json.html);
- [coverage.py — cálculo e campos de coverage](https://coverage.readthedocs.io/en/latest/faq.html#q-how-is-the-total-percentage-calculated);
- [mutmut — requisitos, execução e configuração](https://mutmut.readthedocs.io/en/latest/).
