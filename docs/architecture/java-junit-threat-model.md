# Threat model — Java 21, Maven e JUnit 5

**Escopo:** fixture `JAVA-CALCULATOR-001` e workflow unitário Java do incremento
6.5. Não constitui suporte geral a projetos Maven ou código Java externo.

## Ativos e fronteiras

Os ativos protegidos são o host, o daemon Docker, o checkout, os planos revisados,
os artefatos JUnit compilados, os relatórios Surefire e a rastreabilidade da run. O
plano vindo do agente é entrada não confiável. O compilador e o runtime ASEF são a
autoridade para package, imports, nomes, paths, POM, comando Maven, imagem e budgets.
O container é uma fronteira de redução de impacto, não uma fronteira contra daemon
ou kernel comprometidos.

## Ameaças e controles

| Ameaça | Controle obrigatório | Falha esperada |
|---|---|---|
| Java, script, import, path ou comando injetado pelo modelo | schema fechado e compilador determinístico | rejeição antes do staging |
| segredo persistido no plano ou diagnóstico | policy de marcadores sensíveis e sanitização | erro de política sem ecoar valor |
| overflow ambíguo ou boolean/float tratado como inteiro | inteiros `int32`, tipos exatos e operações sem overflow | erro de contrato |
| POM troca dependência, plugin, repositório ou versão | detector XML estrito; DOCTYPE/ENTITY proibidos | projeto não suportado |
| symlink escapa da fixture | arquivos regulares, paths fixos e hashes no manifest | staging recusado |
| download, exfiltração ou alvo externo durante teste | cache preparado no build e `--network none` | falha de infraestrutura/toolchain |
| escrita no checkout ou na imagem | workspace/rootfs read-only; cópia descartável em tmpfs | controle de isolamento falha |
| escalada no container | UID/GID não-root, capabilities removidas e `no-new-privileges` | probe falha fechado |
| XML Surefire ausente, enorme, duplicado ou adulterado | allowlist, limites, parser estrito e reconciliação | resultado inválido, nunca sucesso |
| stdout forjado como resultado | Surefire XML é evidência nativa autoritativa | stdout apenas diagnóstico delimitado |
| execução antes da revisão | checkpoint humano persistido e hash do plano | estado `WAITING_FOR_HUMAN_REVIEW` |
| dependência/cache alterado entre runs | imagem por ID e versões/digest documentados | identidade divergente |

## Dados permitidos e proibidos

O plano aceita somente descrição pública, IDs, uma de quatro operações, dois
inteiros e um oracle inteiro ou `ArithmeticException` para divisão por zero. Não
aceita source, classpath, reflection, filesystem, rede, environment, credenciais,
Maven settings, argumentos JVM, dependências ou repositórios.

São publicáveis: plano sanitizado, hashes, versões, contadores, duração delimitada e
diagnósticos allowlisted. Source gerado e XML podem compor evidência local, mas não
devem conter paths absolutos do host, variáveis de ambiente ou conteúdo secreto.

## Hipóteses e limites

- Docker Desktop, daemon, host e kernel são confiáveis.
- A fixture versionada e o toolchain construído são inspecionáveis; cadeia de
  suprimentos completa não é alegada.
- A dependência JUnit existe no cache da imagem, mas nenhuma resolução externa é
  permitida durante uma run.
- O incremento não recebe repositórios reais do usuário nem executa Java arbitrário.
- Gradle, Kotlin, Spring, Android, API Java e plugins Maven adicionais permanecem fora.

Qualquer relaxamento de rede, projeto, dependência, comando ou geração de source
livre exige novo threat model e validação humana; não pode ser inferido deste escopo.
