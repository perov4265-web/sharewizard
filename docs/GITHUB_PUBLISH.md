# Инструкция по публикации ShareWizard на GitHub

## Шаг 1 — Создать репозиторий на GitHub

1. Зайдите на https://github.com/new
2. Заполните поля:
   - **Repository name:** `sharewizard`
   - **Description:** `Мастер публикации сетевых папок для Windows 10/11`
   - Видимость: **Public** (или Private)
   - ❌ НЕ ставьте галочку «Add a README file» — он уже есть
3. Нажмите **Create repository**

## Шаг 2 — Инициализировать локальный репозиторий

Откройте терминал (PowerShell или Git Bash) в папке проекта:

```bash
cd путь\к\папке\sharewizard

git init
git add .
git commit -m "Initial commit: ShareWizard v1.0.0"
```

## Шаг 3 — Связать с GitHub и загрузить

```bash
git remote add origin https://github.com/ВАШ_ЛОГИН/sharewizard.git
git branch -M main
git push -u origin main
```

## Шаг 4 — Создать тег версии (Release)

```bash
git tag -a v1.0.0 -m "ShareWizard v1.0.0 — первый публичный релиз"
git push origin v1.0.0
```

Затем на GitHub:
- Перейдите в **Releases** → **Draft a new release**
- Выберите тег `v1.0.0`
- Заголовок: `ShareWizard v1.0.0`
- Приложите архив `ShareWizard_v1.0.0.zip` (содержимое папки проекта)
- Нажмите **Publish release**

## Шаг 5 — Настроить репозиторий (опционально)

В настройках репозитория (Settings):
- **Topics:** добавьте `windows`, `smb`, `network-share`, `tkinter`, `python`, `sysadmin`
- **Website:** можно оставить пустым
- Включите **Issues** и **Discussions**

## Проверка

После загрузки убедитесь, что на главной странице репозитория:
- ✅ Отображается README.md с описанием
- ✅ Есть файл LICENSE
- ✅ Папка `.github` содержит шаблоны Issue
- ✅ Папка `docs` содержит CONFIGURATION.md
