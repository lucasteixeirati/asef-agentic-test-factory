# Relato — incremento 5.8.3 jornada pública

- **Data:** 2026-07-17
- **Estado:** concluída e aprovada localmente
- **Dependência:** revisão 5.8.2 aprovada por Lucas

Lucas aprovou a revisão da 5.8.2 e autorizou exclusivamente a jornada pública da 5.8.3. O README foi reduzido a uma entrada de cinco minutos e passou a separar claramente a última release publicada `v0.1.0a5` do contrato/report 5.8 ainda local.

Foram criados quickstart instalado, tutorial demo WF-001, tutorial live, interpretação do report e troubleshooting. A escrita foi confrontada com `--help`, outcomes, schema, renderer e paths reais do CLI. O demo não alega usar o oracle combinado do 5.3; o live não fixa modelo, tarifa, preço ou câmbio e exige secret no host, budget e autorização. O troubleshooting começa por exit/classification/doctor e não recomenda prune amplo, desabilitar controles ou executar código gerado no host.

A auditoria aprovou links locais dos seis documentos, existência de assets referenciados, secret scan, `git diff --check` e regressão de 337 testes com 33 skips opcionais e branch coverage de 85,34%. Nenhum código de produto, commit, push, CI, versão ou release foi criado nesta fatia. Arquitetura e contribuição permanecem reservadas à 5.8.4.
