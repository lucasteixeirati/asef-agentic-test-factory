# Journal — Etapa 5.2: pytest e resultado estruturado

- **Data:** 2026-07-13
- **Incremento:** 5.2
- **Participantes:** Lucas e GPT-5.6 Sol
- **Estado:** concluído e publicado

## Intenção

Substituir interpretação frágil de texto do runner por evidência estruturada do pytest, mantendo a ferramenta fora do core e sem conceder escrita sobre o SUT.

## O que foi construído

O adapter executa pytest 8.3.3 em uma imagem derivada e sem rede. O JUnit XML nativo é normalizado em outcomes neutros: pass, assertion failure, test error, no tests, tool error e infraestrutura. stdout, stderr e JUnit permanecem evidências distintas.

O workspace é montado read-only. Um arquivo de saída vazio e controlado é criado em diretório irmão, montado separadamente e removido depois da captura. Validações impedem que esse mount seja o próprio workspace, um descendente, um ancestral ou um path fora da raiz autorizada.

## Supply chain

A imagem base continua fixada por digest. Pytest e suas dependências diretas possuem versão e SHA-256 pinados. A CI constrói a imagem; o adapter resolve o tag para um image ID imutável e executa pelo ID, registrando-o no resultado.

Isso ainda não equivale a distribuição pública da imagem. A CLI não foi migrada silenciosamente e o perfil permanece parcial.

## Falhas e aprendizado

Um teste de contrato inicialmente esperava a mensagem da nova regra de reconciliação, mas seus dados violavam primeiro uma regra antiga. O produto rejeitou corretamente o resultado; o teste foi reformulado para exercitar uma propriedade por vez.

O desenho inicial pinava versões do toolchain, porém não hashes. A revisão adicionou `--require-hashes`, mostrando que “reproduzível” precisa incluir também a identidade do artefato baixado.

## Evidência

- adapter/parser: 7/7;
- pytest Docker: 3/3;
- Docker/security: 14/14;
- core: 147 descobertos, 125 aprovados, 22 opt-in;
- coverage geral 88% e adapter 93%.

## Reflexão para o livro

O incremento exemplifica um padrão de QA: um canal de evidência exige sua própria superfície de segurança. Tornar o resultado estruturado não deveria transformar o diretório de resultados em um caminho alternativo para modificar o SUT. Também mostra que exit code e causa não são sinônimos; a normalização deve preservar fatos antes da interpretação agêntica.

A revisão final tornou explícita outra diferença importante: `pytest` pode encerrar com sucesso mesmo contendo testes ignorados. O adapter preserva esse fato como `PASSED`, mas o workflow não aceita uma suíte gerada incompleta. Separar sucesso da ferramenta de aceitação do produto evita que uma automação aparentemente verde esconda ausência de verificação.

## Decisão humana e próximo passo

Lucas aprovou explicitamente o incremento 5.2 em 2026-07-13. A publicação e a confirmação dos três jobs da CI pública autorizaram o planejamento do 5.3, que poderá combinar essa evidência com o oracle independente e aplicar correção limitada.

O commit `7d549a8` foi publicado. A execução pública `29287409883` aprovou `core`, `docker-security` e `framework-spikes`. Além da regressão e da varredura de segredos, a CI Linux construiu a imagem pytest pinada, executou as 14 integrações Docker, instalou o package e confirmou a demo sem chave fora do checkout. O 5.2 está encerrado; somente o planejamento detalhado do 5.3 fica autorizado neste momento.
