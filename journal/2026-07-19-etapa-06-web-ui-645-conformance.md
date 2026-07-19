# Etapa 6.4.5 — conformance e hardening de Web UI

Data: 2026-07-19

## Escopo

Foi criado o dataset versionado `WEB-UI-CONFORMANCE-001` com 14 controles:
leitura, mutação resetável, seletor semântico, divergência, timeout, navegação
externa, request externo, popup, dialog, download, secret, adulteração, screenshot
privado e budget de requests.

Os nove casos que exigem navegador foram executados em Chromium real, em container
não-root, root filesystem somente leitura e `--network none`. Cada caso foi repetido
duas vezes. O fingerprint funcional exclui somente duração e nome do screenshot
privado; status, contadores, diagnóstico, passo e presença de evidência permanecem
no oracle.

## Finding e correção

A primeira execução adversarial revelou uma janela de evento no popup: a criação da
nova página podia ser entregue logo após a resolução do click e, por isso, aparecer
como falha funcional posterior. O driver ganhou uma drenagem pós-click limitada a
100 ms antes de aceitar a ação. A matriz completa foi reconstruída e repetida após
a correção, sem divergência de fingerprint.

## Limites preservados

- `conformance.html` é uma página adversarial separada; a fixture principal não a referencia;
- o endereço externo é `192.0.2.1`, reservado para documentação, e a route é abortada antes do transporte;
- a rede Docker permanece desabilitada, inclusive nos casos adversariais;
- screenshots existem somente em falha e continuam não publicáveis por padrão;
- navegação externa, secret, adulteração e budget são bloqueados antes do browser/container;
- nenhum finding alto ou crítico permaneceu aberto nesta fatia.
