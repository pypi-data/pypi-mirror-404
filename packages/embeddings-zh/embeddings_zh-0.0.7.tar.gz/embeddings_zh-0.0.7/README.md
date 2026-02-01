# embeddings-zh

Embeddings with Chatopera Synonyms for chatbot, RAG.

[GitHub](https://github.com/chatopera/embeddings-zh) | [Gitee](https://gitee.com/chatopera/embeddings-zh)

Model: [GitHub](https://github.com/chatopera/Synonyms) | [Gitee](https://gitee.com/chatopera/Synonyms)

```
pip install -U embeddings-zh
```

Usage::


## 中文简体 / Simplified Chinese

```

from embeddings_zh import EmbeddingsZh

emb = EmbeddingsZh()
vectors = emb.embed_documents([texts]) # e.g. emb.embed_documents(["今天天气怎么样", "有什么推荐"])
vector = emb.embed_query(texts) # e.g. emb.embed_documents("有什么推荐")

```

## 中文繁體 / Traditional Chinese

The API is the same as Simplified Chinese.

```
from embeddings_zh import EmbeddingsZhTw

emb = EmbeddingsZhTw(w2v_model_path=os.path.join(curdir, "data", "models", "tmunlp_1.6B_WB_100dim_2020v1.bin.gz"))
print("Embed doc")
print(emb.embed_documents(["依照世界骨髓庫制定的原則", "進行造血幹細胞移植後"]))

print("Embed query")
print(emb.embed_query("進行造血幹細胞移植後"))
```


# Tutorials

* Build a chabot with langchain: [demo](./demo/)

# License
[LICENSE](./LICENSE)