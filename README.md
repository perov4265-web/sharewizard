# 📂 ShareWizard

> **Мастер публикации сетевых папок для Windows 10 / 11**  
> Настраивает SMB-ресурс, права NTFS, брандмауэр и сетевое обнаружение — в несколько кликов.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078d7?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-tkinter-orange)
![Admin](https://img.shields.io/badge/Requires-Administrator-red)

---

## ✨ Возможности

| Категория | Что настраивается |
|-----------|-------------------|
| **Папка** | Создание (если не существует), путь, имя SMB-ресурса, описание |
| **Права** | NTFS и SMB-права раздельно, произвольное число пользователей/групп |
| **SMB** | Access Based Enumeration, шифрование, лимит подключений, кеширование |
| **Брандмауэр** | Порт 445, NetBIOS 137-139, сетевое обнаружение, профили сети |
| **Сеть** | Сетевое обнаружение, общий доступ к файлам, защита паролем |
| **Службы** | LanmanServer, WinRM, зависимые службы обнаружения |
| **Безопасность** | Аудит доступа к папке (Success + Failure) |
| **Диагностика** | Живой мониторинг состояния всех компонентов |
| **Журнал** | Цветной лог выполнения, сохранение в файл |

---



## 🚀 Быстрый старт

### Требования

- Windows 10 или Windows 11
- [Python 3.8+](https://python.org/downloads/) — при установке включите **"Add Python to PATH"**
- Права **администратора**

### Установка и запуск

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/sharewizard.git
cd sharewizard
```

Затем двойной клик на **`Запустить_ShareWizard.bat`** — батник сам запросит права администратора (UAC).

Или вручную из PowerShell (от администратора):

```powershell
python ShareWizard.py
```

### Зависимости

ShareWizard не требует установки сторонних библиотек — используется только стандартная библиотека Python (`tkinter`, `subprocess`, `threading`, `ctypes`).

---

## 📋 Пошаговая инструкция

1. Запустите `Запустить_ShareWizard.bat` (согласитесь с UAC)
2. Нажмите **Обзор...** и выберите папку, или введите путь вручную
3. Укажите **имя SMB-ресурса** (латиницей, без пробелов)
4. Настройте **права доступа** — добавьте нужных пользователей/группы
5. Проверьте **диагностику** в правой панели
6. Нажмите **▶ ПРИМЕНИТЬ НАСТРОЙКИ**
7. После завершения подключитесь с другого ПК: `\\ИМЯ_КОМПЬЮТЕРА\ИМЯ_РЕСУРСА`

---

## 🔧 Что делает программа под капотом

```
Запуск
  │
  ├─ 1. Создание папки (если не существует)
  ├─ 2. Запуск службы LanmanServer (автозапуск)
  ├─ 3. Настройка NTFS-прав (FileSystemAccessRule)
  ├─ 4. Удаление старого SMB-ресурса (если был)
  ├─ 5. New-SmbShare (ABE, шифрование, лимит, кеш)
  ├─ 6. Grant-SmbShareAccess для каждого пользователя
  ├─ 7. Брандмауэр: порт 445, NetBIOS, Discovery
  ├─ 8. Сетевые службы: fdPHost, FDResPub, SSDPSRV
  ├─ 9. Реестр: сетевое обнаружение, SMB v2
  └─ 10. Опциональный аудит (auditpol + FileSystemAuditRule)
```

---

## 📁 Структура проекта

```
sharewizard/
├── ShareWizard.py              # Основная программа (GUI + логика)
├── Запустить_ShareWizard.bat   # Запуск с UAC-повышением прав
├── README.md                   # Этот файл
├── LICENSE                     # Лицензия MIT
├── .gitignore                  # Исключения Git
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md       # Шаблон баг-репорта
│   │   └── feature_request.md  # Шаблон запроса функции
│   └── PULL_REQUEST_TEMPLATE.md
└── docs/
    └── CONFIGURATION.md        # Подробная документация по параметрам
```

---

## ⚙️ Параметры конфигурации

Подробное описание всех настроек см. в [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| ABE | Вкл | Скрывает папки, к которым нет доступа |
| SMB-шифрование | Выкл | Требует Windows 8+ на клиенте |
| Макс. подключений | 0 (∞) | Лимит одновременных сессий |
| Кеширование | None | Режим офлайн-кеша |
| Профиль FW | Domain + Private | Профиль брандмауэра |
| Аудит | Выкл | Журнал Success + Failure в Event Log |

---

## 🐛 Известные ограничения

- Требует Windows 10/11 (вызовы `netsh`, `powershell`, `sc` специфичны для Windows)
- SMB-шифрование работает только если клиент поддерживает SMB 3.0+
- Служба `Browser` (обозреватель сети) недоступна в Windows 10 1709+
- Для настройки аудита необходима политика `Object Access` в `auditpol`

---

## 🤝 Contributing

1. Fork репозитория
2. Создайте ветку: `git checkout -b feature/my-feature`
3. Зафиксируйте изменения: `git commit -m 'Add: my feature'`
4. Push: `git push origin feature/my-feature`
5. Откройте Pull Request

---

## 📄 Лицензия

Распространяется под лицензией **MIT**. Подробнее см. [LICENSE](LICENSE).

---

<div align="center">
  Сделано для системных администраторов Windows
</div>
