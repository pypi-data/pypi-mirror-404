# `lflatten`

Biblioteca Python **simples, tipada e reversível** para **flatten** e **unflatten** de estruturas aninhadas (`dict` e `list`).

O foco do projeto é:
- simplicidade
- previsibilidade
- round-trip garantido (`unflatten(flatten(x)) == x`)
- suporte a **separador customizável**
- suporte a **escape de separador nas chaves**
- tipagem estática clara

---

## Instalação

Projeto local / em desenvolvimento:

```bash
pip install -e .
````

Ou, se publicado futuramente:

```bash
pip install lflatten
```

---

## Uso básico

> [Documentação](docs/index.md)

### Flatten

```python
from py_simple_flatten import flatten

data = {
    "foo": {
        "bar": 10
    }
}

flatten(data)
```

Resultado:

```python
{
    "foo.bar": 10
}
```

---

### Unflatten

```python
from py_simple_flatten import unflatten

flat = {
    "foo.bar": 10
}

unflatten(flat)
```

Resultado:

```python
{
    "foo": {
        "bar": 10
    }
}
```

---

## Separador customizado (`sep`)

### Exemplo com `sep=":"`

```python
data = {
    "foo:bar": {
        "baz": 10
    }
}

flatten(data, sep=":")
```

Resultado:

```python
{
    "foo\\:bar:baz": 10
}
```

E o round-trip funciona corretamente:

```python
unflatten(
    {"foo\\:bar:baz": 10},
    sep=":"
)
```

Resultado:

```python
{
    "foo:bar": {
        "baz": 10
    }
}
```

---

## Escape de separador

* O separador dentro da chave é **automaticamente escapado**
* `:` → `\:`
* `.` → `\.`
* `\` → `\\`

Isso garante que o `unflatten` reconstrua a estrutura original **sem ambiguidade**.

---

## Listas

Listas são suportadas e reconstruídas corretamente:

```python
data = {
    "a": [1, {"b": 2}]
}

flatten(data)
```

Resultado:

```python
{
    "a.0": 1,
    "a.1.b": 2
}
```

---

## `ignore_none`

Ignora valores `None` durante o flatten:

```python
flatten(
    {"a": None, "b": 1},
    ignore_none=True
)
```

Resultado:

```python
{
    "b": 1
}
```

---

## Tipos

Tipos principais (simplificados):

```python
Flatten = dict[str, Any]
Iter = dict | list
```

A API é compatível com `mypy` / `pyright`.

---

## Garantias do projeto

* ✅ Flatten profundo (`dict` + `list`)
* ✅ Unflatten reversível
* ✅ Separador customizável
* ✅ Escape seguro de chaves
* ✅ Tipagem estática
* ✅ Sem dependências externas

---

## Quando usar

* Serialização de estruturas complexas
* Logs
* Armazenamento chave-valor
* Normalização de dados
* Conversão para DataFrame / CSV

---

## Licença

MIT

---

## Status

Projeto pequeno, estável e intencionalmente minimalista.
Contribuições são bem-vindas se mantiverem o foco em simplicidade e previsibilidade.

