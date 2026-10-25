# NexusPulse — мод Telegram 🚀

Форк Telegram-FOSS с ребрендингом в **NexusPulse**, твоим лого и фишкой
**«Режим невидимки»** — когда она включена, клиент никогда не отправляет статус
«в сети», и собеседники видят «был(а) недавно» вместо «online».

APK собирается **бесплатно на серверах GitHub** — тебе нужен только аккаунт GitHub.
Ничего устанавливать на компьютер не нужно.

---

## Что делает мод

| Фишка | Описание |
|---|---|
| Название | Приложение везде называется **NexusPulse** (все языки) |
| Иконка | Твоё лого (неоновая «N» с орбитой) во всех размерах + адаптивная иконка |
| Package | `com.nexuspulse.messenger` (ставится рядом с оригинальным Telegram) |
| Режим невидимки | Тумблер в **Настройки → Конфиденциальность**, включён по умолчанию |

> ⚠️ Честное ограничение: сервер Telegram всё равно технически видит активность
> (это верно для ЛЮБОГО клиентского мода), но другие пользователи твой статус
> «online» видеть не будут.

## Сборка за 5 шагов

1. **Создай репозиторий** на GitHub (например `nexuspulse`) — Public или Private.
2. **Загрузись все файлы этого кита** в корень репозитория:
   ```
   nexuspulse/
   ├── scripts/apply_mod.py
   ├── assets/logo.png
   └── .github/workflows/build.yml
   ```
   (через веб-интерфейс GitHub: «Add file → Upload files», папку `.github` тоже можно загрузить через веб).
3. Открой вкладку **Actions** в репозитории → выбери **«Build NexusPulse APK»** → кнопка **Run workflow**.
4. Жди ~30–60 минут (сборка тяжёлая). Статус виден прямо в Actions.
5. Когда сборка позеленеет — открой её, пролистай вниз в **Artifacts** и скачай **NexusPulse-APK**.

Перед установкой включи в Android «Установка из неизвестных источников».

## Если сборка упала

- Открой упавший job в Actions и посмотри последний красный шаг.
- Чаще всего: обновились исходники Telegram-FOSS и «уехали» строки, которые патчит
  скрипт. В логе будет видно, какой паттерн не нашёлся (`[WARN] pattern not found`).
- Можно закрепить стабильную версию: в `build.yml` замени
  `git clone --depth=1 ...` на `git clone --depth=1 -b <номер_релиза> ...`
  (номера релизов: https://github.com/Telegram-FOSS-Team/Telegram-FOSS/releases).

## Локальная сборка (для продвинутых)

```bash
git clone --depth=1 https://github.com/Telegram-FOSS-Team/Telegram-FOSS.git
cd Telegram-FOSS
python3 ../nexuspulse-mod-kit/scripts/apply_mod.py
./gradlew assembleAfatDebug
```

## Структура мода (что именно правит скрипт)

- `res/values*/strings.xml` — AppName → NexusPulse, новые строки
- `TMessagesProj/build.gradle` — applicationId → com.nexuspulse.messenger
- `res/mipmap-*` — иконки из `assets/logo.png`
- `GhostConfig.java` (новый файл) — хранение настройки невидимки
- `MessagesController.updateTimerProc()` — блокировка отправки статуса «online»
- `PrivacySettingsActivity` — тумблер «Режим невидимки» в настройках конфиденциальности
- `ApplicationLoader` — загрузка настройки при старте
