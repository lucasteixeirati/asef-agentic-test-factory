# Tutorial — WF-001 live com budget explícito

Leia primeiro a fonte canônica de [suporte e limitações](../project/support-and-limitations.md).

O modo live é experimental, variável e opt-in. Ele chama um provider real para análise/geração; pode consumir dinheiro e falhar por disponibilidade, modelo, rate limit, rede ou mudança externa. O caminho demo é a referência offline e deve ser executado primeiro.

## Pré-condições

- quickstart demo concluído;
- contexto live fictício revisado;
- modelo atualmente disponível para sua conta;
- tarifas atuais de input/output obtidas pelo operador;
- teto em BRL que você aceita consumir;
- autorização para enviar o requisito e o contexto permitido ao provider.

O repositório não congela preço, câmbio ou disponibilidade de modelo. Não copie valores antigos de exemplos sem verificá-los.

## Secret somente no host

Defina a credencial apenas na sessão do PowerShell:

```powershell
$secureKey = Read-Host "Provider API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
Remove-Variable secureKey
```

Não passe a chave como argumento, não a grave em `.env`, cassette, contexto, journal, report ou screenshot. O ASEF publica somente a presença booleana da chave nos diagnósticos live.

Ao terminar:

```powershell
Remove-Item Env:OPENAI_API_KEY
```

## Diagnóstico live

```powershell
asef doctor `
  --mode live `
  --context examples/context/walking-skeleton-live-context.example.json `
  --output .asef/doctor
```

O doctor verifica pré-condições locais, mas não prova disponibilidade futura do provider e não faz chamada paga.

## Geração mínima

Substitua modelo e tarifas por valores verificados no momento da execução:

```powershell
asef generate `
  --mode live `
  --context examples/context/walking-skeleton-live-context.example.json `
  --model MODEL_AVAILABLE_TO_OPERATOR `
  --api-budget-brl 1.00 `
  --input-cost-brl-per-million INPUT_RATE_BRL `
  --output-cost-brl-per-million OUTPUT_RATE_BRL `
  --provider-timeout-seconds 60 `
  --max-output-tokens 600
```

`generate` para após geração, static validation e staging; não executa o teste no Docker. Use `run` com os mesmos controles somente quando quiser também executar o artifact no sandbox local.

O budget precisa ser positivo. Limites de chamadas, retries, tokens, tempo e custo continuam hard stops do runtime; recommendation no report não aumenta budget automaticamente.

## Custo estimado e custo real

O state registra tokens observados e custo estimado a partir das tarifas fornecidas; quando a operação emite report terminal, esses valores também aparecem nele. Isso não é fatura do provider. Compare depois com o painel/fatura oficial e registre divergências sem publicar credenciais ou payload integral.

Se a resposta exceder budget observado, o estado preserva o custo real observado e encerra como budget; não normaliza o valor para o teto.

## Recording de cassette

`--record-live-cassettes` só deve ser usado com autorização explícita e dados inteiramente fictícios. Cassettes podem conter respostas do provider e não são automaticamente publicáveis. Revise e sanitize fora do fluxo público antes de qualquer commit.

Sem autorização, não use a flag.

## Falhas esperadas

- exit `2`: argumento/contexto inválido antes da run;
- exit `5`: artifact ou input bloqueado por policy;
- exit `6`: budget esgotado;
- exit `7`: provider ou infraestrutura;
- exit `4`: execução funcional não aceita, se você usou `run`.

Leia `classification`, depois `errors` no state e as evidências referenciadas. Não cole response integral ou secret em issue pública.

## Sanitização e cleanup

Depois do experimento:

1. remova a variável de ambiente;
2. examine `.asef/runs`, `.asef/live-cassettes` e logs localmente;
3. não publique artifact/source ou raw output sem autorização;
4. execute cleanup dry-run;
5. aplique somente targets elegíveis e compreendidos.

```powershell
asef cleanup --kind all --older-than-days 7
```

Não execute código gerado diretamente no host e não desabilite controles Docker para contornar falhas. Veja [troubleshooting](../guides/troubleshooting.md) e a [arquitetura do provider live](../architecture/live-provider.md).
