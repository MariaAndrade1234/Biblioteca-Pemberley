# REVISÃO DE MARIA BEATRIZ

## Descrição:
Essas correções tem o intuito de instruir o desenvolvedor que está começando a melhorar suas skills, aprender com `devs` mais experientes, além de direcionar para a cultura organizacional do time de tecnologia seguindo boas práticas de programação.

## Correções:

**Duplicação no Modelo**

Na model está duplicado o campo de status

```py
	STATUS_AVAILABLE = 'available'
	STATUS_BORROWED = 'borrowed'
	STATUS_RESERVED = 'reserved'

	STATUS_CHOICES = [
		(STATUS_AVAILABLE, 'Available'),
		(STATUS_BORROWED, 'Borrowed'),
		(STATUS_RESERVED, 'Reserved'),
	]
```
Poderia ser assim 

```py
STATUS_CHOICES = [
		(STATUS_AVAILABLE, 'Available'),
		(STATUS_BORROWED, 'Borrowed'),
		(STATUS_RESERVED, 'Reserved'),
	]

status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
```

**Na model `Borrowing` tem campo `returned` que não foi solicitado no projeto**

Devemos seguir estritamente o que é pedido, se tem algo que queremos colocar a mais, devemos solicitar um ADR 

```py
	return_date = models.DateTimeField()
	returned = models.BooleanField(default=False)
```

**Uma model não solicitada**

Segue o mesmo argumento do tópico anterior.

```py
class Reservation(TimestampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
	active = models.BooleanField(default=True)
```
**Não implementou contratos no Serializer e nem usou NestedSerializer em momento algum**

Foi pedido no projeto para usar NestedSerialized, o que não foi feito no projeto, é importante um desenvolvedor django entender e se fundamentar no que é um serializer.

**O teste foi implementado, mas não houve instrução de execução dos testes e por essa razão não tive como avaliar os testes se passaram, foi solicitado testes apenas na lógica de empréstimo do livro.**

Instruções de testes são essenciais na aplicação.

**A estrutura de código ficou muito acoplada em "Library".**

Uma estrutura desacoplada, permite uma melhor manutenção no código. 

**O README provavelmente foi escrito com IA, nas instruções do teste é claro o "Or run pytest (if installed):" e não houve instalação de rota para o sawagger.**

Evitar o máximo o uso de IA enquanto está aprendendo, o desenvolvedor aprende errando, e usar IA para desenvolver algo como se fosse um projeto low code ou vibe coding, faz com que o desenvolvedor não enfrente desafios em amadurecer e ter conhecimentos necessários para ser um desenvolvedor. 

**Rotas que não foram elaboradas e muito menos houve uso de padrões REST**

É importante para um desenvolvedor web entender os padrões Rest e implementar rotas especificas para cada endpoint, tornando a manutenção do código mais facil. 

- **Impressão geral (técnica):**  
  Para nível **Júnior 1**, o projeto está **acima da média** em:
  - estrutura de apps (`users`, `library`, `core`) bem separada;
  - uso correto de DRF (`ModelViewSet`, filtros, paginação, `DefaultRouter`);
  - camada de serviços em `library/services.py` com regras de negócio de empréstimo/reserva;
  - boa cobertura de testes de fluxo (empréstimos) e de autenticação JWT.

- **Sobre uso de IA (probabilidade):**
  - Há alguns **sinais fortes de apoio por IA**, principalmente:
    - README em inglês, longo, bem organizado, com frases típicas de resposta de chat (“If you want, I can also add…”);
    - desenho da camada de serviço (`BorrowingService` com exceções de domínio, `transaction.atomic`, `select_for_update`) e injeção de dependência em views (`borrowing_service`, `user_service`) é um padrão mais avançado do que o esperado para Júnior 1;
    - uso de imports dinâmicos/`getattr(__import__(...))` em locais onde um import simples resolveria, o que é um padrão muito típico de respostas de IA tentando “generalizar” demais.
  - Ao mesmo tempo:
    - há sinais de iteração manual (tabs misturados com spaces, pequenos deslizes de texto em português, docstrings adaptadas).
  - **Conclusão sobre IA:**  
    - Eu não consigo afirmar autoria, mas **a probabilidade de uso intenso de IA como apoio é alta**, especialmente em README, camada de serviço e alguns testes.  
    - O projeto parece o resultado de alguém guiando/ajustando respostas de IA, não apenas copiando sem testar (os testes são coerentes com o código).

- **Conclusão resumida sobre senioridade:**  
  - Como código funcional de backend, **é aprovável/forte para Júnior 1** em termos de entrega técnica.  
  - Como avaliação de “skill individual” sem IA, eu ficaria com **ressalva importante**: o nível de arquitetura e de texto está mais para **Pleno orientado por IA** do que para Júnior escrevendo 100% sozinho.



