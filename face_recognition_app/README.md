# Aplicativo de Reconhecimento Facial em Flutter

Este aplicativo Flutter implementa um cliente para o sistema de reconhecimento facial em tempo real.

## Requisitos

- Flutter SDK (versão 3.0.0 ou superior)
- Dart SDK (versão 3.0.0 ou superior)
- Servidor de reconhecimento facial rodando (verifique o repositório principal)

## Configuração

1. Instale o Flutter seguindo as instruções oficiais: https://flutter.dev/docs/get-started/install

2. Clone este repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd face_recognition_app
```

3. Instale as dependências:
```bash
flutter pub get
```

4. Certifique-se de que o servidor de reconhecimento facial está rodando em `localhost:8000`

## Executando o Aplicativo

1. Conecte um dispositivo ou inicie um emulador

2. Execute o aplicativo:
```bash
flutter run
```

## Funcionalidades

- Visualização em tempo real da câmera
- Reconhecimento facial em tempo real
- Feedback visual do status de conexão
- Exibição de resultados de reconhecimento
- Interface moderna e responsiva

## Estrutura do Projeto

- `lib/main.dart`: Arquivo principal do aplicativo
- `pubspec.yaml`: Configurações e dependências do projeto

## Dependências Principais

- `camera`: Para acesso à câmera do dispositivo
- `web_socket_channel`: Para comunicação em tempo real com o servidor
- `image`: Para processamento de imagens
- `path_provider`: Para gerenciamento de arquivos temporários

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request 