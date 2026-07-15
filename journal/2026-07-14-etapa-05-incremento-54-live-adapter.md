# Relato — Etapa 5, incremento 5.4

- **Data:** 2026-07-14
- **Estado:** concluído localmente; candidata `0.1.0a3` em fechamento

O gateway OpenAI do spike não implementava as portas públicas e mantinha budget próprio do legado. O 5.4 separou transporte de autoridade: a aplicação reserva e persiste cada chamada, enquanto o adapter traduz análise, geração e correção para Structured Outputs.

A documentação oficial vigente confirmou `text.format` com JSON Schema estrito na Responses API. O transporte passou a usar `store: false`, erros tipados e ausência de detalhes remotos potencialmente sensíveis nas mensagens persistidas.

Na primeira revisão, foi encontrada uma lacuna: o modelo recebia o requisito, mas não o SUT autorizado. O adapter passou a vincular exclusivamente arquivos concretos do `read_scope`, com resolução de path, limite total e bloqueio de marcadores sensíveis antes do provider.

O smoke real permanece manual porque implica rede, credencial e custo. A evidência automática usa transporte falso e prova schemas, CLI live, retry central, reserva anterior à chamada, custo excedido, cassette sanitizado e bloqueio pré-provider.

Após o hardening inicial, o core descobriu 194 testes: 170 passaram e 24 ficaram opt-in, com 86% de branch coverage. Na revisão de versão, as regressões de budget elevaram o total para 199 testes: 183 passaram e 16 ficaram opt-in, com 87% de branch coverage. Os 18 testes opcionais de workflow/framework passaram. Docker aprovou 14 de 15 integrações, com o mesmo skip local de symlink por privilégio do Windows. Secret scan e integridade do diff passaram.

Após autorização explícita, foi executada uma única chamada real com teto de R$ 0,10 e 300 tokens de saída. O provider retornou `gpt-5.4-2026-03-05`; foram consumidos 194 tokens de entrada e 138 de saída, com latência de 4.515 ms e custo estimado de R$ 0,01533. O teste passou na primeira chamada, sem retry. Nenhuma credencial, prompt integral ou conteúdo retornado foi registrado na evidência pública.

Na revisão de fechamento foi encontrado um bypass de budget por valores monetários não finitos (`NaN`/`Infinity`). A correção passou a rejeitar esses valores no contrato, gateway e configuração live antes de qualquer transporte, além de revalidar o requisito em cada operação pública do adapter. As regressões dedicadas passaram.

Com esse smoke e as verificações automáticas aprovadas, o incremento 5.4 foi aceito para a candidata pré-alpha `0.1.0a3`. O empacotamento e a instalação limpa foram aprovados; restam commit, CI pública, tag e release no GitHub.
