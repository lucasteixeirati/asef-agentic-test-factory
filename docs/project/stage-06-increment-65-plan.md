# Plano detalhado do incremento 6.5 — Java 21, Maven e JUnit 5

**Status:** aprovado por delegação para execução local dentro da Etapa 6; promoção
documental permanece reservada à validação humana final do Gate 6.

## Objetivo

Provar o workflow unitário equivalente em um segundo ecossistema: uma intenção em
linguagem natural produz casos tipados e revisáveis; um compilador determinístico
gera JUnit 5; após o checkpoint, Maven executa uma fixture Java 21 em Docker sem rede
e o ASEF devolve resultado normalizado e evidências reconciliadas.

## Escopo inicial

- Java 21, Maven e JUnit Jupiter;
- projeto Maven fictício pequeno e imutável;
- detecção estrita de `pom.xml` e layout `src/main/java`;
- operações públicas e determinísticas da fixture `Calculator`;
- geração por cassette antes de qualquer provider live;
- Surefire XML nativo como evidência de execução;
- imagem/toolchain dedicada, pinada e preparada antes da run;
- rede desligada, usuário não-root, workspace read-only e output separado.

Gradle, Kotlin, Spring, Android, banco, API Java, projetos externos, dependências
fornecidas pelo usuário, reflection livre, scripts e execução no host ficam fora do
incremento.

## Decisões de arquitetura

1. O modelo não gera Java livre. Ele propõe `JavaUnitTestPlan` declarativo, com
   vocabulário fechado de operação, argumentos e oracle.
2. Origem, package, classe, imports, nome do teste, versão de Java/JUnit/Surefire,
   POM, argv e imagem são definidos pelo runtime.
3. `JavaUnitTestCompiler` transforma o plano revisado em uma única classe JUnit 5
   determinística e registra bytes/SHA-256.
4. Maven executa offline. Dependências e plugins são materializados durante o build
   da imagem, nunca durante a run.
5. Surefire XML é copiado para o output e normalizado para o contrato neutro já usado
   pela execução de testes; stdout/stderr não decidem sozinhos os contadores.
6. O envelope genérico de capability run poderá ser reutilizado, mas contratos Java,
   compilador, parser Maven e staging permanecem nos adapters da capacidade.

## Contrato declarativo inicial

Cada cenário declara:

- ID e descrição pública delimitada;
- operação fechada: `add`, `subtract`, `multiply` ou `divide`;
- dois argumentos inteiros de 32 bits;
- oracle: inteiro esperado ou exceção `ArithmeticException`;
- nenhum código, path, package, import, comando, dependência ou configuração Maven.

O plano limita quantidade de cenários, tamanho, IDs, valores e duplicidade. Secrets,
campos desconhecidos, floats, booleanos como inteiros e texto de controle falham
antes da compilação.

## Toolchain e sandbox

- base oficial Maven 3.9.x com Eclipse Temurin 21 por digest;
- JUnit Jupiter e Surefire em versões exatas;
- driver de comandos fechados `version`, `probe` e `run`;
- `mvn --offline --batch-mode --no-transfer-progress test`;
- nenhum settings.xml, mirror, proxy, credential ou repositório externo na run;
- `--network none`, rootfs/workspace read-only, capabilities removidas, UID/GID não
  privilegiado, CPU/memória/PIDs/tempo limitados;
- árvore de trabalho descartável sob tmpfs e somente reports/resultados allowlisted
  copiados ao output;
- imagem resolvida para image ID antes da execução.

## Fatias

### 6.5.1 — contratos, fixture, detecção e threat model

**Status em 19/07/2026:** concluída localmente. Contrato declarativo, parser estrito,
política anti-secrets, limites de overflow, detector Maven fechado, fixture Java 21,
manifest por hash e threat model foram implementados e cobertos por testes.

**Entrega:** plano/resultado estritos, parser, política, fixture Maven e ameaças Java.

**Aceite:** entradas ambíguas, scripts, secrets, paths, operações e budgets fora do
vocabulário falham fechados; fixture não possui dependência operacional externa.

### 6.5.2 — toolchain Maven/JUnit reproduzível

**Status em 19/07/2026:** concluída localmente. A imagem dedicada usa a base Maven
3.9.16/Temurin 21 por digest, Java 21.0.11, JUnit 5.13.4, compiler 3.14.1 e Surefire
3.5.5 estável. O cache foi materializado no build; o probe real passou como UID/GID
65534, rede desligada, rootfs/workspace read-only e Maven apto a operar offline.

**Entrega:** imagem por digest, versões pinadas, cache offline, driver fechado e probe.

**Aceite:** Java/Maven iniciam como não-root; dependências resolvem offline; rede,
rootfs e workspace estão fechados; output e budgets são delimitados.

### 6.5.3 — compilador e execução normalizada

**Entrega:** Java determinístico, staging, Surefire XML, resultado neutro e integridade.

**Aceite:** positivo passa; assertion falha funcionalmente; compilação/infraestrutura,
timeout, ausência de testes, tamper e identidade divergente permanecem distintos.

### 6.5.4 — linguagem natural, run e revisão

**Entrega:** `java-generate` por cassette, plano persistido por hash e `java --run-id`
após checkpoint; live permanece não chamado até prova separada futura.

**Aceite:** run nasce antes da geração, usage/budgets são preservados, nenhuma
execução precede revisão e artifact reconcilia com o plano.

### 6.5.5 — conformance e equivalência

**Entrega:** dataset positivo/negativo/adversarial, repetição e comparação factual com
o workflow unitário Python e a compilação TypeScript já observada.

**Aceite:** fingerprints funcionais estáveis; nenhum caso usa rede; o core não ganha
imports ou branches de Maven/JUnit/Java.

### 6.5.6 — documentação e experiência instalada

**Entrega:** tutorial, arquitetura, matriz, limitações, journal, livro, wheel/sdist e
revisão local.

**Aceite:** wheel instalado fora do checkout gera, permite revisão e executa a fixture
com material público; regressão, cobertura >=85%, docs, scanner e Docker passam.

## Critério de promoção

Somente `unit` poderá tornar-se `partial` dentro de `java-junit`, e o perfil poderá
tornar-se `experimental`, após todas as provas e a validação humana final do Gate 6.
Isso não cria suporte geral a Maven, Java, Kotlin, Spring, Gradle ou projetos reais.

## Bloqueadores

- dependência baixada durante a run;
- Java/comando/path livre originado do modelo;
- workspace fonte gravável ou rede habilitada;
- parsing de stdout como oracle principal quando Surefire XML deveria existir;
- finding alto/crítico aberto;
- promoção, push, tag, release ou provider live antes da validação final.
