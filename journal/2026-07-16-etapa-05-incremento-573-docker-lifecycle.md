# Relato — Incremento 5.7.3 hardening Docker

- **Data:** 2026-07-16
- **Estado:** implementação e revisão local concluídas

Lucas autorizou a 5.7.3 após o fechamento do Security Dataset. O trabalho endureceu o ciclo de vida comum sem ampliar a autoridade dos manifests: labels, imagem, mounts, budgets e comandos continuam definidos pelo package.

O `DockerRunner` passou a identificar cada container por labels ASEF e a produzir uma observação própria de cleanup. Timeout, interrupção e exceção tentam remoção forçada; execução normal também verifica que o container desapareceu. Uma saída funcional zero não apaga uma falha de inspeção ou um residual.

A detecção de órfãos usa labels exatos de ownership e capability. Os sete executores Docker da Security Suite exigem cleanup confirmado e registram `managed_residual_count: 0`. SEC-011 também verifica que o argv não monta o socket Docker e contém os labels esperados.

A prova real `security-20260716T132831Z-b165d7fe` terminou 12/12, com hash estável e nenhuma sobra por labels. A regressão descobriu 290 testes, aprovou 261 e ignorou 29 opcionais; branch coverage ficou em 85,64%. Compilação, integridade do diff e secret scans do source e da evidência passaram.

Com a revisão verde, a 5.7.3 foi aprovada localmente. Doctor, cleanup de arquivos e CI não foram iniciados.
