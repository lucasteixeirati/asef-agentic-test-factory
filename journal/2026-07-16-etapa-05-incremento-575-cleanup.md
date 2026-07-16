# Relato — Incremento 5.7.5 retention e cleanup

- **Data:** 2026-07-16
- **Estado:** implementação e revisão local concluídas

Lucas autorizou a 5.7.5 após o fechamento do doctor. A fatia implementou policy versionada, `asef cleanup`, tombstones, apply condicionado por capability, cleanup observável de workspaces, debug allowlisted e scanner endurecido.

O principal limite não foi contornado: o Windows observado não sustenta apply recursivo resistente a links. Diretórios ficam planejados ou falham com diagnóstico explícito. Arquivos e containers podem ser removidos após revalidação; durante a revisão, apply ocorreu apenas em fixtures temporárias.

O dry-run real combinado encontrou um backup de log elegível e 13 targets recentes ou malformed, sem remover nada. Ele também demonstrou a diferença entre evidência nova com timestamp e artefatos legados que não podem ser selecionados com segurança.

Durante a revisão foram corrigidos root resolution prematuro, ID Docker curto, travessia de filesystem, overlap run/quality, Markdown injection e dois problemas no scanner. O sdist tar.gz passou a ser realmente aberto e erros de scan deixaram de ser silenciosos.

Security permaneceu 12/12, Smoke 20/20 e nenhum container ficou residual. A regressão descobriu 316 testes, aprovou 285 e ignorou 31 opcionais, com branch coverage de 85,16%. A 5.7.6 não foi iniciada.
