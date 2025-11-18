from django.db import models



class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True

#É um "molde": Serve para não precisar digitar os campos de data em todo arquivo models.py.

#Automação:

#created_at: Salva a data/hora exata da criação (nunca muda).

#updated_at: Atualiza a data/hora automaticamente sempre que o registro é editado.

#abstract = True: Diz ao Django: "Não crie uma tabela no banco para isso. Apenas empreste esses campos para quem herdar desta classe (como Livros ou Usuários).""""