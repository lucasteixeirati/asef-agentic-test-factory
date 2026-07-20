# Tutorial — Java/JUnit local e revisável

Este tutorial usa somente a fixture Calculator empacotada, o cassette gravado e a
imagem local `asef/java-junit:21.0.11`. Não usa provider, rede na execução, projeto
externo ou credencial.

## 1. Preparar a imagem

```powershell
docker build -t asef/java-junit:21.0.11 tooling/java-junit
```

A base Maven é pinada por digest e o build materializa o cache usado por
`mvn --offline`. Construir a imagem pode acessar o Maven Central; a run não acessa.

## 2. Gerar um plano

```powershell
asef java-generate --requirement "Teste soma e divisão por zero da Calculator"
```

O resultado informa `run_id`, caminho do plano e `WAITING_FOR_HUMAN_REVIEW`. Abra o
JSON e confirme operações, argumentos e oracles. Nada foi executado nessa etapa.

## 3. Aprovar e executar

```powershell
asef java --run-id <RUN_ID>
```

Informar o `run_id` é a aprovação explícita do plano preservado por SHA-256. O ASEF
compila JUnit determinístico, executa Maven offline no container e retorna contadores
normalizados. A run contém `state.json`, `manifest.json`, plano, resultado e XML
Surefire.

## Interpretação

- `PASSED` / exit `0`: todos os oracles revisados passaram;
- `ASSERTION_FAILURE` / exit `4`: a automação encontrou divergência funcional;
- exit `2`: input, plano, hash, policy ou contexto inválido;
- exit `6`: budget esgotado;
- exit `7`: Maven, compilação, sandbox, timeout ou evidência nativa inválida.

Não edite a run após a geração: qualquer divergência de hash bloqueia a execução.
Não use este caminho para Gradle, Kotlin, Spring, Android, dependências próprias ou
Java arbitrário; esses casos estão fora do contrato atual.
