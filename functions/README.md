Pub/Sub の Cloud Functions ハンドラー

## スキーマ

```
topic: email
{
    "to_emails": [...],
    "subject": "...",
    "message": "...",
}
```

```
topic: push
{
    "tokens": [...],
    "room": "...",
    "user": "....",
    "message": "...",
}
```

## 注意

Firebase と Sendgrid の環境が用意できなかったので未検証。