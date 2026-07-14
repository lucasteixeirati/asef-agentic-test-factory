# Relato — Etapa 5, incremento 5.3 em hardening

- **Data:** 2026-07-14
- **Incremento:** 5.3
- **Estado:** concluído, revisado e publicado como pré-alpha `0.1.0a2`

## Resultado observado

O fluxo interno agora combina execução pytest do artifact gerado com oracle curado e isolado. A decisão é determinística: erro do teste pode pedir correção, falha do oracle gera somente suspeita de defeito e exige humano, e evidência inconclusiva não é promovida a defeito.

Cada tentativa preserva artifact, stdout, stderr, resultado bruto, execução normalizada e avaliação. Teste gerado e oracle usam namespaces e workspaces separados. Uma evidência publicada não pode ser sobrescrita.

## Correção e revisão

O runtime permite no máximo duas correções. Feedback é sanitizado, limitado e recebe fingerprint; repetir o mesmo diagnóstico encerra cedo. Path, cenários e SUT não podem ser alterados pela correção. A chamada consome budget antes do provider, inclusive se o retorno for inválido.

A suspeita de defeito pausa em checkpoint. Repetir a mesma decisão humana reutiliza o resultado persistido sem executar novamente teste, oracle ou correção; uma decisão conflitante é bloqueada.

## Evidência Docker

Docker Desktop e a imagem pytest pinada estavam disponíveis. As 14 integrações existentes executaram com 13 aprovações e um skip causado pela falta de privilégio local para criar symlink no Windows. Uma integração adicional do 5.3 executou teste gerado e oracle em containers reais, workspaces distintos e read-only, terminando em `ACCEPTED` com evidências separadas.

## Findings da revisão e correções

A primeira revisão rejeitou provisoriamente o incremento. Foram corrigidos: persistência dos artifacts de correção, reserva de budget antes do provider, normalização de falhas parciais, cleanup dos workspaces, evolução do estado para `1.2.0`, identidade imutável do oracle e semântica do tipo de checkpoint.

O hardening revelou ainda uma diferença LF/CRLF no Windows. Artifacts e oracle passaram a ser persistidos como bytes UTF-8, garantindo que o SHA-256 publicado corresponda ao conteúdo real.

Após as correções, o core executou 178 testes com 88% de branch coverage; o workflow opcional passou 18/18; e Docker passou 14 de 15 testes, com um skip conhecido por privilégio de symlink no host Windows.

## Publicação e limite da conclusão

O commit funcional `1cf687f` foi publicado e a execução pública `29360824309` aprovou os jobs `core`, `framework-spikes` e `docker-security`. Wheel e sdist passaram por auditoria, secret scan e instalação limpa; a demo keyless terminou em `SUCCEEDED/ACCEPTED`.

O incremento foi encerrado como pré-alpha `0.1.0a2`. O novo código ainda não é o fluxo padrão da CLI, e a publicação não amplia a alegação de segurança para código hostil ou uso em produção.
