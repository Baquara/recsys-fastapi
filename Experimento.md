# Guia da API do Recsys

Este guia fornece instruções sobre como interagir com a API do Recsys.


## Acessando a API

A API pode ser acessada no endpoint [https://recsysapi-cz0t.onrender.com/](https://recsysapi-cz0t.onrender.com/). Os usuários podem interagir com a API, realizando ações como adicionar, remover e buscar itens. A API também pode ser usada para gerar recomendações.

## Limpar o Banco de Dados

Use a seguinte solicitação `DELETE` para limpar o banco de dados.

```sh
curl -X DELETE https://recsysapi-cz0t.onrender.com/clear_db
```

## Adicionar Itens

Itens podem ser adicionados ao banco de dados com uma solicitação `POST`, conforme mostrado abaixo:

```sh
curl -X POST https://recsysapi-cz0t.onrender.com/item -d @items.json -H "Content-Type: application/json"
```

O arquivo `items.json` deve ter a seguinte estrutura:

```json
{
    "items": [
        {
            "itemId": "1",
            "title": "Estátua da Liberdade",
            "description": "Uma colossal escultura neoclássica na Ilha da Liberdade no Porto de Nova York",
            "tag": ["EUA", "Nova York", "Monumento"]
        },
        ...
    ]
}
```

Consulte o arquivo **items.json** incluído no projeto: https://github.com/Baquara/recsys-fastapi/blob/main/items.json


## Obter Itens

Para obter itens do banco de dados, use a seguinte solicitação `GET`:

```sh
curl -X GET https://recsysapi-cz0t.onrender.com/items
```

## Adicionar Usuários

Usuários podem ser adicionados ao banco de dados com uma solicitação `POST`:

```sh
curl -X POST https://recsysapi-cz0t.onrender.com/user -d @users.json -H "Content-Type: application/json"
```

O arquivo `users.json` deve ter a seguinte estrutura:

```json
{
    "items": [
        {
            "userId": 1,
            "itemId": 1,
            "rating": 3.5,
            "timestamp": 1112486027
        },
        ...
    ]
}
```

Consulte o arquivo **users.json** incluído no projeto: https://github.com/Baquara/recsys-fastapi/blob/main/users.json

## Obter Usuários

Para obter usuários do banco de dados, use a seguinte solicitação `GET`:

```sh
curl -X GET https://recsysapi-cz0t.onrender.com/users
```

## Fazer Recomendações

Você pode fazer recomendações usando o Filtro Colaborativo ou o Filtro Baseado em Conteúdo.

### Filtragem Colaborativa

Para obter recomendações usando o Filtragem Colaborativa para um usuário específico, envie uma solicitação `GET` para `/user/recommendations` com os parâmetros opcionais `nrec` para o número de recomendações e `sel_item` para um item específico.

```sh
curl -X GET "https://recsysapi-cz0t.onrender.com/user/recommendations?nrec=5&sel_item=Item1"
```

### Filtragem Baseada em Conteúdo

Para obter recomendações usando o Filtragem Baseada em Conteúdo para um item específico, envie uma solicitação `GET` para `/item/neighbors` com os parâmetros opcionais `itemno` para o número do item e `nitems` para o número de itens.

```sh
curl -X GET "https://recsysapi-cz0t.onrender.com/item/neighbors?itemno=1&nitems=5"
```

Substitua `nrec`, `sel_item`, `itemno` e `nitems` conforme necessário.

## Perguntas de Experimento

Como parte do meu projeto de mestrado, agradeço muito seu feedback sobre a API do Sistema de Recomendação. Sua contribuição me ajudará a avaliar a eficácia do sistema e identificar áreas para melhorias. Por favor

, reserve um momento para responder às seguintes perguntas:

1. Como você avaliaria o desempenho geral e a responsividade da API?
2. Você conseguiu configurar e executar com sucesso a API usando as instruções fornecidas?
3. Você encontrou alguma dificuldade ou problema ao interagir com a API ou executar os scripts?
4. Você achou a documentação da API e os exemplos fornecidos claros e úteis?
5. Você conseguiu entender e utilizar os sistemas de recomendação por Filtro Colaborativo e Filtro Baseado em Conteúdo de forma eficaz?
6. As recomendações geradas pelo sistema estavam de acordo com suas expectativas? Elas foram úteis e relevantes?
7. Houve alguma funcionalidade específica que você sentiu que estava faltando na API?
8. Você tem alguma sugestão para melhorar a API ou os sistemas de recomendação?
9. Como a API do Sistema de Recomendação se compara a outras APIs de sistemas de recomendação que você pode ter usado no passado? Forneça suas percepções e comparações em relação aos recursos, usabilidade, desempenho e quaisquer outros aspectos relevantes ao comparar a API do Sistema de Recomendação com outras APIs similares com as quais você trabalhou.

Seu feedback é inestimável para mim, e agradeço por dedicar seu tempo para me ajudar com meu projeto. Se você tiver algum comentário ou percepção adicional, sinta-se à vontade para compartilhá-los. Obrigado!
