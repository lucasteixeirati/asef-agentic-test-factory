# Toolchain Java/JUnit

Constrói a imagem dedicada com Maven/JUnit pré-carregados:

```text
docker build -t asef/java-junit:21.0.11 tooling/java-junit
```

O driver aceita somente `version`, `probe` e `run`. A execução ASEF resolve a tag
para image ID e sempre aplica rede desligada, rootfs/workspace read-only, UID/GID
65534, capabilities removidas, `no-new-privileges` e budgets. `run` usa Maven
`--offline` e copia somente XML Surefire para o output separado.
