# Contratos de capabilities, skills e perfis

## Princípios

- contratos não dependem de SDK de provider ou framework agêntico;
- inputs e outputs são schemas do core;
- capability não decide a próxima transição do workflow;
- efeitos colaterais são declarados;
- toda operação recebe contexto de run, policy e budget;
- erros são tipados e normalizados.

## Contratos do workspace

### `WorkspaceReader`

- **Entrada:** raiz autorizada, allowlist, exclusões e limites.
- **Saída:** manifest de arquivos, hashes e conteúdo permitido por referência.
- **Efeitos:** somente leitura.
- **Erros:** path escape, arquivo proibido, limite excedido.

### `ArtifactWriter`

- **Entrada:** caminho relativo seguro, conteúdo e metadados.
- **Saída:** `GeneratedArtifact`.
- **Efeitos:** escrita somente no workspace de tentativa.
- **Erros:** path escape, tamanho excedido, tipo proibido.

## Contratos de linguagem e tooling

### `ProjectDetector`

- detecta perfis candidatos e evidências;
- não escolhe silenciosamente quando houver ambiguidade;
- retorna nível de confiança explicável e conflitos.

### `DependencyManager`

- valida lockfile e allowlist;
- prepara dependências apenas por política explícita;
- não possui rede por padrão;
- retorna inventário e hashes.

### `BuildAdapter`

- valida ou compila o projeto;
- retorna resultado normalizado, logs limitados e artefatos;
- respeita cancelamento e timeout.

### `StaticAnalysisAdapter`

- executa verificações configuradas;
- normaliza finding, severidade, arquivo e localização;
- distingue erro da ferramenta de finding no código.

### `TestRunnerAdapter`

- descobre e executa testes permitidos;
- retorna `ExecutionResult` normalizado;
- não interpreta semanticamente um defeito no SUT.

### `CoverageAdapter`

- coleta cobertura no escopo autorizado;
- informa métrica, unidade, arquivos considerados e limitações;
- não converte cobertura em qualidade automaticamente.

### `MutationAdapter`

- cria e executa mutantes dentro de budget próprio;
- retorna mutantes mortos, sobreviventes, inválidos e timeout;
- preserva a localização e o operador de mutação.

### `ResultNormalizer`

- converte saída nativa para schemas do core;
- mantém referência ao resultado bruto;
- falha explicitamente quando não puder normalizar.

## `LanguageProfile`

Um perfil declara:

- identificador, versão e nível de suporte;
- detectores e capabilities disponíveis;
- imagem de container por digest;
- arquivos de projeto e lockfiles reconhecidos;
- comandos permitidos por capability;
- formatos de resultado;
- limites e incompatibilidades;
- conformance suite aplicável.

Nenhum perfil precisa implementar capability opcional, mas deve declarar sua ausência.

## Contratos de modelo

### `ModelGateway`

- recebe prompt versionado, schema esperado, configuração e budget;
- retorna structured output ou erro tipado;
- registra provider, modelo, parâmetros, uso e latência;
- secrets são resolvidos fora do estado persistido;
- retries são comandados pelo runtime.

### `RecordedModelGateway`

- reproduz respostas gravadas por chave de cassette;
- não realiza rede;
- valida versão do prompt e schema;
- falha quando a gravação não corresponde ao request.

## Contratos de sandbox

### `SandboxRunner`

- cria container efêmero pelo perfil e política;
- aplica mounts, rede, usuário, recursos e timeout;
- executa comando previamente autorizado;
- captura resultado limitado;
- remove recursos ao final;
- nunca monta o socket do Docker ou secrets do provider.

## Contratos de evidência

### `EventSink`

- grava eventos append-only por run;
- assegura identificador, correlação e versão do schema;
- não aceita evento sem sanitização declarada.

### `ArtifactStore`

- armazena conteúdo por hash;
- retorna referência imutável;
- aplica política de retenção e publicação.

## Taxonomia de erros

- `ValidationError`;
- `PolicyViolation`;
- `BudgetExceeded`;
- `CapabilityUnavailable`;
- `ToolExecutionError`;
- `InfrastructureError`;
- `ProviderTransientError`;
- `ProviderPermanentError`;
- `NormalizationError`;
- `HumanDecisionRequired`.

Erros não previstos sobem como falha interna, sem serem automaticamente apresentados como defeito do SUT.

