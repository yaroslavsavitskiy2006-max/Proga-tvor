# -*- coding: utf-8 -*-
"""
ЛАБОРАТОРНАЯ РАБОТА · БЛОКЧЕЙН · ООП

Клиент студента: создаёт блок с фамилией и группой, майнит его
(Proof-of-Work) и присоединяет к общей цепочке преподавателя.

Запуск:
    pip install requests
    python student_client_task.py --surname Иванов --group КИС-01-22 --server http://127.0.0.1:5000

Если аргументы не указаны, берутся значения по умолчанию / переменные окружения
STUDENT_SURNAME, STUDENT_GROUP, BLOCKCHAIN_SERVER.
"""
import argparse
import hashlib
import os
import time

import requests


class Block:
    """Один блок цепочки. Хранит данные и умеет считать свой хэш и майнить."""

    NUM_ZEROS = 4   # сложность Proof-of-Work (должно совпадать с сервером)

    def __init__(self, index, surname, group, prev_hash,
                 message="Привет, блокчейн!", timestamp=None, nonce=0):
        # поля блока уже заданы — трогать не нужно
        self.index = index
        self.surname = surname
        self.group = group
        self.message = message
        self.prev_hash = prev_hash
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = nonce
        self.hash = None

    @property
    def data(self):
        """Данные блока одной строкой (фамилия, группа, сообщение). НЕ менять формат!"""
        return f"{self.surname}, группа {self.group} — {self.message}"

    def header(self):
        """Заголовок для хэширования. Формат ДОЛЖЕН совпадать с сервером — не менять."""
        return f"{self.index}|{self.prev_hash}|{self.data}|{self.timestamp}|{self.nonce}"

    def calc_hash(self):
        """SHA-256 (hexdigest) от self.header(), закодированного в utf-8."""
        return hashlib.sha256(self.header().encode("utf-8")).hexdigest()

    def mine(self):
        """Proof-of-Work: подбираем nonce, пока хэш не начнётся с NUM_ZEROS нулей."""
        target = "0" * Block.NUM_ZEROS
        while True:
            current = self.calc_hash()
            if current.startswith(target):
                self.hash = current
                return self.nonce, self.hash
            self.nonce += 1

    def to_dict(self):
        """Словарь блока со всеми полями, которые ждёт сервер."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "surname": self.surname,
            "group": self.group,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "hash": self.hash if self.hash is not None else self.calc_hash(),
        }

    def __repr__(self):
        return (f"Block(index={self.index}, surname={self.surname!r}, "
                f"group={self.group!r}, hash={str(self.hash)[:12]}…)")


class StudentClient:
    """Клиент студента: общается с сервером преподавателя и присоединяет блок."""

    def __init__(self, server_url, surname, group):
        url = server_url.strip().rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        self.server = url
        self.surname = surname
        self.group = group

    def get_last_block(self):
        """GET /last_block — последний блок цепочки (готовый метод)."""
        r = requests.get(f"{self.server}/last_block", timeout=10)
        r.raise_for_status()
        return r.json()

    def create_block(self, last, message):
        """Создать Block, идущий за блоком last.

        Позиционные аргументы: index, surname, group, prev_hash.
        Именованный аргумент: message.
        """
        return Block(
            last["index"] + 1,          # позиционный
            self.surname,               # позиционный
            self.group,                 # позиционный
            last["hash"],               # позиционный
            message=message,            # именованный
        )

    def submit(self, block):
        """POST /add_block. Возвращает (status_code, ответ-JSON)."""
        r = requests.post(
            f"{self.server}/add_block",
            json=block.to_dict(),
            timeout=10,
        )
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"accepted": False, "reason": r.text}

    def show_chain(self):
        """Показать текущую цепочку преподавателя (готовый метод)."""
        chain = requests.get(f"{self.server}/chain", timeout=10).json()["chain"]
        print("\nТекущая цепочка преподавателя:")
        for b in chain:
            who = "ГЕНЕЗИС" if b["index"] == 0 else f"{b['surname']} (гр. {b['group']})"
            print(f"  #{b['index']:>2}  {who:<30} hash={b['hash'][:12]}…  prev={b['prev_hash'][:12]}…")

    def run(self, message="Привет, блокчейн!"):
        """Главный сценарий. Вызывает create_block / mine / submit."""
        print(f"Подключаюсь к {self.server}  как  {self.surname} (гр. {self.group})")
        for attempt in range(1, 6):
            last = self.get_last_block()
            block = self.create_block(last, message)
            print(f"[Попытка {attempt}] Майнинг блока #{block.index} … "
                  f"(ищем хэш с {Block.NUM_ZEROS} нулями)")
            nonce, h = block.mine()
            print(f"  Найден nonce={nonce}, hash={h[:20]}…  отправляем преподавателю…")
            status, res = self.submit(block)
            if res.get("accepted"):
                print(f"\n✔ БЛОК ПРИНЯТ! Ваш блок #{res['index']} добавлен в цепочку. "
                      f"Длина цепочки: {res['chain_length']}.")
                break
            print(f"✖ Блок отклонён: {res.get('reason')}")
            if status == 409 and "last_block" in res:
                print("  Цепочка изменилась — перемайниваем…")
                continue
            break
        self.show_chain()


def main():
    parser = argparse.ArgumentParser(
        description="Клиент блокчейн-сети: майнит блок и добавляет его в общую цепочку."
    )
    parser.add_argument(
        "--server",
        default=os.environ.get("BLOCKCHAIN_SERVER", "http://10.39.120.52:5000"),
        help="адрес сервера преподавателя (по умолчанию http://10.39.120.52:5000)",
    )
    parser.add_argument(
        "--surname",
        default=os.environ.get("STUDENT_SURNAME", "Савицкий"),
        help="фамилия студента",
    )
    parser.add_argument(
        "--group",
        default=os.environ.get("STUDENT_GROUP", "ОКБП-401итмп"),
        help="группа студента",
    )
    parser.add_argument(
        "--message",
        default="Мой блок на ООП",
        help="сообщение внутри блока",
    )
    args = parser.parse_args()

    # ИМЕНОВАННЫЕ (keyword) аргументы — при создании клиента:
    client = StudentClient(
        server_url=args.server,
        surname=args.surname,
        group=args.group,
    )
    # НЕИМЕНОВАННЫЙ (позиционный) аргумент — при вызове метода:
    try:
        client.run(args.message)
    except requests.exceptions.ConnectionError:
        print(f"✖ Не удалось подключиться к серверу {client.server}.")
        print("  Убедитесь, что преподаватель запустил teacher_server.py,")
        print("  и проверьте адрес в аргументе --server.")
        raise SystemExit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"✖ Сервер вернул ошибку: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
