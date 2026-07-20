# Retrospectiva técnica — Etapa 6

A Etapa 6 transformou a fundação Python em três jornadas cotidianas delimitadas:
API, Web UI e Java unitário. O ganho de velocidade veio do envelope comum de run,
policies, budgets, Docker e evidências, enquanto contratos e tooling permaneceram
específicos nos adapters.

Os principais achados foram produzidos pelas provas, não por especulação: corrida de
popup no browser, assets ausentes no wheel, Surefire ainda não publicado, ordem de
métodos no XML e fixture Java inicialmente dependente do checkout. Cada correção
virou teste permanente.

A consolidação também impediu dois overclaims. Coverage/mutation só estão disponíveis
no recorte Python; Node e Java declaram ausência. TypeScript tinha Web UI real, mas
não unit equivalente; o Gate forçou uma prova Node test/TAP sobre a mesma intenção
aritmética revisada do Java.

O resultado técnico está pronto para decisão humana, não para promoção automática.
Uso externo, Kotlin, `.bat`, projetos reais e avaliação independente continuam
lacunas abertas sem prazo, conforme decisão do autor.
