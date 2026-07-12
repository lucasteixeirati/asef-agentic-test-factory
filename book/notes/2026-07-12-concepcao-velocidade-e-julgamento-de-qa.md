# Nota contemporânea — Concepção, velocidade e julgamento de QA

- **Data:** 2026-07-12
- **Dia do projeto:** Dia 2
- **Natureza:** reflexão contemporânea baseada no relato do autor e nas evidências disponíveis
- **Estado editorial:** matéria-prima; não é capítulo concluído

## De uma fábrica do SDLC para Quality Engineering

A ideia inicialmente explorada com Gemini Pro era uma ferramenta agêntica capaz de automatizar todo o ciclo de desenvolvimento de software. O escopo era amplo e atraente, mas, conforme o autor compreendeu melhor as implicações da proposta, sua experiência de 15 anos em qualidade de software passou a funcionar como filtro.

O projeto foi então redirecionado para a disciplina de Quality Engineering. A mudança não representou apenas uma redução de escopo. Ela aproximou a ideia de problemas que o autor conhece no trabalho cotidiano, preservou espaço para técnicas modernas e criou uma narrativa profissional mais coerente: demonstrar como um especialista em qualidade projeta, testa e governa uma fábrica de testes agêntica.

## IA como aceleradora, não como autoridade

O desenvolvimento passou a usar GPT-5.6 Sol no ChatGPT/Codex. Até este registro, o autor estima aproximadamente 10 horas de uso e 150 interações. Esses números são retrospectivos e aproximados; servem como baseline inicial, não como telemetria precisa.

As primeiras estimativas geradas pela IA apontavam semanas de desenvolvimento. No segundo dia, o projeto já havia concluído os dois primeiros gates e estava próximo de completar os experimentos da Etapa 3. O impacto percebido na velocidade é muito alto, embora ainda não exista um percentual calculável.

Essa velocidade precisa ser interpretada com rigor. Foram acelerados planejamento, documentação, implementação experimental e feedback automatizado. Ainda não foram concluídos o walking skeleton, os alphas, a validação multilíngue, a experiência com usuários externos, o hardening e a versão pública robusta. A velocidade dos primeiros artefatos não pode ser extrapolada automaticamente para o tempo de maturação do produto.

## O olhar de QA sobre a colaboração

A experiência profissional influenciou as decisões ao permitir comparar as propostas da IA com o cotidiano real de QA e com tendências atuais do mercado. O autor não apenas revisou código: revisou premissas, utilidade, fronteiras de segurança, critérios de evidência e o próprio posicionamento do projeto.

Isso sugere uma tese importante para o livro: no desenvolvimento assistido por IA, Quality Engineering pode ser aplicado também ao processo de colaboração. Sugestões da IA tornam-se hipóteses; implementações tornam-se objetos de teste; afirmações de sucesso exigem evidências; e a decisão final continua humana.

## Fricção também é evidência

Durante a jornada surgiram dúvidas sobre tokens, reasoning, limites de uso e janela de contexto. A própria IA foi usada para esclarecer essas questões. A situação mostra uma característica circular dessa forma de trabalho: a ferramenta participa do desenvolvimento e também ajuda o profissional a compreender os limites da colaboração.

Outra fricção é documental. Quanto mais rapidamente a IA produz código e texto, maior é o risco de registrar apenas resultados técnicos e perder percepções humanas contemporâneas. Esta nota foi criada para corrigir essa lacuna antes que a narrativa precise ser reconstruída de memória.

## Hipóteses editoriais a acompanhar

- A aceleração permanecerá quando o projeto entrar em integração, segurança e avaliação externa?
- A quantidade de retrabalho crescerá conforme a arquitetura deixar de ser um spike?
- O uso de IA reduzirá tempo total ou deslocará esforço para revisão e validação?
- Quais sugestões serão rejeitadas graças à experiência profissional do autor?
- A percepção de velocidade será confirmada pelos dias por entregável registrados ao final dos próximos gates?

Essas perguntas permanecem abertas e não devem receber respostas retrospectivas fabricadas.

## Adendo — testar a correção da própria IA

O experimento de structured output mostrou que não basta validar a primeira resposta. Também é necessário testar o mecanismo que pede à IA para corrigir sua resposta. O runtime passou a limitar novas tentativas, registrar cada falha e encerrar a execução quando o budget termina.

Uma primeira implementação cobria apenas erros detectados depois que o gateway retornava. A revisão dos testes revelou que frameworks também podem rejeitar a saída internamente. A política foi então ampliada para tratar as duas origens de modo uniforme. Esse episódio ilustra como o olhar de QA encontra riscos não apenas no caminho principal, mas também no mecanismo de recuperação criado para torná-lo confiável.
