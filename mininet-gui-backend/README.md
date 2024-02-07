# mininet-gui-backend

Backend for the Mininet-GUI app.

## API docs

<http://127.0.0.1:8000/docs>

## Running backend

```
sudo uvicorn mininet_gui_backend.api:app --host=0.0.0.0 --port=8080 --log-level debug
```

## Starting network

```
curl -X POST http://mininet-gui-backend:8080/api/mininet/start
```


