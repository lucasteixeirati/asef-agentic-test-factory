# Política de retenção local

- **Policy ID:** `asef-local-retention`
- **Versão:** `1.0.0`
- **Schema:** `1.0.0`

| Classe | Regra |
|---|---|
| recursos efêmeros | remoção imediata observável |
| evidência final | somente cleanup explícito |
| logs operacionais | rotação de 1 MiB com dois backups; cleanup explícito por idade |
| cassettes live | locais, explícitos e não publicáveis automaticamente |
| reports de CI | sete dias, somente sanitizados |
| debug | evidência sanitizada; nunca workspace, environment, prompt ou resposta bruta |
| tombstones | preservação explícita e fora do próprio ciclo de cleanup |

`asef cleanup` é dry-run por padrão, possui raiz fixa `.asef` e exige `--apply` para mutação. Idade vem de timestamp/manifest validado. Targets desconhecidos, malformed, linkados ou com identidade alterada são ignorados ou falham sem heurística destrutiva.

No perfil Windows caracterizado, diretórios não são removidos por `--apply`, pois as primitivas disponíveis não sustentam a alegação de remoção recursiva resistente a links. Arquivos regulares elegíveis podem ser removidos após revalidação; containers exigem label ASEF, idade validada e ID exato. A prova recursiva Linux pertence à CI da 5.7.6.

Bytes liberados são estimativas. A política não promete secure erase, backup, imutabilidade ou recuperação.
